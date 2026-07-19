"""Deterministic environment and screenshot helpers for headless Qt tests.

This module intentionally imports only the Python standard library.  A Qt test
runner can use it before importing PySide6, while contract-only CI can exercise
the same route and evidence rules without installing Qt.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .contract import load_contract, png_dimensions

HEADLESS_ENVIRONMENT = {
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "QSG_RENDER_LOOP": "basic",
    "QSG_RHI_BACKEND": "software",
    "QT_QPA_PLATFORM": "offscreen",
    "QT_QUICK_CONTROLS_STYLE": "Basic",
    "TZ": "UTC",
}
WAYLAND_ENVIRONMENT = {"QT_QPA_PLATFORM": "wayland"}


@dataclass(frozen=True)
class ScreenshotEvidence:
    route_id: str
    path: str
    width: int
    height: int
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def qt_environment(
    platform: str = "offscreen", *, base: Mapping[str, str] | None = None
) -> dict[str, str]:
    """Return a complete environment to install before importing PySide6."""

    if platform not in {"offscreen", "wayland"}:
        raise ValueError("platform must be 'offscreen' or 'wayland'")
    environment = dict(os.environ if base is None else base)
    if platform == "offscreen":
        environment.update(HEADLESS_ENVIRONMENT)
    else:
        environment.update(WAYLAND_ENVIRONMENT)
    return environment


def expected_screenshot_name(source_design: int, route_id: str) -> str:
    """Return the canonical filename for one route's native screenshot."""

    if source_design not in range(1, 8):
        raise ValueError("source_design must be in the range 1..7")
    if not route_id or any(
        character not in "abcdefghijklmnopqrstuvwxyz-" for character in route_id
    ):
        raise ValueError("route_id must contain lowercase ASCII letters and hyphens")
    return f"{source_design:02d}-{route_id}-800x480.png"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_screenshot_evidence(
    directory: Path, contract: dict[str, Any] | None = None
) -> tuple[list[ScreenshotEvidence], list[str]]:
    """Check the complete seven-route screenshot matrix and return stable evidence."""

    contract = load_contract() if contract is None else contract
    viewport = contract["viewport"]
    expected_dimensions = (viewport["width"], viewport["height"])
    records: list[ScreenshotEvidence] = []
    errors: list[str] = []
    for route in contract["routes"]:
        filename = expected_screenshot_name(route["source_design"], route["id"])
        screenshot = directory / filename
        if not screenshot.is_file():
            errors.append(f"missing screenshot: {filename}")
            continue
        try:
            width, height = png_dimensions(screenshot)
        except (OSError, ValueError) as exc:
            errors.append(f"invalid screenshot {filename}: {exc}")
            continue
        if (width, height) != expected_dimensions:
            errors.append(
                f"screenshot {filename} is {width}x{height}; "
                f"expected {expected_dimensions[0]}x{expected_dimensions[1]}"
            )
        records.append(
            ScreenshotEvidence(
                route_id=route["id"],
                path=filename,
                width=width,
                height=height,
                sha256=sha256_file(screenshot),
            )
        )
    return records, errors
