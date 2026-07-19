import json
import queue
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from pi_app.bullettime.media_catalog import load_catalog_animation, scan_capture_catalog
from pi_app.bullettime.qt_ui import ALL_ROUTES, QtUiController

REPO_ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = REPO_ROOT / "pi_app" / "bullettime" / "qml"


def published_capture(root: Path, capture_id: str, *, partial: bool = False) -> Path:
    """Create a published capture fixture without importing another test module."""
    directory = root / capture_id
    directory.mkdir()
    animation = directory / "bullet_time.gif"
    frames = [Image.new("RGB", (24, 16), color) for color in ("red", "green")]
    frames[0].save(
        animation,
        save_all=True,
        append_images=frames[1:],
        duration=[80, 120],
        loop=0,
    )
    cameras = [
        {"logical_camera_id": camera_id, "status": "complete"}
        for camera_id in range(1, 4 if partial else 5)
    ]
    if partial:
        cameras.append({"logical_camera_id": 4, "status": "error"})
    manifest = {
        "schema_version": 2,
        "capture_id": capture_id,
        "status": "partial" if partial else "complete",
        "cameras": cameras,
        "files": [{"path": animation.name, "role": "animation"}],
    }
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return directory


class QtUiControllerTests(unittest.TestCase):
    def test_review_is_detached_before_removable_media_disappears(self):
        commands = queue.Queue()
        controller = QtUiController(commands)
        with tempfile.TemporaryDirectory() as temp:
            media = Path(temp) / "bullet_time.gif"
            frames = [Image.new("RGB", (16, 12), color) for color in ("red", "blue")]
            frames[0].save(
                media,
                save_all=True,
                append_images=frames[1:],
                duration=[80, 120],
                loop=0,
            )
            controller.handle_event(
                {"state": "REVIEW", "image": str(media), "manifest": {"cameras": []}}
            )
            media.unlink()

            self.assertEqual(controller.route, "review")
            self.assertEqual(len(controller.review_frames), 2)
            self.assertTrue(controller.image_source.startswith("data:image/png;base64,"))

    def test_session_library_opens_real_detached_review_in_viewer(self):
        controller = QtUiController(queue.Queue())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            published_capture(root, "capture-real")
            controller.apply_catalog(scan_capture_catalog(root))
            opened = []
            controller.set_catalog_callbacks(lambda: None, opened.append)

            self.assertEqual(controller.qml_library_items[0]["title"], "capture-real")
            self.assertEqual(controller.qml_library_items[0]["viewCount"], 4)
            self.assertTrue(controller.navigate("library"))
            self.assertTrue(controller.open_library_item(0))
            self.assertEqual(opened[0].capture_id, "capture-real")
            frames, durations = load_catalog_animation(opened[0], (800, 480))
            controller.apply_opened_catalog(opened[0], frames, durations, None)
            self.assertEqual(controller.route, "viewer")
            self.assertTrue(controller.image_source.startswith("data:image/png;base64,"))
            controller.advance_review_frame()
            self.assertTrue(controller.image_source.startswith("data:image/png;base64,"))

    def test_navigation_model_is_separate_from_capture_workflow_snapshot(self):
        commands = queue.Queue()
        controller = QtUiController(commands)
        controller.handle_event({"state": "READY", "connected_camera_ids": [1, 2, 3, 4]})

        self.assertTrue(controller.navigate("library"))
        controller.handle_event({"state": "READY", "connected_camera_ids": [1, 2, 3, 4]})
        self.assertEqual(controller.route, "library")
        self.assertEqual(controller.snapshot.state, "READY")

        self.assertTrue(controller.navigate("control"))
        self.assertTrue(controller.request_capture())
        self.assertEqual(commands.get_nowait(), "CAPTURE")
        self.assertEqual(controller.route, "progress")
        self.assertEqual(controller.snapshot.state, "LOADING")

    def test_unsupported_route_cannot_send_capture_command(self):
        commands = queue.Queue()
        controller = QtUiController(commands)
        controller.handle_event({"state": "READY", "connected_camera_ids": [1, 2, 3, 4]})
        controller.navigate("library")
        self.assertFalse(controller.request_capture())
        self.assertTrue(commands.empty())


class QmlContractTests(unittest.TestCase):
    def test_all_seven_design_routes_are_native_qml_components(self):
        pages = {
            "ready": "ReadyPage.qml",
            "progress": "ProgressPage.qml",
            "review": "ReviewPage.qml",
            "preview": "PreviewPage.qml",
            "control": "ControlCenterPage.qml",
            "library": "LibraryPage.qml",
            "viewer": "ViewerPage.qml",
        }
        self.assertEqual(set(pages), set(ALL_ROUTES))
        for route, filename in pages.items():
            with self.subTest(route=route):
                content = (QML_ROOT / "pages" / filename).read_text(encoding="utf-8")
                self.assertIn("import QtQuick", content)
                self.assertNotIn("designs/ux-mockups", content)

        harness = (QML_ROOT / "RouteHarness.qml").read_text(encoding="utf-8")
        for route in set(pages) - {"ready"}:
            self.assertIn(f'bridge.route === "{route}"', harness)
        self.assertIn("return readyPage", harness)
        self.assertIn('argumentValue("--media="', harness)

    def test_runtime_is_fixed_800x480_and_contains_no_power_or_network_status_space(self):
        content = "\n".join(path.read_text(encoding="utf-8") for path in QML_ROOT.rglob("*.qml"))
        main = (QML_ROOT / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("width: 800", main)
        self.assertIn("height: 480", main)
        self.assertNotIn("BATTERY", content.upper())
        self.assertNotIn("HOTSPOT", content.upper())
        self.assertNotIn(" LIVE", content.upper())

    def test_placeholder_is_truthfully_labeled_and_settings_are_inert(self):
        placeholder = (QML_ROOT / "components" / "PlaceholderSurface.qml").read_text(
            encoding="utf-8"
        )
        setting = (QML_ROOT / "components" / "SettingCard.qml").read_text(encoding="utf-8")
        self.assertIn('text: "DEMO PLACEHOLDER"', placeholder)
        self.assertIn('text: "PREVIEW NOT CONNECTED"', placeholder)
        self.assertIn("bridge.previewPlaceholder", placeholder)
        self.assertIn("enabled: false", setting)
        self.assertNotIn("bridge.", setting)

    def test_library_is_scrollable_and_primary_touch_targets_are_not_tiny(self):
        library = (QML_ROOT / "pages" / "LibraryPage.qml").read_text(encoding="utf-8")
        ready = (QML_ROOT / "pages" / "ReadyPage.qml").read_text(encoding="utf-8")
        self.assertIn("GridView", library)
        self.assertIn("boundsBehavior: Flickable.StopAtBounds", library)
        self.assertNotIn("height: 36", ready)

    def test_qt_import_remains_lazy_for_headless_hosts(self):
        # Importing this module succeeds in CI without PySide6 installed.
        import pi_app.bullettime.qt_ui as qt_ui

        self.assertTrue(callable(qt_ui.run_qt_ui))


if __name__ == "__main__":
    unittest.main()
