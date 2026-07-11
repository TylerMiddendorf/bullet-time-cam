"""Atomic capture persistence and manifest maintenance."""

from __future__ import annotations

import json
import os
import time
import uuid
import zlib
from pathlib import Path


def atomic_json(path: Path, value: dict) -> None:
    temp = path.with_suffix(path.suffix + ".part")
    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def commit_capture(root: Path, metadata: dict, jpeg: bytes, metrics: dict) -> tuple[Path, dict]:
    capture_id = f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}_{uuid.uuid4().hex[:8]}"
    capture_dir = root / capture_id
    capture_dir.mkdir(parents=True, exist_ok=False)
    part = capture_dir / "camera_01.jpg.part"
    final = capture_dir / "camera_01.jpg"
    with part.open("wb") as handle:
        handle.write(jpeg)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(part, final)
    checksum = zlib.crc32(jpeg) & 0xFFFFFFFF
    manifest = {
        "schema_version": 1,
        "capture_id": capture_id,
        "status": "complete",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "timing_basis": "Pi durations use monotonic_ns; node microseconds are unsynchronized",
        "node": metadata,
        "files": [{"path": final.name, "role": "original", "bytes": len(jpeg), "crc32": f"{checksum:08x}"}],
        "metrics": metrics,
        "errors": [],
        "limitations": ["display timestamp is a software render callback, not a photon measurement"],
    }
    atomic_json(capture_dir / "manifest.json", manifest)
    try:
        directory_fd = os.open(capture_dir, os.O_RDONLY)
        os.fsync(directory_fd)
        os.close(directory_fd)
    except OSError:
        pass
    return final, manifest

