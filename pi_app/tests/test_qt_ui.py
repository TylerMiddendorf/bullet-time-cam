import json
import queue
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from pi_app.bullettime.media_catalog import load_catalog_animation, scan_capture_catalog
from pi_app.bullettime.qt_ui import ALL_ROUTES, QtUiController, _AsyncResultQueue
from pi_app.bullettime.storage import StorageUsage

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

        self.assertTrue(controller.navigate("capture"))
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

    def test_capture_route_is_the_only_touchscreen_route_that_can_take_a_photo(self):
        controller = QtUiController(queue.Queue())
        controller.handle_event({"state": "READY", "connected_camera_ids": [1, 2, 3, 4]})

        for route in ALL_ROUTES - {"capture"}:
            with self.subTest(route=route):
                self.assertTrue(controller.navigate(route))
                self.assertFalse(controller.can_capture)

        self.assertTrue(controller.navigate("capture"))
        self.assertTrue(controller.can_capture)

    def test_delete_requires_confirmation_and_returns_to_refreshed_library(self):
        controller = QtUiController(queue.Queue())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            published_capture(root, "capture-delete")
            published_capture(root, "capture-retain")
            controller.apply_catalog(scan_capture_catalog(root))
            selected = controller.library_items[controller.selected_library_index]
            delete_requests = []
            controller.set_catalog_callbacks(
                lambda: None, lambda _entry: None, delete_requests.append
            )

            self.assertTrue(controller.prompt_delete_selected())
            self.assertTrue(controller.delete_confirmation_visible)
            self.assertEqual(controller.pending_delete_title, selected.capture_id)
            controller.cancel_delete()
            self.assertFalse(controller.delete_confirmation_visible)
            self.assertEqual(delete_requests, [])

            self.assertTrue(controller.prompt_delete_selected())
            self.assertTrue(controller.confirm_delete())
            self.assertEqual(delete_requests, [selected])
            self.assertEqual(controller.catalog_status, "deleting")

            selected.directory.rename(root / "deleted-off-thread")
            refreshed = scan_capture_catalog(root)
            controller.apply_deleted_catalog(selected, refreshed, None)
            self.assertEqual(controller.route, "library")
            self.assertFalse(controller.delete_confirmation_visible)
            self.assertNotIn(
                selected.capture_id, [item.capture_id for item in controller.library_items]
            )
            self.assertIn("Deleted", controller.catalog_message)

    def test_delete_failure_is_visible_and_does_not_drop_catalog_entry(self):
        controller = QtUiController(queue.Queue())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            published_capture(root, "capture-keep")
            controller.apply_catalog(scan_capture_catalog(root))
            entry = controller.library_items[0]

            controller.apply_deleted_catalog(entry, None, OSError("drive removed"))

            self.assertEqual(controller.route, "library")
            self.assertEqual(controller.catalog_status, "removed")
            self.assertEqual(controller.library_items, [entry])
            self.assertIn("drive removed", controller.catalog_message)

    def test_library_exposes_used_and_available_usb_capacity(self):
        controller = QtUiController(queue.Queue())
        usage = StorageUsage(
            available=True,
            total_bytes=250_000_000_000,
            used_bytes=18_600_000_000,
            free_bytes=231_400_000_000,
        )

        controller.apply_catalog(scan_capture_catalog(None), usage)

        self.assertEqual(controller.storage_used_text, "18.6 GB")
        self.assertEqual(controller.storage_available_text, "231.4 GB")
        self.assertAlmostEqual(controller.storage_used_fraction, 0.0744)

        controller.apply_catalog(scan_capture_catalog(None), StorageUsage(available=False))
        self.assertEqual(controller.storage_used_text, "--")
        self.assertEqual(controller.storage_available_text, "UNAVAILABLE")
        self.assertEqual(controller.storage_used_fraction, 0.0)

    def test_async_library_refresh_applies_catalog_and_capacity_arguments(self):
        controller = QtUiController(queue.Queue())
        results = _AsyncResultQueue()
        usage = StorageUsage(
            available=True,
            total_bytes=250_000_000_000,
            used_bytes=3_800_000,
            free_bytes=249_996_200_000,
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            published_capture(root, "capture-from-new-photo")
            controller.set_catalog_callbacks(
                lambda: results.put(scan_capture_catalog(root), usage),
                lambda _entry: None,
            )

            self.assertTrue(controller.navigate("library"))
            self.assertEqual(controller.catalog_status, "loading")
            self.assertEqual(results.drain(controller.apply_catalog), 1)

        self.assertEqual(controller.catalog_status, "ready")
        self.assertEqual(
            [entry.capture_id for entry in controller.library_items],
            ["capture-from-new-photo"],
        )
        self.assertEqual(controller.storage_used_text, "3.8 MB")
        self.assertEqual(controller.storage_available_text, "250.0 GB")
        self.assertEqual(results.drain(controller.apply_catalog), 0)


class QmlContractTests(unittest.TestCase):
    def test_all_seven_design_routes_are_native_qml_components(self):
        pages = {
            "ready": "ReadyPage.qml",
            "progress": "ProgressPage.qml",
            "review": "ReviewPage.qml",
            "capture": "CapturePage.qml",
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
        self.assertIn("flags: Qt.FramelessWindowHint", harness)

    def test_runtime_is_fixed_800x480_and_contains_no_power_or_network_status_space(self):
        content = "\n".join(path.read_text(encoding="utf-8") for path in QML_ROOT.rglob("*.qml"))
        main = (QML_ROOT / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("width: 800", main)
        self.assertIn("height: 480", main)
        self.assertNotIn("BATTERY", content.upper())
        self.assertNotIn("HOTSPOT", content.upper())
        self.assertNotIn(" LIVE", content.upper())

    def test_capture_placeholder_is_truthfully_labeled_and_settings_are_inert(self):
        placeholder = (QML_ROOT / "components" / "PlaceholderSurface.qml").read_text(
            encoding="utf-8"
        )
        setting = (QML_ROOT / "components" / "SettingCard.qml").read_text(encoding="utf-8")
        self.assertIn('text: "STATIC PLACEHOLDER"', placeholder)
        self.assertIn('text: "CAMERA VIEW NOT CONNECTED"', placeholder)
        self.assertIn("bridge.previewPlaceholder", placeholder)
        self.assertIn("enabled: false", setting)
        self.assertNotIn("bridge.", setting)

    def test_ready_navigation_has_settings_library_and_capture_without_capture_command(self):
        ready = (QML_ROOT / "pages" / "ReadyPage.qml").read_text(encoding="utf-8")
        self.assertIn('objectName: "settingsButton"', ready)
        self.assertIn('label: "\\u2699"', ready)
        self.assertIn('objectName: "libraryButton"', ready)
        self.assertIn('label: "LIBRARY"', ready)
        self.assertIn('objectName: "captureNavigationButton"', ready)
        self.assertIn('bridge.navigate("capture")', ready)
        self.assertNotIn("bridge.capture()", ready)

    def test_library_is_scrollable_and_primary_touch_targets_are_not_tiny(self):
        library = (QML_ROOT / "pages" / "LibraryPage.qml").read_text(encoding="utf-8")
        ready = (QML_ROOT / "pages" / "ReadyPage.qml").read_text(encoding="utf-8")
        touch_button = (QML_ROOT / "components" / "TouchButton.qml").read_text(encoding="utf-8")
        self.assertIn("GridView", library)
        self.assertIn("boundsBehavior: Flickable.StopAtBounds", library)
        self.assertIn("snapMode: GridView.SnapToRow", library)
        self.assertIn("function changeLibraryPage(offset)", library)
        self.assertIn("libraryPageCount", library)
        self.assertIn('objectName: "libraryPageUp"', library)
        self.assertIn('label: "\\u25B2"', library)
        self.assertIn('objectName: "libraryPageDown"', library)
        self.assertIn('label: "\\u25BC"', library)
        self.assertIn("bridge.selectLibraryItem(targetIndex)", library)
        self.assertIn('text: "REMOVABLE USB"', library)
        self.assertIn("fontSizeMode: Text.Fit", library)
        self.assertNotIn("height: 36", ready)
        self.assertIn("fontSizeMode: Text.Fit", touch_button)
        self.assertIn("width: parent.width - 24", touch_button)
        self.assertIn('objectName: "deleteSelectedButton"', library)
        self.assertIn("bridge.promptDeleteSelected()", library)
        self.assertIn('objectName: "storageUsageMetric"', library)
        self.assertIn('text: "USED"', library)
        self.assertIn('text: "AVAILABLE"', library)
        self.assertIn("bridge.storageUsedText", library)
        self.assertIn("bridge.storageAvailableText", library)
        self.assertIn("bridge.storageUsedFraction", library)

        viewer = (QML_ROOT / "pages" / "ViewerPage.qml").read_text(encoding="utf-8")
        confirmation = (QML_ROOT / "components" / "DeleteConfirmation.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn('objectName: "viewerDeleteButton"', viewer)
        self.assertIn("fontSizeMode: Text.Fit", viewer)
        self.assertIn('objectName: "confirmDeleteButton"', confirmation)
        self.assertIn("This cannot be undone", confirmation)

    def test_contract_matches_detached_viewer_and_inert_settings(self):
        contract = json.loads(
            (REPO_ROOT / "pi_app" / "qt_validation" / "ux_contract.json").read_text(
                encoding="utf-8"
            )
        )
        viewer_contract = next(route for route in contract["routes"] if route["id"] == "gif-viewer")
        viewer = (QML_ROOT / "pages" / "ViewerPage.qml").read_text(encoding="utf-8")
        control = (QML_ROOT / "pages" / "ControlCenterPage.qml").read_text(encoding="utf-8")

        self.assertEqual(viewer_contract["decoder"], "Python.Pillow+QtQuick.Image")
        self.assertEqual(
            viewer_contract["allowed_commands"],
            [
                "PROMPT_DELETE_CAPTURE_SET",
                "CONFIRM_DELETE_CAPTURE_SET",
                "NAVIGATE_LIBRARY",
            ],
        )
        self.assertIn("Image {", viewer)
        self.assertNotIn("AnimatedImage", viewer)
        self.assertNotIn("QtMultimedia", viewer)
        self.assertIn('status: "V2 · DISABLED"', control)
        setting = (QML_ROOT / "components" / "SettingCard.qml").read_text(encoding="utf-8")
        self.assertNotIn("onTapped", setting)

    def test_qt_import_remains_lazy_for_headless_hosts(self):
        # Importing this module succeeds in CI without PySide6 installed.
        import pi_app.bullettime.qt_ui as qt_ui

        self.assertTrue(callable(qt_ui.run_qt_ui))


if __name__ == "__main__":
    unittest.main()
