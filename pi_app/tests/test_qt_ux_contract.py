import copy
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pi_app.qt_validation.contract import (
    EXPECTED_ROUTE_IDS,
    REPOSITORY_ROOT,
    load_contract,
    png_dimensions,
    validate_contract,
)
from pi_app.qt_validation.headless import (
    collect_screenshot_evidence,
    expected_screenshot_name,
    qt_environment,
)
from pi_app.tools.smoke_qt_qml import build_parser as build_qml_smoke_parser


def _minimal_png_header(width: int, height: int) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", width, height)
    )


class QtUxContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_contract()

    def test_repository_contract_passes(self):
        report = validate_contract(self.contract)
        self.assertTrue(report.ok, report.errors)
        self.assertEqual(report.route_count, 7)

    def test_all_source_rasters_are_1619_by_971(self):
        for route in self.contract["routes"]:
            with self.subTest(route=route["id"]):
                path = REPOSITORY_ROOT / route["source_mockup"]
                self.assertEqual(png_dimensions(path), (1619, 971))

    def test_routes_have_canonical_ids_and_native_paths(self):
        routes = self.contract["routes"]
        self.assertEqual(tuple(route["id"] for route in routes), EXPECTED_ROUTE_IDS)
        self.assertEqual(len({route["path"] for route in routes}), 7)
        self.assertEqual(self.contract["viewport"]["layout_mode"], "native")

    def test_runtime_package_set_is_minimal_and_effects_is_conditional(self):
        self.assertEqual(
            self.contract["runtime"]["apt_packages"],
            [
                "python3-pyside6.qtquick",
                "qml6-module-qtquick-controls",
                "qml6-module-qtquick-layouts",
                "qml6-module-qtqml-workerscript",
                "qt6-wayland",
            ],
        )
        self.assertEqual(
            self.contract["runtime"]["conditional_apt_packages"],
            {"qml6-module-qtquick-effects": "only-if-QML-imports-QtQuick.Effects"},
        )
        requirement_lines = [
            line.strip()
            for line in (REPOSITORY_ROOT / "pi_app" / "system-requirements-qt.txt")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(requirement_lines, self.contract["runtime"]["apt_packages"])

    def test_validator_rejects_scope_expansion(self):
        unsafe = copy.deepcopy(self.contract)
        unsafe["scope"]["battery_ui"] = True
        unsafe["scope"]["hotspot_claims"] = True
        report = validate_contract(unsafe)
        self.assertFalse(report.ok)
        self.assertIn("scope battery_ui must be False", report.errors)
        self.assertIn("scope hotspot_claims must be False", report.errors)

    def test_validator_rejects_forbidden_rendered_claim(self):
        unsafe = copy.deepcopy(self.contract)
        unsafe["routes"][0]["rendered_text"].append("HOTSPOT ON")
        report = validate_contract(unsafe)
        self.assertIn("route 'ready' renders forbidden term 'hotspot'", report.errors)

    def test_validator_rejects_control_center_node_command(self):
        unsafe = copy.deepcopy(self.contract)
        route = next(
            item for item in unsafe["routes"] if item["id"] == "four-camera-control-center"
        )
        route["settings_mode"] = "enabled"
        route["node_commands"].append("SET_EXPOSURE")
        report = validate_contract(unsafe)
        self.assertIn("control center settings must be disabled", report.errors)
        self.assertIn("control center must not expose node commands", report.errors)

    def test_validator_rejects_library_mutation_and_multimedia(self):
        unsafe = copy.deepcopy(self.contract)
        library = next(item for item in unsafe["routes"] if item["id"] == "removable-media-library")
        library["mutating_operations"].append("DELETE")
        viewer = next(item for item in unsafe["routes"] if item["id"] == "gif-viewer")
        viewer["qt_modules"].append("QtMultimedia")
        report = validate_contract(unsafe)
        self.assertIn("library must not expose mutating operations", report.errors)
        self.assertIn("viewer must not depend on QtMultimedia", report.errors)

    def test_cli_emits_stable_json_report(self):
        result = subprocess.run(
            [sys.executable, "-m", "pi_app.tools.validate_qt_ux_contract", "--json"],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["route_count"], 7)
        self.assertEqual(report["errors"], [])


class HeadlessQtUtilityTests(unittest.TestCase):
    def test_headless_and_wayland_environments_are_explicit(self):
        headless = qt_environment("offscreen", base={"KEEP": "yes"})
        self.assertEqual(headless["KEEP"], "yes")
        self.assertEqual(headless["QT_QPA_PLATFORM"], "offscreen")
        self.assertEqual(headless["QSG_RHI_BACKEND"], "software")
        wayland = qt_environment("wayland", base={})
        self.assertEqual(wayland, {"QT_QPA_PLATFORM": "wayland"})

    def test_screenshot_names_are_deterministic(self):
        self.assertEqual(
            expected_screenshot_name(4, "static-preview-placeholder"),
            "04-static-preview-placeholder-800x480.png",
        )
        with self.assertRaises(ValueError):
            expected_screenshot_name(8, "extra")

    def test_screenshot_matrix_checks_dimensions_and_hashes(self):
        contract = load_contract()
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            for route in contract["routes"]:
                filename = expected_screenshot_name(route["source_design"], route["id"])
                (directory / filename).write_bytes(_minimal_png_header(800, 480))
            records, errors = collect_screenshot_evidence(directory, contract)
        self.assertEqual(errors, [])
        self.assertEqual(len(records), 7)
        self.assertTrue(all(record.width == 800 for record in records))
        self.assertTrue(all(len(record.sha256) == 64 for record in records))

    def test_screenshot_matrix_reports_missing_and_wrong_size(self):
        contract = load_contract()
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            first = contract["routes"][0]
            filename = expected_screenshot_name(first["source_design"], first["id"])
            (directory / filename).write_bytes(_minimal_png_header(801, 480))
            _, errors = collect_screenshot_evidence(directory, contract)
        self.assertEqual(len(errors), 7)
        self.assertIn("is 801x480; expected 800x480", errors[0])

    def test_qml_smoke_parser_is_bounded_and_headless_by_default(self):
        arguments = build_qml_smoke_parser().parse_args(["--qml", "Main.qml"])
        self.assertEqual(arguments.platform, "offscreen")
        self.assertEqual(arguments.timeout_ms, 5000)
        self.assertEqual(arguments.required_object, "startupLogo")


if __name__ == "__main__":
    unittest.main()
