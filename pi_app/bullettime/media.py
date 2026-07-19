"""Atomic multi-camera persistence and GIF generation."""

from __future__ import annotations

import io
import os
import shutil
import zlib
from pathlib import Path

from PIL import Image

from .coordinator import CompletedCapture
from .storage import _fsync_directory, atomic_json


def animation_sequence(camera_ids: list[int]) -> list[int]:
    """Return one forward/backward pass without duplicating either endpoint."""
    if len(camera_ids) < 2:
        return list(camera_ids)
    return camera_ids + camera_ids[-2:0:-1]


def _display_frame(payload: bytes, max_width: int | None) -> Image.Image:
    with Image.open(io.BytesIO(payload)) as source:
        frame = source.convert("RGB")
    if max_width and frame.width > max_width:
        height = max(1, round(frame.height * max_width / frame.width))
        frame = frame.resize((max_width, height), Image.Resampling.LANCZOS)
    return frame


def _write_library_preview(frame: Image.Image, path: Path) -> dict:
    """Write the small still used by the library without reopening the GIF."""
    preview = frame.copy()
    preview.thumbnail((240, 135), Image.Resampling.LANCZOS)
    preview.save(path, format="JPEG", quality=72, optimize=True)
    payload = path.read_bytes()
    return {
        "path": path.name,
        "role": "library_preview",
        "bytes": len(payload),
        "crc32": f"{zlib.crc32(payload) & 0xFFFFFFFF:08x}",
        "width": preview.width,
        "height": preview.height,
    }


def commit_capture_set(
    root: Path,
    capture: CompletedCapture,
    *,
    storage: dict,
    gif_frame_ms: int = 150,
    gif_max_width: int | None = 800,
) -> tuple[Path, dict]:
    """Publish one complete directory only after every artifact is durable."""
    if gif_frame_ms <= 0 or (gif_max_width is not None and gif_max_width <= 0):
        raise ValueError("GIF timing and dimensions must be positive")
    capture_dir = root / capture.capture_id
    staging_dir = root / f".{capture.capture_id}.part"
    staging_dir.mkdir(parents=False, exist_ok=False)
    files = []
    try:
        for camera_id, image in sorted(capture.images.items()):
            name = f"camera_{camera_id:02d}.jpg"
            part = staging_dir / f"{name}.part"
            final = staging_dir / name
            with part.open("wb") as handle:
                handle.write(image.payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(part, final)
            files.append(
                {
                    "path": name,
                    "role": "original",
                    "logical_camera_id": camera_id,
                    "bytes": len(image.payload),
                    "crc32": f"{zlib.crc32(image.payload) & 0xFFFFFFFF:08x}",
                }
            )

        ordered_ids = sorted(capture.images)
        sequence = animation_sequence(ordered_ids)
        review_name = f"camera_{ordered_ids[0]:02d}.jpg" if ordered_ids else ""
        if len(sequence) >= 2:
            frames_by_id = {
                camera_id: _display_frame(capture.images[camera_id].payload, gif_max_width)
                for camera_id in ordered_ids
            }
            frames = [frames_by_id[camera_id] for camera_id in sequence]
            files.append(
                _write_library_preview(
                    frames_by_id[ordered_ids[0]], staging_dir / "library_preview.jpg"
                )
            )
            gif_path = staging_dir / "bullet_time.gif"
            frames[0].save(
                gif_path,
                save_all=True,
                append_images=frames[1:],
                duration=gif_frame_ms,
                loop=0,
                format="GIF",
            )
            payload = gif_path.read_bytes()
            files.append(
                {
                    "path": gif_path.name,
                    "role": "animation",
                    "bytes": len(payload),
                    "crc32": f"{zlib.crc32(payload) & 0xFFFFFFFF:08x}",
                    "frame_count": len(sequence),
                    "camera_sequence": sequence,
                }
            )
            review_name = gif_path.name

        cameras = []
        for camera_id in sorted(set(capture.images) | set(capture.errors)):
            if camera_id in capture.images:
                image = capture.images[camera_id]
                cameras.append(
                    {
                        "logical_camera_id": camera_id,
                        "node_uid": image.node_uid,
                        "boot_id": image.boot_id,
                        "capture_seq": image.capture_seq,
                        "status": "complete",
                        "metrics": image.metadata.get("host_metrics", {}),
                    }
                )
            else:
                cameras.append({"logical_camera_id": camera_id, "status": "error"})
        manifest = {
            "schema_version": 2,
            "capture_id": capture.capture_id,
            "status": "partial" if capture.partial else "complete",
            "cameras": cameras,
            "files": files,
            "errors": [
                {
                    "logical_camera_id": failure.logical_camera_id,
                    "code": failure.code,
                    "message": failure.message,
                }
                for _, failure in sorted(capture.errors.items())
            ],
            "metrics": {
                "pi_monotonic_ns": {
                    "first_capture_started_ns": capture.first_started_ns,
                    "capture_set_completed_ns": capture.completed_ns,
                },
                "durations_ms": {
                    "capture_set": (capture.completed_ns - capture.first_started_ns) / 1_000_000
                },
            },
            "storage": storage,
        }
        atomic_json(staging_dir / "manifest.json", manifest)
        _fsync_directory(staging_dir)
        os.replace(staging_dir, capture_dir)
        _fsync_directory(root)
        return capture_dir / review_name, manifest
    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)
        raise
