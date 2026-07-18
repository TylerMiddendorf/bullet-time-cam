"""Serial-device discovery for camera nodes."""

from __future__ import annotations

import glob
import os


def discover_ports() -> list[str]:
    """Return unique real paths for likely USB serial camera devices."""
    candidates = (
        glob.glob("/dev/serial/by-id/*") + glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*")
    )
    return list(dict.fromkeys(os.path.realpath(path) for path in candidates))
