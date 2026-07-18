"""Headless and touchscreen presentation loops for the camera receiver."""

from __future__ import annotations

import json
import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, ImageSequence, ImageTk

from .gpio_trigger import HardwareTrigger
from .storage import UsbStorageResolver, atomic_json


@dataclass(frozen=True)
class Presentation:
    state: str
    image: str | None
    text: str
    color: str


class PresentationState:
    """Pure UI reducer used by both Tk and deterministic tests."""

    def __init__(self) -> None:
        self.state = "STARTING"
        self.review_image: str | None = None
        self.capture_in_progress = False

    def apply(self, event: dict) -> Presentation:
        state = str(event["state"])
        message = str(event.get("message", state))
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
            presentation = Presentation(state, self.review_image, text, color)
        elif state == "READY" and self.review_image:
            self.capture_in_progress = False
            presentation = Presentation(state, self.review_image, "", "white")
        elif state == "ERROR":
            self.capture_in_progress = False
            image = self.review_image if self.review_image and not was_capturing else None
            presentation = Presentation(state, image, message, "#ff5050")
        else:
            presentation = Presentation(state, None, message, "white")
        self.state = state
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
    label = tk.Label(
        root,
        text="",
        fg="white",
        bg="black",
        font=("Sans", 28),
        compound="center",
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
            display_size = (
                int(config.get("display_width", 800)),
                int(config.get("display_height", 480)),
            )
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
        frames = []
        durations = []
        with Image.open(path_text) as source:
            for source_frame in ImageSequence.Iterator(source):
                frame = source_frame.convert("RGB")
                frame.thumbnail(
                    (
                        config.get("display_width", 800),
                        config.get("display_height", 480),
                    )
                )
                frames.append(ImageTk.PhotoImage(frame.copy()))
                durations.append(max(20, int(source_frame.info.get("duration", 100))))
        if not frames:
            raise RuntimeError(f"review media contains no frames: {path_text}")
        animation.update(frames=frames, durations=durations, index=0, path=path_text)
        image_ref["value"] = frames[0]
        if len(frames) > 1:
            animation["after_id"] = root.after(durations[0], advance_animation)

    def poll() -> None:
        try:
            while True:
                event = events.get_nowait()
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
                        rendered_ns = time.monotonic_ns()
                        manifest["metrics"]["pi_monotonic_ns"]["display_callback_ns"] = rendered_ns
                        start = manifest["metrics"]["pi_monotonic_ns"].get(
                            "first_capture_started_ns", rendered_ns
                        )
                        manifest["metrics"]["durations_ms"]["capture_event_to_display_callback"] = (
                            rendered_ns - start
                        ) / 1_000_000
                        atomic_json(path.parent / "manifest.json", manifest)

                    root.after_idle(rendered)
                else:
                    cancel_animation()
                    image_ref["value"] = None
                    label.configure(image="", text=presentation.text, fg=presentation.color)
        except queue.Empty:
            pass
        root.after(50, poll)

    root.protocol("WM_DELETE_WINDOW", lambda: (stop.set(), root.destroy()))

    def request_capture(_event) -> None:
        if presentation_state.state in {"READY", "REVIEW", "REVIEW_WITH_ERROR", "ERROR"}:
            presentation_state.apply({"state": "LOADING", "message": "Starting capture..."})
            commands.put("CAPTURE")

    label.bind("<Button-1>", request_capture)
    poll()
    root.mainloop()
