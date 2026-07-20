"""Command-line entry point for the Bullet-Time Raspberry Pi application."""

from __future__ import annotations

import argparse
import json
import signal
from pathlib import Path

from .gpio_trigger import HardwareTrigger
from .storage import UsbStorageResolver


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="pi_app/config.json")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--trigger-once",
        action="store_true",
        help="issue one GPIO hardware-trigger pulse after connecting",
    )
    parser.add_argument(
        "--trigger-count",
        type=int,
        default=0,
        help="issue N sequential GPIO hardware-trigger pulses",
    )
    parser.add_argument(
        "--diagnostic-usb-trigger",
        action="store_true",
        help="use explicit USB CAPTURE_REQUEST test scaffolding instead of GPIO pulses",
    )
    parser.add_argument(
        "--corrupt-next-payload",
        action="store_true",
        help="arm test-only corruption of the next requested USB image",
    )
    parser.add_argument(
        "--truncate-camera-id",
        type=int,
        choices=range(1, 5),
        default=0,
        help="test-only: interrupt the selected camera after IMAGE transfer begins",
    )
    parser.add_argument(
        "--allow-incomplete-node-set",
        action="store_true",
        help="test-only: allow bounded automatic capture with one or more nodes missing",
    )
    parser.add_argument(
        "--initial-route",
        choices=("ready", "capture"),
        default=None,
        help="bounded UI validation: open directly on the selected route",
    )
    parser.add_argument(
        "--quit-after-seconds",
        type=float,
        default=0,
        help="bounded UI validation: exit automatically after this many seconds",
    )
    parser.add_argument(
        "--capture-after-seconds",
        type=float,
        default=0,
        help="bounded UI validation: invoke Capture after preview runs for this interval",
    )
    return parser.parse_args()


def load_config(args: argparse.Namespace) -> dict:
    with open(args.config, encoding="utf-8") as handle:
        config = json.load(handle)
    config_dir = Path(args.config).resolve().parent
    config["trigger_count"] = max(
        args.trigger_count,
        1 if args.trigger_once else 0,
        int(config.get("trigger_count", 0)),
    )
    config["corrupt_next_payload"] = args.corrupt_next_payload or bool(
        config.get("corrupt_next_payload", False)
    )
    config["truncate_camera_id"] = int(
        getattr(args, "truncate_camera_id", 0) or config.get("truncate_camera_id", 0)
    )
    config["diagnostic_usb_trigger"] = args.diagnostic_usb_trigger
    config["allow_incomplete_node_set"] = args.allow_incomplete_node_set
    initial_route = getattr(args, "initial_route", None)
    if initial_route is not None:
        config["initial_route"] = initial_route
    quit_after_seconds = float(getattr(args, "quit_after_seconds", 0))
    if quit_after_seconds < 0:
        raise ValueError("quit_after_seconds must not be negative")
    config["quit_after_ms"] = round(quit_after_seconds * 1000)
    capture_after_seconds = float(getattr(args, "capture_after_seconds", 0))
    if capture_after_seconds < 0:
        raise ValueError("capture_after_seconds must not be negative")
    if capture_after_seconds > 0 and config.get("initial_route") != "capture":
        raise ValueError("capture_after_seconds requires --initial-route capture")
    config["capture_after_ms"] = round(capture_after_seconds * 1000)
    if config.get("startup_logo"):
        logo_path = Path(config["startup_logo"])
        config["startup_logo"] = str(
            (logo_path if logo_path.is_absolute() else config_dir / logo_path).resolve()
        )
    return config


def main() -> None:
    args = parse_args()
    config = load_config(args)
    from .ui import run_headless, run_ui

    storage_config = config.get("usb_storage", {})
    storage = UsbStorageResolver(
        capture_directory=storage_config.get("capture_directory", "BulletTime"),
        preferred_mount_name=storage_config.get("preferred_mount_name"),
        auto_mount=bool(storage_config.get("auto_mount", True)),
        stale_staging_seconds=float(storage_config.get("stale_staging_seconds", 3600)),
    )
    trigger_pin = int(config["trigger_gpio_bcm"])
    pulse_seconds = float(config["trigger_pulse_ms"]) / 1000

    def request_shutdown(_signal_number, _frame) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)
    try:
        with HardwareTrigger(trigger_pin, pulse_seconds) as trigger:
            (run_headless if args.headless else run_ui)(config, trigger, storage)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
