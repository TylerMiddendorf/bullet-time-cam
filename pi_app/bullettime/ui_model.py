"""Platform-neutral state for the touchscreen presentation layer."""

from __future__ import annotations

from dataclasses import dataclass

CAMERA_COUNT = 4
CAMERA_STATES = frozenset(
    {"disconnected", "ready", "waiting", "capturing", "transferring", "complete", "error"}
)


@dataclass(frozen=True)
class Presentation:
    """Compatibility view of one receiver event for simple presenters."""

    state: str
    image: str | None
    text: str
    color: str


@dataclass(frozen=True)
class UiSnapshot:
    """Complete immutable state consumed by the Qt bridge."""

    state: str
    screen: str
    image: str | None
    message: str
    color: str
    capture_in_progress: bool
    capture_phase: str
    connected_camera_ids: tuple[int, ...]
    camera_states: tuple[str, ...]
    usb_status: str
    view_count: int
    failed_camera_ids: tuple[int, ...]


def compact_ui_message(message: str) -> str:
    """Keep common storage failures actionable and readable on an 800x480 display."""

    lowered = message.lower()
    if "no space left" in lowered or "errno 28" in lowered:
        return (
            "USB storage is full\nFree space or insert another USB drive,\nthen tap to try again."
        )
    if "read-only" in lowered or "errno 30" in lowered:
        return "USB storage is read-only\nInsert a writable USB drive,\nthen tap to try again."
    if "automatic mount errors" in lowered or any(
        detail in lowered
        for detail in ("wrong fs type", "bad superblock", "unknown filesystem", "mount failed")
    ):
        return (
            "USB storage could not be mounted\nRepair or replace the USB drive,\n"
            "then tap to try again."
        )
    if "input/output error" in lowered or "errno 5" in lowered:
        return (
            "USB storage was removed or failed\nReconnect or replace the USB drive,\n"
            "then tap to try again."
        )
    if "no writable usb storage" in lowered:
        return "USB storage unavailable\nInsert a writable USB drive,\nthen tap to try again."
    return message


def _capture_phase(event: dict, message: str, current: str) -> str:
    phase = str(event.get("phase", "")).lower()
    if phase in {"capturing", "transferring", "building"}:
        return phase
    lowered = message.lower()
    if "build" in lowered or "committ" in lowered or "animation" in lowered:
        return "building"
    if "transfer" in lowered or "finishing" in lowered:
        return "transferring"
    if current in {"capturing", "transferring", "building"}:
        return current
    return "capturing"


def _event_camera_ids(event: dict, key: str) -> tuple[int, ...]:
    values = event.get(key, ())
    if not isinstance(values, (list, tuple, set, frozenset)):
        return ()
    return tuple(sorted({int(value) for value in values if 1 <= int(value) <= CAMERA_COUNT}))


class PresentationState:
    """Pure reducer shared by Qt, headless-compatible tests, and migration shims."""

    def __init__(self) -> None:
        self.state = "STARTING"
        self.review_image: str | None = None
        self.review_text = ""
        self.review_color = "white"
        self.capture_in_progress = False
        self.capture_phase = "idle"
        self.connected_camera_ids: tuple[int, ...] = ()
        self.camera_states = ["disconnected"] * CAMERA_COUNT
        self.usb_status = "checking"
        self.view_count = 0
        self.failed_camera_ids: tuple[int, ...] = ()
        starting = Presentation("STARTING", None, "Starting", "white")
        self.snapshot = self._snapshot(starting)

    def _snapshot(self, presentation: Presentation) -> UiSnapshot:
        if self.capture_in_progress:
            screen = "progress"
        elif presentation.image:
            screen = "review"
        elif presentation.state == "ERROR":
            screen = "error"
        else:
            screen = "ready"
        return UiSnapshot(
            state=presentation.state,
            screen=screen,
            image=presentation.image,
            message=presentation.text,
            color=presentation.color,
            capture_in_progress=self.capture_in_progress,
            capture_phase=self.capture_phase,
            connected_camera_ids=self.connected_camera_ids,
            camera_states=tuple(self.camera_states),
            usb_status=self.usb_status,
            view_count=self.view_count,
            failed_camera_ids=self.failed_camera_ids,
        )

    def _apply_connected_cameras(self, event: dict) -> None:
        connectivity_provided = "connected_camera_ids" in event or "connected_camera_count" in event
        if "connected_camera_ids" in event:
            self.connected_camera_ids = _event_camera_ids(event, "connected_camera_ids")
        elif "connected_camera_count" in event:
            count = int(event.get("connected_camera_count", 0))
            if count == 0:
                self.connected_camera_ids = ()
            elif count == CAMERA_COUNT:
                self.connected_camera_ids = tuple(range(1, CAMERA_COUNT + 1))

        explicit_states = event.get("camera_states")
        if isinstance(explicit_states, (list, tuple)) and len(explicit_states) == CAMERA_COUNT:
            normalized = [str(value).lower() for value in explicit_states]
            if all(value in CAMERA_STATES for value in normalized):
                self.camera_states = normalized
                return

        connected_set = set(self.connected_camera_ids)
        for index in range(CAMERA_COUNT):
            if not self.capture_in_progress:
                self.camera_states[index] = (
                    "ready" if index + 1 in connected_set else "disconnected"
                )
            elif connectivity_provided and index + 1 not in connected_set:
                self.camera_states[index] = "disconnected"

    def _apply_progress(self, event: dict, message: str, was_capturing: bool) -> None:
        if not was_capturing:
            connected_set = set(self.connected_camera_ids)
            self.camera_states = [
                "waiting" if camera_id in connected_set else "disconnected"
                for camera_id in range(1, CAMERA_COUNT + 1)
            ]
            self.failed_camera_ids = ()
            self.view_count = 0
        self.capture_phase = _capture_phase(event, message, self.capture_phase)
        camera_id = int(event.get("camera_id", 0) or 0)
        camera_status = str(event.get("camera_status", "")).lower()
        if 1 <= camera_id <= CAMERA_COUNT and camera_status in CAMERA_STATES:
            self.camera_states[camera_id - 1] = camera_status

        completed = {
            index + 1 for index, value in enumerate(self.camera_states) if value == "complete"
        }
        failed = set(self.failed_camera_ids)
        completed.update(_event_camera_ids(event, "completed_camera_ids"))
        failed.update(_event_camera_ids(event, "failed_camera_ids"))
        if 1 <= camera_id <= CAMERA_COUNT:
            if camera_status == "complete":
                completed.add(camera_id)
                failed.discard(camera_id)
            elif camera_status == "error":
                failed.add(camera_id)
                completed.discard(camera_id)
        completed.difference_update(failed)
        for complete_id in completed:
            self.camera_states[complete_id - 1] = "complete"
        for failed_id in failed:
            self.camera_states[failed_id - 1] = "error"
        self.failed_camera_ids = tuple(sorted(failed))
        self.view_count = len(completed)

    def _apply_manifest(self, event: dict) -> None:
        manifest = event.get("manifest")
        if not isinstance(manifest, dict):
            return
        cameras = manifest.get("cameras", [])
        completed: list[int] = []
        failed: list[int] = []
        for camera in cameras if isinstance(cameras, list) else []:
            if not isinstance(camera, dict):
                continue
            camera_id = int(camera.get("logical_camera_id", 0) or 0)
            if not 1 <= camera_id <= CAMERA_COUNT:
                continue
            if camera.get("status") == "complete":
                completed.append(camera_id)
                self.camera_states[camera_id - 1] = "complete"
            else:
                failed.append(camera_id)
                self.camera_states[camera_id - 1] = "error"
        self.view_count = len(completed)
        self.failed_camera_ids = tuple(sorted(failed))

    def apply(self, event: dict) -> Presentation:
        state = str(event["state"])
        message = compact_ui_message(str(event.get("message", state)))
        was_capturing = self.capture_in_progress
        # Connectivity is orthogonal to presentation state. In particular, an
        # idle storage ERROR must not erase or hide the still-connected nodes.
        self._apply_connected_cameras(event)
        if state == "LOADING":
            self.capture_in_progress = True
            self._apply_progress(event, message, was_capturing)
            presentation = Presentation(state, None, message, "#ffb000")
        elif state in {"REVIEW", "REVIEW_WITH_ERROR"}:
            self.capture_in_progress = False
            self.capture_phase = "complete"
            if event.get("image"):
                self.review_image = str(event["image"])
            text = message if state == "REVIEW_WITH_ERROR" else ""
            color = "#ff5050" if state == "REVIEW_WITH_ERROR" else "white"
            self.review_text = text
            self.review_color = color
            self.usb_status = "saved"
            self._apply_manifest(event)
            presentation = Presentation(state, self.review_image, text, color)
        elif state == "READY":
            self.capture_in_progress = False
            self.capture_phase = "idle"
            self.usb_status = "ready"
            if self.review_image:
                presentation = Presentation(state, self.review_image, "", "white")
            else:
                presentation = Presentation(state, None, message, "white")
        elif state == "ERROR":
            self.capture_in_progress = False
            self.capture_phase = "idle"
            if "usb storage" in message.lower():
                self.usb_status = "error"
            if self.review_image and self.review_text and not was_capturing:
                presentation = Presentation(
                    "REVIEW_WITH_ERROR",
                    self.review_image,
                    self.review_text,
                    self.review_color,
                )
            else:
                image = self.review_image if self.review_image and not was_capturing else None
                presentation = Presentation(state, image, message, "#ff5050")
        else:
            presentation = Presentation(state, None, message, "white")
        self.state = presentation.state
        self.snapshot = self._snapshot(presentation)
        return presentation
