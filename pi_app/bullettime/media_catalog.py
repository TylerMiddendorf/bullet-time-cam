"""Catalog and guarded deletion of published capture sets on removable USB media."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image

EAGER_THUMBNAIL_COUNT = 6


@dataclass(frozen=True)
class CatalogEntry:
    capture_id: str
    directory: Path
    animation: Path
    status: str
    view_count: int
    failed_camera_ids: tuple[int, ...]
    thumbnail_bytes: bytes
    thumbnail_mime: str


@dataclass(frozen=True)
class CatalogSnapshot:
    status: str
    entries: tuple[CatalogEntry, ...]
    skipped_count: int = 0
    message: str = ""


def _published_entry(directory: Path, *, decode_thumbnail: bool) -> CatalogEntry | None:
    try:
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or int(manifest.get("schema_version", 0)) != 2:
            return None
        capture_id = str(manifest.get("capture_id", "")).strip()
        if not capture_id or capture_id != directory.name:
            return None
        cameras = manifest.get("cameras")
        files = manifest.get("files")
        if not isinstance(cameras, list) or not isinstance(files, list):
            return None
        animation_file = next(
            (item for item in files if isinstance(item, dict) and item.get("role") == "animation"),
            None,
        )
        if animation_file is None:
            return None
        relative = Path(str(animation_file.get("path", "")))
        if relative.is_absolute() or ".." in relative.parts or relative == Path("."):
            return None
        animation = directory / relative
        if not animation.is_file():
            return None
        with animation.open("rb") as stream:
            signature = stream.read(6)
        if signature not in {b"GIF87a", b"GIF89a"}:
            return None
        thumbnail_bytes = b""
        thumbnail_mime = ""
        preview_file = next(
            (
                item
                for item in files
                if isinstance(item, dict) and item.get("role") == "library_preview"
            ),
            None,
        )
        if preview_file is not None:
            preview_relative = Path(str(preview_file.get("path", "")))
            if (
                not preview_relative.is_absolute()
                and ".." not in preview_relative.parts
                and preview_relative != Path(".")
            ):
                preview = directory / preview_relative
                try:
                    thumbnail_bytes = preview.read_bytes()
                    if thumbnail_bytes.startswith(b"\xff\xd8\xff"):
                        thumbnail_mime = "image/jpeg"
                    else:
                        thumbnail_bytes = b""
                except OSError:
                    thumbnail_bytes = b""
        if not thumbnail_bytes and decode_thumbnail:
            # Only decode the initially visible row in this worker. Reading all
            # legacy GIFs made a 200-set catalog take tens of seconds.
            with Image.open(animation) as source:
                source.seek(0)
                thumbnail = source.convert("RGB")
                thumbnail.thumbnail((240, 135))
                thumbnail_output = BytesIO()
                thumbnail.save(thumbnail_output, format="JPEG", quality=72)
                thumbnail_bytes = thumbnail_output.getvalue()
                thumbnail_mime = "image/jpeg"
        completed = sorted(
            int(camera["logical_camera_id"])
            for camera in cameras
            if isinstance(camera, dict)
            and camera.get("status") == "complete"
            and 1 <= int(camera.get("logical_camera_id", 0)) <= 4
        )
        failed = sorted(
            int(camera["logical_camera_id"])
            for camera in cameras
            if isinstance(camera, dict)
            and camera.get("status") != "complete"
            and 1 <= int(camera.get("logical_camera_id", 0)) <= 4
        )
        if len(completed) < 2:
            return None
        status = str(manifest.get("status", ""))
        if status not in {"complete", "partial"}:
            return None
        return CatalogEntry(
            capture_id=capture_id,
            directory=directory,
            animation=animation,
            status=status,
            view_count=len(completed),
            failed_camera_ids=tuple(failed),
            thumbnail_bytes=thumbnail_bytes,
            thumbnail_mime=thumbnail_mime,
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, OSError):
        return None


def scan_capture_catalog(root: Path | None) -> CatalogSnapshot:
    """Scan published sets only; malformed, staging, and unreadable entries are skipped."""

    if root is None:
        return CatalogSnapshot("unavailable", (), message="USB media is not available")
    try:
        directories = [
            entry
            for entry in root.iterdir()
            if entry.is_dir() and not entry.name.startswith(".") and not entry.is_symlink()
        ]
    except OSError:
        return CatalogSnapshot("removed", (), message="USB media was removed or is unreadable")

    directories.sort(key=lambda directory: directory.name, reverse=True)
    entries: list[CatalogEntry] = []
    skipped = 0
    for directory in directories:
        entry = _published_entry(
            directory,
            decode_thumbnail=len(entries) < EAGER_THUMBNAIL_COUNT,
        )
        if entry is None:
            skipped += 1
        else:
            entries.append(entry)
    if not root.is_dir():
        return CatalogSnapshot("removed", (), message="USB media was removed during refresh")
    return CatalogSnapshot("ready", tuple(entries), skipped_count=skipped)


def load_catalog_animation(
    entry: CatalogEntry, display_size: tuple[int, int]
) -> tuple[list[Image.Image], list[int]]:
    """Decode and detach a selected published animation from removable storage."""

    from .ui import _load_review_frames

    return _load_review_frames(entry.animation, display_size)


def delete_catalog_entry(root: Path | None, entry: CatalogEntry) -> None:
    """Delete one still-valid published capture set below the active USB root.

    The catalog entry is revalidated immediately before removal. This prevents
    callers from using this operation as a general recursive-delete primitive
    or deleting a path that has since been replaced with a symlink.
    """

    if root is None:
        raise OSError("USB media is not available")
    try:
        resolved_root = root.resolve(strict=True)
        if entry.directory.is_symlink() or not entry.directory.is_dir():
            raise ValueError("selected capture set is no longer a regular directory")
        if entry.directory.parent.resolve(strict=True) != resolved_root:
            raise ValueError("selected capture set is outside the active USB library")
    except OSError as exc:
        raise OSError("USB media was removed or is unreadable") from exc

    verified = _published_entry(entry.directory, decode_thumbnail=False)
    if verified is None or verified.capture_id != entry.capture_id:
        raise ValueError("selected capture set is no longer a valid published capture")
    if verified.animation.resolve(strict=True) != entry.animation.resolve(strict=True):
        raise ValueError("selected capture animation changed after catalog refresh")

    shutil.rmtree(entry.directory)
