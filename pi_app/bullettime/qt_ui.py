"""Qt Quick touchscreen runtime with a testable, toolkit-neutral controller."""

from __future__ import annotations

import base64
import io
import logging
import queue
import subprocess
import threading
import time
from collections.abc import Callable
from pathlib import Path

from PIL import Image

from .gpio_trigger import HardwareTrigger
from .media_catalog import (
    CatalogEntry,
    CatalogSnapshot,
    delete_catalog_entry,
    load_catalog_animation,
    scan_capture_catalog,
)
from .storage import (
    StorageUnavailable,
    StorageUsage,
    UsbStorageResolver,
    atomic_json,
    read_storage_usage,
)
from .ui_model import PresentationState, UiSnapshot

LOGGER = logging.getLogger(__name__)
RUNTIME_ROUTES = frozenset({"ready", "progress", "review"})
SECONDARY_ROUTES = frozenset({"capture", "control", "library", "viewer"})
ALL_ROUTES = RUNTIME_ROUTES | SECONDARY_ROUTES
CAPTURE_ROUTES = frozenset({"capture"})
CAPTURE_STATES = frozenset({"READY", "REVIEW", "REVIEW_WITH_ERROR", "ERROR"})


class _AsyncResultQueue:
    """Transfer worker results to Qt while preserving callback arguments."""

    def __init__(self) -> None:
        self._results: queue.Queue = queue.Queue()

    def put(self, *values: object) -> None:
        self._results.put(values)

    def drain(self, apply_result: Callable[..., None]) -> int:
        applied = 0
        while True:
            try:
                values = self._results.get_nowait()
            except queue.Empty:
                return applied
            apply_result(*values)
            applied += 1


def _format_storage_bytes(value: int) -> str:
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f} GB"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f} MB"
    return f"{value / 1_000:.1f} KB"


def _frame_data_url(frame: Image.Image) -> str:
    output = io.BytesIO()
    frame.save(output, format="PNG")
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


class QtUiController:
    """Own UI state without importing PySide6, so headless tests remain portable."""

    def __init__(
        self,
        commands: queue.Queue,
        *,
        display_size: tuple[int, int] = (800, 480),
        on_changed: Callable[[], None] | None = None,
    ) -> None:
        self.commands = commands
        self.display_size = display_size
        self.presentation_state = PresentationState()
        self.route = "ready"
        self.review_frames: list[str] = []
        self.review_durations: list[int] = []
        self.review_index = 0
        self.library_items: list[CatalogEntry] = []
        self.selected_library_index = -1
        self.catalog_status = "idle"
        self.catalog_message = ""
        self.storage_usage = StorageUsage(available=False)
        self.delete_confirmation_visible = False
        self.pending_delete_entry: CatalogEntry | None = None
        self.last_manifest: dict | None = None
        self.display_timing_recorded = False
        self.camera_recovery_pending = False
        self.camera_recovery_message = ""
        self._on_changed = on_changed or (lambda: None)
        self._refresh_catalog: Callable[[], None] = lambda: None
        self._refresh_storage: Callable[[], None] = lambda: None
        self._open_catalog_entry: Callable[[CatalogEntry], None] = lambda _entry: None
        self._delete_catalog_entry: Callable[[CatalogEntry], None] = lambda _entry: None
        self._recover_cameras: Callable[[], None] = lambda: None

    @property
    def snapshot(self) -> UiSnapshot:
        return self.presentation_state.snapshot

    @property
    def image_source(self) -> str:
        if not self.review_frames:
            return ""
        return self.review_frames[self.review_index]

    @property
    def qml_library_items(self) -> list[dict]:
        return [
            {
                "title": item.capture_id,
                "viewCount": item.view_count,
                "partial": item.status == "partial",
                "thumbnail": (
                    "data:image/png;base64," + base64.b64encode(item.thumbnail_png).decode("ascii")
                    if item.thumbnail_png
                    else ""
                ),
            }
            for item in self.library_items
        ]

    @property
    def can_capture(self) -> bool:
        return self.route in CAPTURE_ROUTES and self.snapshot.state in CAPTURE_STATES

    @property
    def can_recover_cameras(self) -> bool:
        return (
            self.route == "control"
            and self.snapshot.state in CAPTURE_STATES
            and not self.snapshot.capture_in_progress
            and not self.camera_recovery_pending
        )

    @property
    def viewer_view_count(self) -> int:
        if 0 <= self.selected_library_index < len(self.library_items):
            return self.library_items[self.selected_library_index].view_count
        return self.snapshot.view_count

    @property
    def pending_delete_title(self) -> str:
        return self.pending_delete_entry.capture_id if self.pending_delete_entry else ""

    @property
    def storage_used_text(self) -> str:
        if not self.storage_usage.available:
            return "--"
        return _format_storage_bytes(self.storage_usage.used_bytes)

    @property
    def storage_available_text(self) -> str:
        if not self.storage_usage.available:
            return "UNAVAILABLE"
        return _format_storage_bytes(self.storage_usage.free_bytes)

    @property
    def storage_used_fraction(self) -> float:
        if not self.storage_usage.available or self.storage_usage.total_bytes <= 0:
            return 0.0
        return min(1.0, self.storage_usage.used_bytes / self.storage_usage.total_bytes)

    @property
    def storage_connected(self) -> bool:
        return self.storage_usage.available

    def set_changed_callback(self, callback: Callable[[], None]) -> None:
        self._on_changed = callback

    def set_catalog_callbacks(
        self,
        refresh: Callable[[], None],
        open_entry: Callable[[CatalogEntry], None],
        delete_entry: Callable[[CatalogEntry], None] | None = None,
    ) -> None:
        self._refresh_catalog = refresh
        self._open_catalog_entry = open_entry
        if delete_entry is not None:
            self._delete_catalog_entry = delete_entry

    def set_storage_refresh_callback(self, refresh: Callable[[], None]) -> None:
        self._refresh_storage = refresh

    def set_camera_recovery_callback(self, recover: Callable[[], None]) -> None:
        self._recover_cameras = recover

    def navigate(self, route: str) -> bool:
        if route not in ALL_ROUTES or self.snapshot.capture_in_progress:
            return False
        self.route = route
        if route == "library":
            self.catalog_status = "loading"
            self.catalog_message = "Refreshing removable USB media"
            self._refresh_catalog()
        elif route == "ready":
            self._refresh_storage()
        self._on_changed()
        return True

    def apply_storage_usage(self, storage_usage: StorageUsage) -> None:
        self.storage_usage = storage_usage
        self._on_changed()

    def request_capture(self) -> bool:
        if not self.can_capture:
            return False
        self.presentation_state.apply(
            {"state": "LOADING", "message": "Starting capture", "phase": "capturing"}
        )
        self.route = "progress"
        self.commands.put("CAPTURE")
        self._on_changed()
        return True

    def request_camera_recovery(self) -> bool:
        if not self.can_recover_cameras:
            return False
        self.camera_recovery_pending = True
        self.camera_recovery_message = "RESTARTING CAMERA USB"
        self._on_changed()
        self._recover_cameras()
        return True

    def apply_camera_recovery_result(self, error: Exception | None) -> None:
        if error is None:
            self.camera_recovery_message = "CAMERA USB RECOVERY STARTED"
        else:
            self.camera_recovery_pending = False
            self.camera_recovery_message = f"RECOVERY FAILED: {error}"
        self._on_changed()

    def open_library_item(self, index: int) -> bool:
        if not 0 <= index < len(self.library_items) or self.snapshot.capture_in_progress:
            return False
        self.selected_library_index = index
        self.catalog_status = "loading"
        self.catalog_message = f"Opening {self.library_items[index].capture_id}"
        self._open_catalog_entry(self.library_items[index])
        self._on_changed()
        return True

    def select_library_item(self, index: int) -> bool:
        if not 0 <= index < len(self.library_items):
            return False
        self.selected_library_index = index
        self._on_changed()
        return True

    def prompt_delete_selected(self) -> bool:
        if (
            not 0 <= self.selected_library_index < len(self.library_items)
            or self.snapshot.capture_in_progress
            or self.catalog_status in {"loading", "deleting"}
        ):
            return False
        self.pending_delete_entry = self.library_items[self.selected_library_index]
        self.delete_confirmation_visible = True
        self._on_changed()
        return True

    def cancel_delete(self) -> None:
        self.delete_confirmation_visible = False
        self.pending_delete_entry = None
        self._on_changed()

    def confirm_delete(self) -> bool:
        entry = self.pending_delete_entry
        if entry is None or not self.delete_confirmation_visible:
            return False
        self.delete_confirmation_visible = False
        self.pending_delete_entry = None
        self.catalog_status = "deleting"
        self.catalog_message = f"Deleting {entry.capture_id}"
        self._delete_catalog_entry(entry)
        self._on_changed()
        return True

    def apply_catalog(
        self,
        catalog: CatalogSnapshot,
        storage_usage: StorageUsage | None = None,
    ) -> None:
        selected_id = (
            self.library_items[self.selected_library_index].capture_id
            if 0 <= self.selected_library_index < len(self.library_items)
            else None
        )
        self.library_items = list(catalog.entries)
        self.catalog_status = catalog.status
        self.catalog_message = catalog.message
        if storage_usage is not None:
            self.storage_usage = storage_usage
        self.selected_library_index = next(
            (
                index
                for index, entry in enumerate(self.library_items)
                if entry.capture_id == selected_id
            ),
            0 if self.library_items else -1,
        )
        self._on_changed()

    def apply_opened_catalog(
        self,
        entry: CatalogEntry,
        frames: list[Image.Image] | None,
        durations: list[int] | None,
        error: Exception | None,
    ) -> None:
        if error is not None or not frames or not durations:
            self.catalog_status = "removed"
            self.catalog_message = "Selected media was removed, corrupt, or unreadable"
            self.route = "library"
            self._on_changed()
            return
        self.review_frames = [_frame_data_url(frame) for frame in frames]
        self.review_durations = list(durations)
        self.review_index = 0
        self.catalog_status = "ready"
        self.catalog_message = entry.capture_id
        self.route = "viewer"
        self._on_changed()

    def apply_deleted_catalog(
        self,
        entry: CatalogEntry,
        catalog: CatalogSnapshot | None,
        error: Exception | None,
        storage_usage: StorageUsage | None = None,
    ) -> None:
        self.delete_confirmation_visible = False
        self.pending_delete_entry = None
        self.route = "library"
        if storage_usage is not None:
            self.storage_usage = storage_usage
        if error is not None or catalog is None:
            self.catalog_status = "removed" if isinstance(error, OSError) else "error"
            self.catalog_message = f"Could not delete {entry.capture_id}: {error}"
            self._on_changed()
            return

        deleted_index = next(
            (
                index
                for index, item in enumerate(self.library_items)
                if item.capture_id == entry.capture_id
            ),
            0,
        )
        self.library_items = list(catalog.entries)
        self.selected_library_index = (
            min(deleted_index, len(self.library_items) - 1) if self.library_items else -1
        )
        self.review_frames = []
        self.review_durations = []
        self.review_index = 0
        self.catalog_status = catalog.status
        self.catalog_message = f"Deleted {entry.capture_id}"
        self._on_changed()

    def advance_review_frame(self) -> int:
        if len(self.review_frames) < 2:
            return 0
        self.review_index = (self.review_index + 1) % len(self.review_frames)
        self._on_changed()
        return self.review_durations[self.review_index]

    def _detach_review(self, path_text: str) -> None:
        # Import lazily to keep one canonical loader and avoid a Qt dependency.
        from .ui import _load_review_frames

        frames, durations = _load_review_frames(Path(path_text), self.display_size)
        self.review_frames = [_frame_data_url(frame) for frame in frames]
        self.review_durations = durations
        self.review_index = 0

    def handle_event(self, event: dict) -> None:
        try:
            presentation = self.presentation_state.apply(event)
            if presentation.image:
                self._detach_review(presentation.image)
            if self.snapshot.screen == "progress":
                self.route = "progress"
            elif self.snapshot.screen == "review":
                self.route = "review"
            elif self.route in RUNTIME_ROUTES:
                self.route = "ready"
            self.last_manifest = event.get("manifest")
            if self.last_manifest is not None:
                self.display_timing_recorded = False
        except Exception as exc:
            LOGGER.error("Qt presentation failed for event %r: %s", event.get("state"), exc)
            self.review_frames = []
            self.review_durations = []
            self.presentation_state = PresentationState()
            self.presentation_state.apply(
                {
                    "state": "ERROR",
                    "message": (
                        "Review unavailable\nThe USB drive containing it was removed.\n"
                        "Reconnect the drive or tap to capture again."
                    ),
                }
            )
            self.route = "ready"
        self._on_changed()

    def record_display_timing(self) -> None:
        manifest = self.last_manifest
        image = self.snapshot.image
        if not manifest or not image or self.display_timing_recorded:
            return
        try:
            rendered_ns = time.monotonic_ns()
            monotonic = manifest["metrics"]["pi_monotonic_ns"]
            monotonic["display_callback_ns"] = rendered_ns
            start = monotonic.get("first_capture_started_ns", rendered_ns)
            manifest["metrics"]["durations_ms"]["capture_event_to_display_callback"] = (
                rendered_ns - start
            ) / 1_000_000
            atomic_json(Path(image).parent / "manifest.json", manifest)
            self.display_timing_recorded = True
        except (KeyError, OSError, TypeError) as exc:
            LOGGER.warning("Could not persist display timing: %s", exc)


def run_qt_ui(
    config: dict,
    trigger: HardwareTrigger,
    storage: UsbStorageResolver,
    *,
    verify_only: bool = False,
) -> None:
    """Run the native Qt Quick UI. PySide6 is intentionally imported only here."""

    from PySide6.QtCore import Property, QObject, Qt, QTimer, QUrl, Signal, Slot
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine

    from .receiver import Receiver

    app = QGuiApplication.instance() or QGuiApplication([])
    if config.get("hide_pointer", True):
        app.setOverrideCursor(Qt.CursorShape.BlankCursor)

    events: queue.Queue = queue.Queue()
    commands: queue.Queue = queue.Queue()
    stop = threading.Event()
    controller = QtUiController(
        commands,
        display_size=(
            int(config.get("display_width", 800)),
            int(config.get("display_height", 480)),
        ),
    )

    repo_root = Path(__file__).resolve().parents[2]
    placeholder = repo_root / "assets" / "ui" / "preview-placeholder.png"
    logo = Path(config.get("startup_logo", repo_root / "assets" / "Logo_800x480.png"))
    first_frame = {"seen": False, "callback": lambda: None}

    class Bridge(QObject):
        changed = Signal()

        def __init__(self) -> None:
            super().__init__()
            controller.set_changed_callback(self.changed.emit)

        @Property(str, notify=changed)
        def route(self) -> str:
            return controller.route

        @Property(str, notify=changed)
        def state(self) -> str:
            return controller.snapshot.state

        @Property(str, notify=changed)
        def message(self) -> str:
            return controller.snapshot.message

        @Property(str, notify=changed)
        def usbStatus(self) -> str:  # noqa: N802 - QML property naming
            return controller.snapshot.usb_status

        @Property(str, notify=changed)
        def capturePhase(self) -> str:  # noqa: N802
            return controller.snapshot.capture_phase

        @Property("QVariantList", notify=changed)
        def cameraStates(self) -> list[str]:  # noqa: N802
            return list(controller.snapshot.camera_states)

        @Property("QVariantList", notify=changed)
        def connectedCameraIds(self) -> list[int]:  # noqa: N802
            return list(controller.snapshot.connected_camera_ids)

        @Property("QVariantList", notify=changed)
        def failedCameraIds(self) -> list[int]:  # noqa: N802
            return list(controller.snapshot.failed_camera_ids)

        @Property(int, notify=changed)
        def viewCount(self) -> int:  # noqa: N802
            return controller.snapshot.view_count

        @Property(int, notify=changed)
        def viewerViewCount(self) -> int:  # noqa: N802
            return controller.viewer_view_count

        @Property(str, notify=changed)
        def imageSource(self) -> str:  # noqa: N802
            return controller.image_source

        @Property("QVariantList", notify=changed)
        def libraryItems(self) -> list[dict]:  # noqa: N802
            return controller.qml_library_items

        @Property(int, notify=changed)
        def selectedLibraryIndex(self) -> int:  # noqa: N802
            return controller.selected_library_index

        @Property(str, notify=changed)
        def catalogStatus(self) -> str:  # noqa: N802
            return controller.catalog_status

        @Property(str, notify=changed)
        def catalogMessage(self) -> str:  # noqa: N802
            return controller.catalog_message

        @Property(str, notify=changed)
        def storageUsedText(self) -> str:  # noqa: N802
            return controller.storage_used_text

        @Property(str, notify=changed)
        def storageAvailableText(self) -> str:  # noqa: N802
            return controller.storage_available_text

        @Property(float, notify=changed)
        def storageUsedFraction(self) -> float:  # noqa: N802
            return controller.storage_used_fraction

        @Property(bool, notify=changed)
        def storageConnected(self) -> bool:  # noqa: N802
            return controller.storage_connected

        @Property(bool, notify=changed)
        def deleteConfirmationVisible(self) -> bool:  # noqa: N802
            return controller.delete_confirmation_visible

        @Property(str, notify=changed)
        def pendingDeleteTitle(self) -> str:  # noqa: N802
            return controller.pending_delete_title

        @Property(str, constant=True)
        def capturePlaceholder(self) -> str:  # noqa: N802
            return QUrl.fromLocalFile(str(placeholder)).toString()

        @Property(str, constant=True)
        def startupLogo(self) -> str:  # noqa: N802
            return QUrl.fromLocalFile(str(logo)).toString()

        @Property(bool, constant=True)
        def fullscreen(self) -> bool:
            return bool(config.get("fullscreen", True))

        @Property(bool, notify=changed)
        def canCapture(self) -> bool:  # noqa: N802
            return controller.can_capture

        @Property(bool, notify=changed)
        def canRecoverCameras(self) -> bool:  # noqa: N802
            return controller.can_recover_cameras

        @Property(bool, notify=changed)
        def cameraRecoveryPending(self) -> bool:  # noqa: N802
            return controller.camera_recovery_pending

        @Property(str, notify=changed)
        def cameraRecoveryMessage(self) -> str:  # noqa: N802
            return controller.camera_recovery_message

        @Slot(result=bool)
        def capture(self) -> bool:
            return controller.request_capture()

        @Slot(result=bool)
        def recoverCameras(self) -> bool:  # noqa: N802
            return controller.request_camera_recovery()

        @Slot(str, result=bool)
        def navigate(self, route: str) -> bool:
            return controller.navigate(route)

        @Slot(int, result=bool)
        def openLibraryItem(self, index: int) -> bool:  # noqa: N802
            return controller.open_library_item(index)

        @Slot(int, result=bool)
        def selectLibraryItem(self, index: int) -> bool:  # noqa: N802
            return controller.select_library_item(index)

        @Slot(result=bool)
        def promptDeleteSelected(self) -> bool:  # noqa: N802
            return controller.prompt_delete_selected()

        @Slot()
        def cancelDelete(self) -> None:  # noqa: N802
            controller.cancel_delete()

        @Slot(result=bool)
        def confirmDelete(self) -> bool:  # noqa: N802
            return controller.confirm_delete()

        @Slot()
        def framePresented(self) -> None:  # noqa: N802
            if not first_frame["seen"]:
                first_frame["seen"] = True
                QTimer.singleShot(0, first_frame["callback"])
                return
            controller.record_display_timing()

    engine = QQmlApplicationEngine()
    bridge = Bridge()
    bridge.setParent(engine)
    engine.rootContext().setContextProperty("bridge", bridge)
    qml_path = Path(__file__).with_name("qml") / "Main.qml"
    engine.addImportPath(str(qml_path.parent))
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        raise RuntimeError(f"Qt Quick failed to load {qml_path}")

    if verify_only:
        QTimer.singleShot(0, app.quit)
        app.exec()
        return

    receiver = Receiver(config, events, commands, stop, trigger, storage)
    catalog_results = _AsyncResultQueue()
    storage_results = _AsyncResultQueue()
    catalog_open_results = _AsyncResultQueue()
    catalog_delete_results = _AsyncResultQueue()
    camera_recovery_results = _AsyncResultQueue()
    catalog_scan_running = threading.Event()
    storage_scan_running = threading.Event()
    catalog_open_running = threading.Event()
    catalog_delete_running = threading.Event()
    camera_recovery_running = threading.Event()

    def refresh_catalog() -> None:
        if catalog_scan_running.is_set():
            return
        catalog_scan_running.set()

        def scan() -> None:
            try:
                try:
                    root = storage.resolve()
                except StorageUnavailable:
                    root = None
                catalog_results.put(scan_capture_catalog(root), read_storage_usage(root))
            finally:
                catalog_scan_running.clear()

        threading.Thread(target=scan, name="usb-media-catalog", daemon=True).start()

    def refresh_storage_usage() -> None:
        if storage_scan_running.is_set():
            return
        storage_scan_running.set()

        def scan() -> None:
            try:
                try:
                    root = storage.resolve()
                except StorageUnavailable:
                    root = None
                storage_results.put(read_storage_usage(root))
            finally:
                storage_scan_running.clear()

        threading.Thread(target=scan, name="usb-storage-usage", daemon=True).start()

    def open_catalog_entry(entry: CatalogEntry) -> None:
        if catalog_open_running.is_set():
            return
        catalog_open_running.set()

        def decode() -> None:
            try:
                frames, durations = load_catalog_animation(entry, controller.display_size)
                catalog_open_results.put(entry, frames, durations, None)
            except Exception as exc:
                catalog_open_results.put(entry, None, None, exc)
            finally:
                catalog_open_running.clear()

        threading.Thread(target=decode, name="usb-media-open", daemon=True).start()

    def remove_catalog_entry(entry: CatalogEntry) -> None:
        if catalog_delete_running.is_set():
            return
        catalog_delete_running.set()
        root = storage.active_root

        def remove() -> None:
            try:
                delete_catalog_entry(root, entry)
                catalog_delete_results.put(
                    entry,
                    scan_capture_catalog(root),
                    None,
                    read_storage_usage(root),
                )
            except Exception as exc:
                catalog_delete_results.put(entry, None, exc, read_storage_usage(root))
            finally:
                catalog_delete_running.clear()

        threading.Thread(target=remove, name="usb-media-delete", daemon=True).start()

    controller.set_catalog_callbacks(refresh_catalog, open_catalog_entry, remove_catalog_entry)
    controller.set_storage_refresh_callback(refresh_storage_usage)

    def recover_cameras() -> None:
        if camera_recovery_running.is_set():
            return
        camera_recovery_running.set()
        command = config.get("camera_recovery_command", [])

        def request_recovery() -> None:
            error: Exception | None = None
            try:
                if (
                    not isinstance(command, list)
                    or not command
                    or not all(isinstance(part, str) and part for part in command)
                ):
                    raise RuntimeError("camera recovery is not installed")
                subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            except Exception as exc:
                error = exc
            finally:
                camera_recovery_results.put(error)
                camera_recovery_running.clear()

        threading.Thread(
            target=request_recovery,
            name="camera-usb-recovery",
            daemon=True,
        ).start()

    controller.set_camera_recovery_callback(recover_cameras)

    poll_timer = QTimer()
    poll_timer.setInterval(50)
    automatic_quit_scheduled = False

    def poll_events() -> None:
        nonlocal automatic_quit_scheduled
        while True:
            try:
                event = events.get_nowait()
            except queue.Empty:
                break
            controller.handle_event(event)
        catalog_results.drain(controller.apply_catalog)
        storage_results.drain(controller.apply_storage_usage)
        if (
            int(config.get("trigger_count", 0)) > 0
            and receiver.automatic_run_completed.is_set()
            and not automatic_quit_scheduled
        ):
            automatic_quit_scheduled = True
            QTimer.singleShot(1000, app.quit)
        catalog_open_results.drain(controller.apply_opened_catalog)
        catalog_delete_results.drain(controller.apply_deleted_catalog)
        camera_recovery_results.drain(controller.apply_camera_recovery_result)

    poll_timer.timeout.connect(poll_events)

    frame_timer = QTimer()
    frame_timer.setSingleShot(True)

    def advance_frame() -> None:
        delay = controller.advance_review_frame()
        if delay:
            frame_timer.start(delay)

    frame_timer.timeout.connect(advance_frame)

    def restart_animation() -> None:
        frame_timer.stop()
        if len(controller.review_frames) > 1:
            frame_timer.start(controller.review_durations[controller.review_index])

    bridge.changed.connect(restart_animation)

    def start_runtime() -> None:
        receiver.start()
        poll_timer.start()
        refresh_storage_usage()

    first_frame["callback"] = start_runtime

    def shutdown() -> None:
        stop.set()
        if receiver.is_alive():
            receiver.join(timeout=2)

    app.aboutToQuit.connect(shutdown)
    app.exec()


def verify_qml(config: dict | None = None) -> None:
    """Load the complete route tree without a receiver or hardware side effects."""

    run_qt_ui(
        config or {"fullscreen": False, "hide_pointer": False}, object(), object(), verify_only=True
    )
