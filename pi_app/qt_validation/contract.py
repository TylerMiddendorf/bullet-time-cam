"""Dependency-free validation for the Qt touchscreen UX contract."""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path(__file__).with_name("ux_contract.json")
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_ROUTE_IDS = (
    "ready",
    "progress",
    "partial-review",
    "static-preview-placeholder",
    "four-camera-control-center",
    "removable-media-library",
    "gif-viewer",
)
EXPECTED_SOURCE_DESIGNS = tuple(range(1, 8))
REQUIRED_APT_PACKAGES = {
    "python3-pyside6.qtcore",
    "python3-pyside6.qtgui",
    "python3-pyside6.qtqml",
    "python3-pyside6.qtquick",
    "qml6-module-qtquick",
    "qml6-module-qtquick-controls",
    "qt6-wayland",
}


@dataclass(frozen=True)
class ContractReport:
    """A stable, serializable validation result."""

    contract_version: int
    route_count: int
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "route_count": self.route_count,
            "status": "PASS" if self.ok else "FAIL",
            "errors": list(self.errors),
        }


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    """Load a contract as UTF-8 JSON without importing Qt or third-party code."""

    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError("contract root must be an object")
    return value


def png_dimensions(path: Path) -> tuple[int, int]:
    """Read dimensions from a PNG IHDR without Pillow or Qt."""

    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG file: {path}")
    if header[12:16] != b"IHDR":
        raise ValueError(f"PNG does not begin with IHDR: {path}")
    return struct.unpack(">II", header[16:24])


def _is_non_empty_string_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item for item in value)
    )


def _validate_bounds(contract: dict[str, Any], errors: list[str]) -> None:
    viewport = contract.get("viewport", {})
    width = viewport.get("width")
    height = viewport.get("height")
    if (width, height) != (800, 480):
        errors.append("viewport must be native 800x480")
        return
    if viewport.get("layout_mode") != "native":
        errors.append("viewport layout_mode must be native")
    for name, bounds in contract.get("named_bounds", {}).items():
        if not (
            isinstance(bounds, list)
            and len(bounds) == 4
            and all(isinstance(value, int) for value in bounds)
        ):
            errors.append(f"named bound {name!r} must contain four integers")
            continue
        x, y, object_width, object_height = bounds
        if min(x, y, object_width, object_height) < 0:
            errors.append(f"named bound {name!r} contains a negative value")
        if x + object_width > width or y + object_height > height:
            errors.append(f"named bound {name!r} exceeds the 800x480 viewport")


def _validate_runtime(contract: dict[str, Any], errors: list[str]) -> None:
    runtime = contract.get("runtime", {})
    expected = {
        "architecture": "arm64",
        "qt_series": "6.8",
        "pyside_series": "6.8",
        "production_platform": "wayland",
        "headless_platform": "offscreen",
    }
    for key, value in expected.items():
        if runtime.get(key) != value:
            errors.append(f"runtime {key} must be {value!r}")
    if runtime.get("production_environment", {}).get("QT_QPA_PLATFORM") != "wayland":
        errors.append("production QT_QPA_PLATFORM must be wayland")
    packages = runtime.get("apt_packages", [])
    if not isinstance(packages, list) or packages != sorted(set(packages)):
        errors.append("runtime apt_packages must be unique and sorted")
    missing = sorted(REQUIRED_APT_PACKAGES.difference(packages))
    if missing:
        errors.append(f"runtime apt_packages missing: {', '.join(missing)}")
    if "QtMultimedia" not in runtime.get("forbidden_qt_modules", []):
        errors.append("QtMultimedia must remain explicitly forbidden")


def _validate_scope(contract: dict[str, Any], errors: list[str]) -> None:
    expected = {
        "camera_count": 4,
        "live_preview_backend": False,
        "multimedia_dependency": False,
        "battery_ui": False,
        "battery_reserved_space": False,
        "hotspot_claims": False,
        "node_setting_commands": False,
        "library_is_read_only": True,
        "library_storage": "removable-usb-only",
    }
    scope = contract.get("scope", {})
    for key, value in expected.items():
        if scope.get(key) != value:
            errors.append(f"scope {key} must be {value!r}")


def _validate_route(
    route: dict[str, Any],
    contract: dict[str, Any],
    repository_root: Path,
    errors: list[str],
) -> None:
    route_id = route.get("id", "<missing>")
    for key in ("id", "path", "source_mockup", "product_tier"):
        if not isinstance(route.get(key), str) or not route[key]:
            errors.append(f"route {route_id!r} has invalid {key}")
    if not _is_non_empty_string_list(route.get("required_objects")):
        errors.append(f"route {route_id!r} must declare required_objects")
    if not isinstance(route.get("rendered_text"), list):
        errors.append(f"route {route_id!r} rendered_text must be a list")
    if not isinstance(route.get("allowed_commands"), list):
        errors.append(f"route {route_id!r} allowed_commands must be a list")
    if not isinstance(route.get("interactive_objects"), list):
        errors.append(f"route {route_id!r} interactive_objects must be a list")

    source = repository_root / str(route.get("source_mockup", ""))
    if not source.is_file():
        errors.append(f"route {route_id!r} source mockup is missing: {source}")
    else:
        expected_raster = contract.get("source_raster", {})
        dimensions = (expected_raster.get("width"), expected_raster.get("height"))
        try:
            actual = png_dimensions(source)
        except (OSError, ValueError) as exc:
            errors.append(f"route {route_id!r} source mockup cannot be read: {exc}")
        else:
            if actual != dimensions:
                errors.append(
                    f"route {route_id!r} source mockup is {actual[0]}x{actual[1]}, "
                    f"expected {dimensions[0]}x{dimensions[1]}"
                )

    rendered_text = "\n".join(str(item) for item in route.get("rendered_text", [])).casefold()
    for term in contract.get("forbidden_rendered_terms", []):
        if str(term).casefold() in rendered_text:
            errors.append(f"route {route_id!r} renders forbidden term {term!r}")

    if route_id == "static-preview-placeholder":
        fixture = contract.get("preview_fixture", {})
        if fixture.get("required_label") not in route.get("rendered_text", []):
            errors.append("static preview route must render DEMO PLACEHOLDER")
        if route.get("fixture") != fixture.get("path"):
            errors.append("static preview route must use the approved fixture path")
        if route.get("allowed_commands"):
            errors.append("static preview route must not emit commands")
    elif route_id == "four-camera-control-center":
        if route.get("camera_count") != 4:
            errors.append("control center must model exactly four cameras")
        if route.get("settings_mode") != "disabled":
            errors.append("control center settings must be disabled")
        if not _is_non_empty_string_list(route.get("disabled_settings")):
            errors.append("control center must identify disabled settings")
        if route.get("node_commands") != []:
            errors.append("control center must not expose node commands")
    elif route_id == "removable-media-library":
        if route.get("storage_scope") != "removable-usb-only":
            errors.append("library must read only removable USB media")
        if route.get("mutating_operations") != []:
            errors.append("library must not expose mutating operations")
    elif route_id == "gif-viewer":
        if route.get("media_type") != "image/gif":
            errors.append("viewer must consume a real GIF")
        if route.get("media_source") != "real-gif-file":
            errors.append("viewer media source must be a real GIF file")
        if route.get("decoder") != "QtQuick.AnimatedImage":
            errors.append("viewer must use QtQuick.AnimatedImage")
        modules = route.get("qt_modules", [])
        if "QtMultimedia" in modules:
            errors.append("viewer must not depend on QtMultimedia")


def validate_contract(
    contract: dict[str, Any] | None = None,
    *,
    contract_path: Path = CONTRACT_PATH,
    repository_root: Path = REPOSITORY_ROOT,
) -> ContractReport:
    """Validate route coverage, dimensions, scope, and runtime policy."""

    errors: list[str] = []
    if contract is None:
        try:
            contract = load_contract(contract_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return ContractReport(0, 0, (f"contract cannot be loaded: {exc}",))

    version = contract.get("contract_version", 0)
    if version != 2:
        errors.append("contract_version must be 2")
    if contract.get("source_raster") != {
        "width": 1619,
        "height": 971,
        "usage": "visual-reference-only",
    }:
        errors.append("source_raster must be 1619x971 and visual-reference-only")

    _validate_bounds(contract, errors)
    _validate_runtime(contract, errors)
    _validate_scope(contract, errors)

    routes = contract.get("routes", [])
    if not isinstance(routes, list):
        errors.append("routes must be a list")
        routes = []
    route_ids = [route.get("id") for route in routes if isinstance(route, dict)]
    route_paths = [route.get("path") for route in routes if isinstance(route, dict)]
    source_designs = [route.get("source_design") for route in routes if isinstance(route, dict)]
    if tuple(route_ids) != EXPECTED_ROUTE_IDS:
        errors.append("routes must cover the seven designs in canonical order")
    if len(route_paths) != len(set(route_paths)):
        errors.append("route paths must be unique")
    if tuple(source_designs) != EXPECTED_SOURCE_DESIGNS:
        errors.append("source_design values must be exactly 1 through 7")
    for route in routes:
        if isinstance(route, dict):
            _validate_route(route, contract, repository_root, errors)
        else:
            errors.append("every route must be an object")

    scenarios = contract.get("required_scenarios", [])
    expected_scenarios = [f"UX-{number:03d}" for number in range(1, 23)]
    if scenarios != expected_scenarios:
        errors.append("required_scenarios must be the ordered UX-001..UX-022 set")

    return ContractReport(
        contract_version=version if isinstance(version, int) else 0,
        route_count=len(routes),
        errors=tuple(errors),
    )
