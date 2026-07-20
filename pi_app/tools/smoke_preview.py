"""Receive bounded in-memory preview frames from every registered camera node."""

from __future__ import annotations

import argparse
import json
import logging
import queue
import threading
import time
import zlib
from pathlib import Path

from pi_app.bullettime.receiver import Receiver
from pi_app.bullettime.storage import StorageUnavailable


class _NoCaptureTrigger:
    pulse_seconds = 0.1

    def pulse(self) -> None:
        raise RuntimeError("preview smoke must never trigger a still capture")


class _NoStorage:
    active_root = None

    def resolve(self) -> Path:
        raise StorageUnavailable("Preview smoke intentionally does not access removable storage")

    def manifest_details(self) -> dict:
        raise RuntimeError("preview smoke must never build a capture manifest")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="pi_app/config.json")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--frames-per-camera", type=int, default=2)
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()
    if args.timeout <= 0 or args.frames_per_camera <= 0:
        raise SystemExit("timeout and frames-per-camera must be positive")
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    events: queue.Queue = queue.Queue()
    commands: queue.Queue = queue.Queue()
    stop = threading.Event()
    receiver = Receiver(config, events, commands, stop, _NoCaptureTrigger(), _NoStorage())
    receiver.start()
    commands.put("PREVIEW_START")
    deadline = time.monotonic() + args.timeout
    frames: dict[int, list[dict]] = {camera_id: [] for camera_id in range(1, 5)}
    try:
        while time.monotonic() < deadline and any(
            len(camera_frames) < args.frames_per_camera for camera_frames in frames.values()
        ):
            try:
                event = events.get(timeout=0.25)
            except queue.Empty:
                continue
            if event.get("type") != "preview_frame":
                continue
            camera_id = int(event["camera_id"])
            payload = event["jpeg"]
            frames[camera_id].append(
                {
                    "node_uid": event["node_uid"],
                    "preview_seq": event["preview_seq"],
                    "jpeg_bytes": len(payload),
                    "jpeg_crc32": f"{zlib.crc32(payload) & 0xFFFFFFFF:08x}",
                    "width": event["width"],
                    "height": event["height"],
                }
            )
    finally:
        commands.put("PREVIEW_STOP")
        stop.set()
        receiver.join(timeout=3)

    report = {
        "status": "passed"
        if all(len(camera_frames) >= args.frames_per_camera for camera_frames in frames.values())
        else "failed",
        "storage_access": "disabled",
        "frames": {str(camera_id): camera_frames for camera_id, camera_frames in frames.items()},
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
