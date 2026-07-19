"""Headless and touchscreen presentation loops for the camera receiver."""

from __future__ import annotations

import json
import queue
import threading
from collections.abc import Callable
from pathlib import Path

from PIL import Image, ImageSequence

from .gpio_trigger import HardwareTrigger
from .storage import UsbStorageResolver
from .ui_model import PresentationState as PresentationState
from .ui_model import compact_ui_message


def _compact_ui_message(message: str) -> str:
    """Compatibility alias retained for existing callers and tests."""

    return compact_ui_message(message)


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
    """Drain queued UI events without allowing one bad event to kill polling."""
    while True:
        try:
            event = events.get_nowait()
        except queue.Empty:
            return
        try:
            handle(event)
        except Exception as exc:
            handle_failure(event, exc)


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
    from .qt_ui import run_qt_ui

    run_qt_ui(config, trigger, storage)
