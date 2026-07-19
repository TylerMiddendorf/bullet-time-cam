"""Read-only catalog of published capture sets on removable USB media."""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class CatalogEntry:
    capture_id: str
    directory: Path
    animation: Path
    status: str
    view_count: int
    failed_camera_ids: tuple[int, ...]
    thumbnail_png: bytes


@dataclass(frozen=True)
class CatalogSnapshot:
    status: str
    entries: tuple[CatalogEntry, ...]
    skipped_count: int = 0
    message: str = ""


def _published_entry(directory: Path) -> CatalogEntry | None:
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
        # Decode the first frame in the worker so corrupt catalog entries never
        # reach QML and never block the GUI thread during validation.
        with Image.open(animation) as source:
            source.seek(0)
            thumbnail = source.convert("RGB")
            thumbnail.thumbnail((240, 135))
            thumbnail_output = io.BytesIO()
            thumbnail.save(thumbnail_output, format="PNG")
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
            thumbnail_png=thumbnail_output.getvalue(),
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

    entries: list[CatalogEntry] = []
    skipped = 0
    for directory in directories:
        entry = _published_entry(directory)
        if entry is None:
            skipped += 1
        else:
            entries.append(entry)
    if not root.is_dir():
        return CatalogSnapshot("removed", (), message="USB media was removed during refresh")
    entries.sort(key=lambda entry: entry.capture_id, reverse=True)
    return CatalogSnapshot("ready", tuple(entries), skipped_count=skipped)


def load_catalog_animation(
    entry: CatalogEntry, display_size: tuple[int, int]
) -> tuple[list[Image.Image], list[int]]:
    """Decode and detach a selected published animation from removable storage."""

    from .ui import _load_review_frames

    return _load_review_frames(entry.animation, display_size)
