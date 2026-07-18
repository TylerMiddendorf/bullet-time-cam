"""Headless and touchscreen presentation loops for the camera receiver."""

from __future__ import annotations

import json
import logging
import queue
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, ImageSequence, ImageTk

from .gpio_trigger import HardwareTrigger
from .storage import UsbStorageResolver, atomic_json

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Presentation:
    state: str
    image: str | None
    text: str
    color: str


def _compact_ui_message(message: str) -> str:
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
        return "USB storage could not be mounted\nRepair or replace the USB drive,\nthen tap to try again."
    if "input/output error" in lowered or "errno 5" in lowered:
        return "USB storage was removed or failed\nReconnect or replace the USB drive,\nthen tap to try again."
    if "no writable usb storage" in lowered:
        return "USB storage unavailable\nInsert a writable USB drive,\nthen tap to try again."
    return message


def _load_review_frames(
    path: Path, display_size: tuple[int, int]
) -> tuple[list[Image.Image], list[int]]:
    """Load detached PIL frames so removable media can disappear after this call."""
    frames: list[Image.Image] = []
    durations: list[int] = []
    with Image.open(path) as source:
        for source_frame in ImageSequence.Iterator(source):
            frame = source_frame.convert("RGB")
            frame.thumbnail(display_size)
            frames.append(frame.copy())
            durations.append(max(20, int(source_frame.info.get("duration", 100))))
    if not frames:
        raise RuntimeError(f"review media contains no frames: {path}")
    return frames, durations


def _drain_events(
    events: queue.Queue,
    handle: Callable[[dict], None],
    handle_failure: Callable[[dict, Exception], None],
) -> None:
    """Drain queued UI events without allowing one bad event to kill Tk polling."""
    while True:
        try:
            event = events.get_nowait()
        except queue.Empty:
            return
        try:
            handle(event)
        except Exception as exc:
            handle_failure(event, exc)


class PresentationState:
    """Pure UI reducer used by both Tk and deterministic tests."""

    def __init__(self) -> None:
        self.state = "STARTING"
        self.review_image: str | None = None
        self.review_text = ""
        self.review_color = "white"
        self.capture_in_progress = False

    def apply(self, event: dict) -> Presentation:
        state = str(event["state"])
        message = _compact_ui_message(str(event.get("message", state)))
        was_capturing = self.capture_in_progress
        if state == "LOADING":
            self.capture_in_progress = True
            presentation = Presentation(state, None, message, "#ffb000")
        elif state in {"REVIEW", "REVIEW_WITH_ERROR"}:
            self.capture_in_progress = False
            if event.get("image"):
                self.review_image = str(event["image"])
            text = message if state == "REVIEW_WITH_ERROR" else ""
            color = "#ff5050" if state == "REVIEW_WITH_ERROR" else "white"
            self.review_text = text
            self.review_color = color
            presentation = Presentation(state, self.review_image, text, color)
        elif state == "READY" and self.review_image:
            self.capture_in_progress = False
            presentation = Presentation(state, self.review_image, "", "white")
        elif state == "ERROR":
            self.capture_in_progress = False
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
        return presentation


def run_headless(config: dict, trigger: HardwareTrigger, storage: UsbStorageResolver) -> None:
    from .receiver import Receiver

    events, commands, stop = queue.Queue(), queue.Queue(), threading.Event()
    receiver = Receiver(config, events, commands, stop, trigger, storage)
    receiver.start()
    bounded_automatic_run = int(config.get("trigger_count", 0)) > 0
    try:
        while True:
            try:
                event = events.get(timeout=0.2)
            except queue.Empty:
                if bounded_automatic_run and receiver.automatic_run_completed.is_set():
                    break
                continue
            print(json.dumps(event, sort_keys=True), flush=True)
            if (
                bounded_automatic_run
                and event.get("manifest") is not None
                and receiver.automatic_run_completed.wait(timeout=0.2)
            ):
                break
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        receiver.join(timeout=2)


def run_ui(config: dict, trigger: HardwareTrigger, storage: UsbStorageResolver) -> None:
    import tkinter as tk

    from .receiver import Receiver

    root = tk.Tk()
    root.configure(background="black")
    if config.get("hide_pointer", True):
        root.configure(cursor="none")
    if config.get("fullscreen", True):
        root.attributes("-fullscreen", True)
    display_size = (
        int(config.get("display_width", 800)),
        int(config.get("display_height", 480)),
    )
    label = tk.Label(
        root,
        text="",
        fg="white",
        bg="black",
        font=("Sans", 24),
        compound="center",
        justify="center",
        wraplength=max(200, display_size[0] - 80),
        borderwidth=0,
        highlightthickness=0,
        padx=0,
        pady=0,
    )
    label.pack(fill="both", expand=True)
    image_ref = {"value": None}
    animation = {"frames": [], "durations": [], "index": 0, "after_id": None, "path": None}
    presentation_state = PresentationState()

    startup_logo = config.get("startup_logo")
    if startup_logo:
        with Image.open(startup_logo) as source:
            logo = ImageOps.contain(source.convert("RGB"), display_size, Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", display_size, "black")
            canvas.paste(
                logo,
                (
                    (display_size[0] - logo.width) // 2,
                    (display_size[1] - logo.height) // 2,
                ),
            )
            image_ref["value"] = ImageTk.PhotoImage(canvas)
        label.configure(image=image_ref["value"])

    # Map a complete logo frame before receiver discovery can publish status.
    root.update_idletasks()
    root.update()

    events, commands, stop = queue.Queue(), queue.Queue(), threading.Event()
    Receiver(config, events, commands, stop, trigger, storage).start()

    def cancel_animation() -> None:
        if animation["after_id"] is not None:
            root.after_cancel(animation["after_id"])
        animation.update(frames=[], durations=[], index=0, after_id=None, path=None)

    def advance_animation() -> None:
        frames = animation["frames"]
        if len(frames) < 2:
            animation["after_id"] = None
            return
        animation["index"] = (animation["index"] + 1) % len(frames)
        image_ref["value"] = frames[animation["index"]]
        label.configure(image=image_ref["value"])
        delay = animation["durations"][animation["index"]]
        animation["after_id"] = root.after(delay, advance_animation)

    def show_media(path_text: str) -> None:
        if animation["path"] == path_text:
            return
        cancel_animation()
        pil_frames, durations = _load_review_frames(Path(path_text), display_size)
        frames = [ImageTk.PhotoImage(frame) for frame in pil_frames]
        animation.update(frames=frames, durations=durations, index=0, path=path_text)
        image_ref["value"] = frames[0]
        if len(frames) > 1:
            animation["after_id"] = root.after(durations[0], advance_animation)

    def present(event: dict) -> None:
        presentation = presentation_state.apply(event)
        if presentation.image:
            show_media(presentation.image)
            label.configure(
                image=image_ref["value"],
                text=presentation.text,
                fg=presentation.color,
            )

            render_path = Path(presentation.image)
            render_manifest = event.get("manifest")

            def rendered(path=render_path, manifest=render_manifest):
                if manifest is None:
                    return
                try:
                    rendered_ns = time.monotonic_ns()
                    manifest["metrics"]["pi_monotonic_ns"]["display_callback_ns"] = rendered_ns
                    start = manifest["metrics"]["pi_monotonic_ns"].get(
                        "first_capture_started_ns", rendered_ns
                    )
                    manifest["metrics"]["durations_ms"]["capture_event_to_display_callback"] = (
                        rendered_ns - start
                    ) / 1_000_000
                    atomic_json(path.parent / "manifest.json", manifest)
                except OSError as exc:
                    # Display metrics are best-effort when removable media disappears.
                    LOGGER.warning("Could not persist display timing: %s", exc)
                    return

            root.after_idle(rendered)
        else:
            cancel_animation()
            image_ref["value"] = None
            label.configure(image="", text=presentation.text, fg=presentation.color)

    def presentation_failed(event: dict, exc: Exception) -> None:
        LOGGER.error("UI presentation failed for event %r: %s", event.get("state"), exc)
        cancel_animation()
        image_ref["value"] = None
        presentation_state.review_image = None
        presentation_state.review_text = ""
        presentation_state.state = "ERROR"
        label.configure(
            image="",
            text=(
                "Review unavailable\nThe USB drive containing it was removed.\n"
                "Reconnect the drive or tap to capture again."
            ),
            fg="#ff5050",
        )

    def poll() -> None:
        _drain_events(events, present, presentation_failed)
        root.after(50, poll)

    root.protocol("WM_DELETE_WINDOW", lambda: (stop.set(), root.destroy()))

    def request_capture(_event) -> None:
        if presentation_state.state in {"READY", "REVIEW", "REVIEW_WITH_ERROR", "ERROR"}:
            presentation_state.apply({"state": "LOADING", "message": "Starting capture..."})
            commands.put("CAPTURE")

    label.bind("<Button-1>", request_capture)
    poll()
    root.mainloop()
