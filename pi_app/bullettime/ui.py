"""Headless and touchscreen presentation loops for the camera receiver."""

from __future__ import annotations

import json
import queue
import threading
import time
from pathlib import Path

from PIL import Image, ImageOps, ImageTk

from .gpio_trigger import HardwareTrigger
from .receiver import Receiver
from .storage import UsbStorageResolver, atomic_json


def run_headless(config: dict, trigger: HardwareTrigger, storage: UsbStorageResolver) -> None:
    events, commands, stop = queue.Queue(), queue.Queue(), threading.Event()
    Receiver(config, events, commands, stop, trigger, storage).start()
    try:
        while True:
            print(json.dumps(events.get(), sort_keys=True), flush=True)
    except KeyboardInterrupt:
        stop.set()


def run_ui(config: dict, trigger: HardwareTrigger, storage: UsbStorageResolver) -> None:
    import tkinter as tk

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
    ui_state = {"value": "STARTING"}

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

    def poll() -> None:
        try:
            while True:
                event = events.get_nowait()
                state = event["state"]
                ui_state["value"] = state
                if state == "REVIEW":
                    with Image.open(event["image"]) as source:
                        display_image = source.copy()
                    display_image.thumbnail(
                        (
                            config.get("display_width", 800),
                            config.get("display_height", 480),
                        )
                    )
                    image_ref["value"] = ImageTk.PhotoImage(display_image)
                    label.configure(image=image_ref["value"], text="")

                    def rendered(path=Path(event["image"]), manifest=event["manifest"]):
                        rendered_ns = time.monotonic_ns()
                        manifest["metrics"]["pi_monotonic_ns"]["display_callback_ns"] = rendered_ns
                        start = manifest["metrics"]["pi_monotonic_ns"].get(
                            "capture_event_received_ns", rendered_ns
                        )
                        manifest["metrics"]["durations_ms"]["capture_event_to_display_callback"] = (
                            rendered_ns - start
                        ) / 1_000_000
                        atomic_json(path.parent / "manifest.json", manifest)

                    root.after_idle(rendered)
                else:
                    color = (
                        "#ffb000"
                        if state == "LOADING"
                        else ("#ff5050" if state == "ERROR" else "white")
                    )
                    label.configure(image="", text=event.get("message", state), fg=color)
        except queue.Empty:
            pass
        root.after(50, poll)

    root.protocol("WM_DELETE_WINDOW", lambda: (stop.set(), root.destroy()))

    def request_capture(_event) -> None:
        if ui_state["value"] in {"READY", "REVIEW", "REVIEW_WITH_ERROR", "ERROR"}:
            ui_state["value"] = "LOADING"
            commands.put("CAPTURE")

    label.bind("<Button-1>", request_capture)
    poll()
    root.mainloop()
