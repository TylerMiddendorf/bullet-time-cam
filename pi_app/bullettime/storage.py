"""Atomic capture persistence and manifest maintenance."""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import time
import uuid
import zlib
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class StorageUnavailable(RuntimeError):
    """Raised when no writable USB-backed filesystem is available."""


@dataclass(frozen=True)
class UsbMount:
    mountpoint: Path
    source: str
    filesystem: str
    major_minor: str


@dataclass(frozen=True)
class StorageUsage:
    """Capacity figures for the active removable volume."""

    available: bool
    total_bytes: int = 0
    used_bytes: int = 0
    free_bytes: int = 0


_MOUNT_ESCAPE = re.compile(r"\\([0-7]{3})")
_CAPTURE_STAGING = re.compile(r"^\.\d{8}T\d{6}Z_[0-9a-f]{8}\.part$")


def read_storage_usage(root: Path | None) -> StorageUsage:
    """Read capacity from the active USB root without falling back elsewhere."""

    if root is None:
        return StorageUsage(available=False)
    try:
        usage = shutil.disk_usage(root)
    except OSError:
        return StorageUsage(available=False)
    return StorageUsage(
        available=True,
        total_bytes=usage.total,
        used_bytes=usage.used,
        free_bytes=usage.free,
    )


def _unescape_mount_field(value: str) -> str:
    return _MOUNT_ESCAPE.sub(lambda match: chr(int(match.group(1), 8)), value)


def is_usb_block_device(major_minor: str, sys_dev_block: Path = Path("/sys/dev/block")) -> bool:
    """Return whether a mounted block device descends from a USB sysfs device."""
    try:
        resolved = (sys_dev_block / major_minor).resolve(strict=True)
    except (FileNotFoundError, OSError):
        return False
    return any(part.lower().startswith("usb") for part in resolved.parts)


def discover_usb_mounts(
    mountinfo_path: Path = Path("/proc/self/mountinfo"),
    sys_dev_block: Path = Path("/sys/dev/block"),
) -> list[UsbMount]:
    """Find writable, mounted filesystems whose backing block device is USB."""
    mounts: list[UsbMount] = []
    try:
        lines = mountinfo_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise StorageUnavailable(f"cannot read mounted filesystems: {exc}") from exc

    for line in lines:
        fields = line.split()
        try:
            separator = fields.index("-")
            major_minor = fields[2]
            mountpoint = Path(_unescape_mount_field(fields[4]))
            mount_options = fields[5].split(",")
            filesystem = fields[separator + 1]
            source = _unescape_mount_field(fields[separator + 2])
        except (ValueError, IndexError):
            continue
        if "ro" in mount_options or mountpoint == Path("/"):
            continue
        if not is_usb_block_device(major_minor, sys_dev_block):
            continue
        mounts.append(UsbMount(mountpoint, source, filesystem, major_minor))
    return mounts


def discover_usb_block_devices(sys_class_block: Path = Path("/sys/class/block")) -> list[Path]:
    """Find USB disks/partitions that udisks can be asked to mount."""
    try:
        entries = list(sys_class_block.iterdir())
    except OSError:
        return []
    usb_entries: list[tuple[Path, Path, bool]] = []
    for entry in entries:
        try:
            resolved = entry.resolve(strict=True)
        except (FileNotFoundError, OSError):
            continue
        if not any(part.lower().startswith("usb") for part in resolved.parts):
            continue
        if entry.name.startswith(("loop", "ram", "zram")):
            continue
        is_partition = (entry / "partition").exists()
        usb_entries.append((entry, resolved, is_partition))
    partitioned_disks = {
        resolved.parent.name for _, resolved, is_partition in usb_entries if is_partition
    }
    devices: list[tuple[bool, Path]] = []
    for entry, _, is_partition in usb_entries:
        if not is_partition and entry.name in partitioned_disks:
            continue
        devices.append((is_partition, Path("/dev") / entry.name))
    # Prefer partitions. Whole-disk filesystems remain supported when no
    # partition table exists.
    return [device for _, device in sorted(devices, key=lambda item: (not item[0], str(item[1])))]


def auto_mount_usb_volumes(devices: Iterable[Path] | None = None) -> list[str]:
    """Ask udisks2 to mount detected USB block devices for the active user."""
    errors: list[str] = []
    candidates = list(devices) if devices is not None else discover_usb_block_devices()
    for device in candidates:
        try:
            completed = subprocess.run(
                ["udisksctl", "mount", "--no-user-interaction", "--block-device", str(device)],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
        except (FileNotFoundError, subprocess.SubprocessError, OSError) as exc:
            errors.append(f"{device}: {exc}")
            continue
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()
            errors.append(f"{device}: {detail or 'udisksctl mount failed'}")
    return errors


class UsbStorageResolver:
    """Resolve every capture to a currently mounted, writable USB volume."""

    def __init__(
        self,
        capture_directory: str = "BulletTime",
        preferred_mount_name: str | None = None,
        auto_mount: bool = True,
        mount_discovery: Callable[[], list[UsbMount]] | None = None,
        automounter: Callable[[], list[str]] | None = None,
        stale_staging_seconds: float = 3600,
    ) -> None:
        relative = Path(capture_directory)
        if relative.is_absolute() or ".." in relative.parts or relative == Path("."):
            raise ValueError("USB capture_directory must be a non-empty relative path")
        self.capture_directory = relative
        self.preferred_mount_name = preferred_mount_name
        self.auto_mount = auto_mount
        self._mount_discovery = mount_discovery or discover_usb_mounts
        self._automounter = automounter or auto_mount_usb_volumes
        if stale_staging_seconds < 0:
            raise ValueError("stale_staging_seconds must not be negative")
        self.stale_staging_seconds = stale_staging_seconds
        self.active_mount: UsbMount | None = None
        self.active_root: Path | None = None

    def _ordered_mounts(self) -> list[UsbMount]:
        mounts = self._mount_discovery()
        return sorted(
            mounts,
            key=lambda mount: (
                0
                if self.preferred_mount_name and mount.mountpoint.name == self.preferred_mount_name
                else 1,
                str(mount.mountpoint),
            ),
        )

    def _select(self, mounts: Iterable[UsbMount]) -> Path | None:
        for mount in mounts:
            if not mount.mountpoint.is_dir() or not os.access(mount.mountpoint, os.W_OK):
                continue
            root = mount.mountpoint / self.capture_directory
            try:
                root.mkdir(parents=True, exist_ok=True)
            except OSError:
                continue
            if not os.access(root, os.W_OK):
                continue
            removed = cleanup_stale_staging(root, self.stale_staging_seconds)
            for staging_dir in removed:
                LOGGER.warning("Removed stale uncommitted capture staging: %s", staging_dir)
            self.active_mount = mount
            self.active_root = root
            return root
        return None

    def resolve(self) -> Path:
        root = self._select(self._ordered_mounts())
        mount_errors: list[str] = []
        if root is None and self.auto_mount:
            mount_errors = self._automounter()
            root = self._select(self._ordered_mounts())
        if root is not None:
            return root
        self.active_mount = None
        self.active_root = None
        detail = f" Automatic mount errors: {'; '.join(mount_errors)}" if mount_errors else ""
        raise StorageUnavailable(
            "No writable USB storage is mounted. Insert a USB drive and try again." + detail
        )

    def manifest_details(self) -> dict:
        if self.active_mount is None or self.active_root is None:
            return {"transport": "usb", "available": False}
        return {
            "transport": "usb",
            "available": True,
            "mountpoint": str(self.active_mount.mountpoint),
            "source": self.active_mount.source,
            "filesystem": self.active_mount.filesystem,
            "capture_root": str(self.active_root),
        }


def atomic_json(path: Path, value: dict) -> None:
    temp = path.with_suffix(path.suffix + ".part")
    try:
        with temp.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    except Exception:
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _fsync_directory(path: Path) -> None:
    try:
        directory_fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    except OSError:
        pass
    finally:
        os.close(directory_fd)


def cleanup_stale_staging(
    root: Path, stale_after_seconds: float, *, now: float | None = None
) -> list[Path]:
    """Remove expired, unmistakably uncommitted capture staging directories."""
    if stale_after_seconds < 0:
        raise ValueError("stale_after_seconds must not be negative")
    cutoff = (time.time() if now is None else now) - stale_after_seconds
    removed: list[Path] = []
    try:
        entries = list(root.iterdir())
    except OSError:
        return removed
    for entry in entries:
        if not _CAPTURE_STAGING.fullmatch(entry.name) or entry.is_symlink():
            continue
        try:
            if not entry.is_dir() or entry.stat().st_mtime > cutoff:
                continue
            shutil.rmtree(entry)
            removed.append(entry)
        except OSError as exc:
            LOGGER.warning("Could not remove stale capture staging %s: %s", entry, exc)
            continue
    if removed:
        _fsync_directory(root)
    return removed


def commit_capture(root: Path, metadata: dict, jpeg: bytes, metrics: dict) -> tuple[Path, dict]:
    capture_id = f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}_{uuid.uuid4().hex[:8]}"
    capture_dir = root / capture_id
    staging_dir = root / f".{capture_id}.part"
    staging_dir.mkdir(parents=False, exist_ok=False)
    part = staging_dir / "camera_01.jpg.part"
    staged_final = staging_dir / "camera_01.jpg"
    final = capture_dir / staged_final.name
    checksum = zlib.crc32(jpeg) & 0xFFFFFFFF
    manifest = {
        "schema_version": 1,
        "capture_id": capture_id,
        "status": "complete",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "timing_basis": "Pi durations use monotonic_ns; node microseconds are unsynchronized",
        "node": metadata,
        "files": [
            {"path": final.name, "role": "original", "bytes": len(jpeg), "crc32": f"{checksum:08x}"}
        ],
        "metrics": metrics,
        "errors": [],
        "limitations": [
            "display timestamp is a software render callback, not a photon measurement"
        ],
    }
    try:
        with part.open("wb") as handle:
            handle.write(jpeg)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(part, staged_final)
        atomic_json(staging_dir / "manifest.json", manifest)
        _fsync_directory(staging_dir)
        os.replace(staging_dir, capture_dir)
        _fsync_directory(root)
    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)
        raise
    return final, manifest
