"""Runtime resource and timing observations for capture evidence."""

from __future__ import annotations

import time
from pathlib import Path

import psutil


def resource_sample(phase: str, storage_path: Path | None = None) -> dict:
    """Capture a lightweight process, memory, storage, and load snapshot."""
    process = psutil.Process()
    process_cpu = process.cpu_times()
    memory = psutil.virtual_memory()
    disk_path = storage_path if storage_path and storage_path.exists() else Path("/")
    disk = psutil.disk_usage(disk_path)
    return {
        "phase": phase,
        "pi_monotonic_ns": time.monotonic_ns(),
        "process_cpu_user_seconds": process_cpu.user,
        "process_cpu_system_seconds": process_cpu.system,
        "process_rss_bytes": process.memory_info().rss,
        "available_memory_bytes": memory.available,
        "storage_free_bytes": disk.free,
        "storage_sample_path": str(disk_path),
        "system_load_average_1m": psutil.getloadavg()[0],
    }
