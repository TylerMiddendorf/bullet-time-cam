"""One-node USB receiver, evidence recorder, and touchscreen UI."""

from __future__ import annotations

import argparse
import glob
import io
import json
import os
import queue
import signal
import threading
import time
from pathlib import Path

import psutil
import serial
from PIL import Image, ImageOps, ImageTk

from . import APP_VERSION
from .capture_control import initiate_capture
from .gpio_trigger import HardwareTrigger
from .protocol import (ACK, CAPTURE_STARTED, ERROR, HELLO, IMAGE, LOG, NACK,
                       PING, TEST_CORRUPT_NEXT_IMAGE, TRANSFER_COMPLETE, encode_frame, read_frame)
from .storage import atomic_json, commit_capture


def discover_ports() -> list[str]:
    candidates = glob.glob("/dev/serial/by-id/*") + glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*")
    return list(dict.fromkeys(os.path.realpath(path) for path in candidates))


def resource_sample(phase: str) -> dict:
    process = psutil.Process()
    process_cpu = process.cpu_times()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "phase": phase,
        "pi_monotonic_ns": time.monotonic_ns(),
        "process_cpu_user_seconds": process_cpu.user,
        "process_cpu_system_seconds": process_cpu.system,
        "process_rss_bytes": process.memory_info().rss,
        "available_memory_bytes": memory.available,
        "storage_free_bytes": disk.free,
        "system_load_average_1m": psutil.getloadavg()[0],
    }


def response_metadata(metadata: dict, status: str, error: str | None = None) -> dict:
    response = {
        "node_uid": metadata.get("node_uid"),
        "boot_id": metadata.get("boot_id"),
        "capture_seq": metadata.get("capture_seq"),
        "status": status,
    }
    if error:
        response["error"] = error[:96]
    return response


class Receiver(threading.Thread):
    def __init__(self, config: dict, events: queue.Queue, commands: queue.Queue,
                 stop: threading.Event, trigger: HardwareTrigger):
        super().__init__(daemon=True)
        self.config, self.events, self.commands, self.stop = config, events, commands, stop
        self.trigger = trigger
        self.capture = {}
        self.pending_images = {}
        self.rejected_images = set()
        self.automatic_triggers_remaining = int(config.get("trigger_count", 0))
        self.automatic_trigger_in_flight = False
        self.diagnostic_usb_trigger = bool(config.get("diagnostic_usb_trigger", False))
        self.corrupt_next_payload = bool(config.get("corrupt_next_payload", False))
        self.pending_trigger = None

    def send_status(self, state: str, **values) -> None:
        self.events.put({"state": state, **values})

    def run(self) -> None:
        while not self.stop.is_set():
            ports = discover_ports()
            if not ports:
                self.send_status("ERROR", message="No camera node found")
                self.stop.wait(self.config.get("reconnect_seconds", 1.0))
                continue
            for port in ports:
                if self.stop.is_set():
                    return
                try:
                    self.receive_port(port)
                except Exception as exc:  # hardware boundary: keep rediscovering
                    self.send_status("ERROR", message=f"{port}: {exc}")
            self.stop.wait(self.config.get("reconnect_seconds", 1.0))

    def receive_port(self, port: str) -> None:
        with serial.Serial(port, self.config.get("serial_baud", 115200), timeout=10, write_timeout=10) as stream:
            stream.write(encode_frame(PING, {"host": "camerapi", "requested_monotonic_ns": time.monotonic_ns()}))
            stream.flush()
            hello = None
            probe_deadline = time.monotonic() + 15
            while time.monotonic() < probe_deadline:
                try:
                    candidate = read_frame(stream)
                except TimeoutError:
                    continue
                if candidate.message_type == HELLO:
                    hello = candidate
                    break
            if hello is None:
                raise RuntimeError("camera HELLO timeout")
            node_uid = hello.metadata.get("node_uid")
            if self.config.get("logical_cameras", {}).get(node_uid) != 1:
                raise RuntimeError(f"Unregistered node UID: {node_uid}")
            self.send_status("READY", message=f"Camera 1 connected: {port}\nTap to capture")
            while not self.stop.is_set():
                automatic_request = self.automatic_triggers_remaining > 0 and not self.automatic_trigger_in_flight
                request_capture = automatic_request
                try:
                    while self.commands.get_nowait() == "CAPTURE":
                        request_capture = True
                except queue.Empty:
                    pass
                if request_capture:
                    if self.corrupt_next_payload:
                        stream.write(encode_frame(TEST_CORRUPT_NEXT_IMAGE, {
                            "host": "camerapi", "reason": "checkpoint4_live_nack_test",
                        }))
                        stream.flush()
                        self.corrupt_next_payload = False
                    trigger_issued_ns = time.monotonic_ns()
                    self.pending_trigger = {
                        "source": "diagnostic_usb" if self.diagnostic_usb_trigger else "pi_gpio17",
                        "issued_ns": trigger_issued_ns,
                    }
                    loading_message = initiate_capture(
                        stream, self.trigger, self.diagnostic_usb_trigger
                    )
                    if automatic_request:
                        self.automatic_trigger_in_flight = True
                    self.send_status("LOADING", message=loading_message)
                frame_read_started_ns = time.monotonic_ns()
                try:
                    # The receiver verifies IMAGE payload CRC itself so it retains the
                    # metadata needed to send a targeted NACK on a live bad payload.
                    frame = read_frame(stream, validate_payload_crc=False)
                except TimeoutError:
                    continue
                now = time.monotonic_ns()
                meta = frame.metadata
                node_uid = meta.get("node_uid")
                logical_id = self.config.get("logical_cameras", {}).get(node_uid)
                if node_uid and logical_id != 1:
                    raise RuntimeError(f"Unregistered node UID: {node_uid}")
                meta["logical_camera_id"] = logical_id
                key = (meta.get("node_uid"), meta.get("boot_id"), meta.get("capture_seq"))
                if frame.message_type == CAPTURE_STARTED:
                    trigger_source = "physical_shared_bus"
                    association_ns = int(self.config.get("trigger_event_association_ms", 1000)) * 1_000_000
                    if self.pending_trigger and now - self.pending_trigger["issued_ns"] <= association_ns:
                        trigger_source = self.pending_trigger["source"]
                    self.pending_trigger = None
                    self.capture[key] = {
                        "capture_event_received_ns": now,
                        "trigger_source": trigger_source,
                        "resource_samples": [resource_sample("capture_started")],
                    }
                    self.send_status("LOADING", message="Capturing image...")
                elif frame.message_type == IMAGE:
                    state = self.capture.setdefault(key, {"capture_event_received_ns": now, "resource_samples": []})
                    state["payload_receive_started_ns"] = frame.payload_started_ns
                    state["payload_received_ns"] = frame.payload_completed_ns
                    state["resource_samples"].append(resource_sample("payload_received"))
                    try:
                        if meta.get("jpeg_bytes") != len(frame.payload):
                            raise RuntimeError("JPEG metadata length mismatch")
                        expected_crc = str(meta.get("jpeg_crc32", "")).lower()
                        import zlib
                        computed_crc = f"{zlib.crc32(frame.payload) & 0xFFFFFFFF:08x}"
                        if expected_crc != computed_crc:
                            raise RuntimeError("JPEG metadata checksum mismatch")
                        processing_started_ns = time.monotonic_ns()
                        with Image.open(io.BytesIO(frame.payload)) as candidate:
                            candidate.verify()
                        processing_completed_ns = time.monotonic_ns()
                        self.pending_images[key] = {
                            "metadata": meta, "payload": frame.payload, "state": state,
                            "processing_started_ns": processing_started_ns,
                            "processing_completed_ns": processing_completed_ns,
                            "expected_crc32": expected_crc, "computed_crc32": computed_crc,
                            "serial_port": port,
                        }
                    except Exception as exc:
                        stream.write(encode_frame(NACK, response_metadata(meta, "failed", str(exc))))
                        stream.flush()
                        self.rejected_images.add(key)
                        message = f"NACK sent: {exc}"
                        print(message, flush=True)
                        self.send_status("ERROR", message=message)
                elif frame.message_type == ERROR:
                    self.send_status("ERROR", message=meta.get("message", "Node error"))
                elif frame.message_type == LOG:
                    # Diagnostic protocol messages must not replace the latest
                    # REVIEW image on the touchscreen.
                    continue
                elif frame.message_type == TRANSFER_COMPLETE:
                    if key in self.rejected_images:
                        self.rejected_images.remove(key)
                        continue
                    pending = self.pending_images.pop(key, None)
                    if pending is None:
                        stream.write(encode_frame(NACK, response_metadata(meta, "failed", "missing matching IMAGE")))
                        stream.flush()
                        continue
                    try:
                        image_meta = pending["metadata"]
                        image_meta["transfer_completed_us"] = meta.get("transfer_completed_us")
                        image_meta["transfer_status"] = meta.get("status")
                        state = pending["state"]
                        scalar_times = {name: value for name, value in state.items() if name.endswith("_ns")}
                        node_times = {name: value for name, value in image_meta.items() if name.endswith("_us")}
                        metrics = {
                            "trigger_source": state.get("trigger_source", "unknown"),
                            "pi_monotonic_ns": scalar_times,
                            "node_monotonic_us": node_times,
                            "durations_ms": {
                                "capture_event_to_payload_received": (state["payload_received_ns"] - state["capture_event_received_ns"]) / 1_000_000,
                                "host_payload_receive": (state["payload_received_ns"] - state["payload_receive_started_ns"]) / 1_000_000,
                                "jpeg_decode_validation": (pending["processing_completed_ns"] - pending["processing_started_ns"]) / 1_000_000,
                                "node_transfer": (node_times["transfer_completed_us"] - node_times["transfer_started_us"]) / 1000,
                            },
                            "resource_samples": state["resource_samples"],
                            "integrity": {"expected_crc32": pending["expected_crc32"], "computed_crc32": pending["computed_crc32"], "checksum_ok": True},
                            "app_version": APP_VERSION,
                            "serial_port": pending["serial_port"],
                        }
                        path, manifest = commit_capture(Path(self.config["storage_root"]), image_meta, pending["payload"], metrics)
                        committed_ns = time.monotonic_ns()
                        manifest["metrics"]["pi_monotonic_ns"]["original_committed_ns"] = committed_ns
                        manifest["metrics"]["durations_ms"]["payload_to_commit"] = (committed_ns - state["payload_received_ns"]) / 1_000_000
                        atomic_json(path.parent / "manifest.json", manifest)
                        stream.write(encode_frame(ACK, response_metadata(image_meta, "committed")))
                        stream.flush()
                        self.send_status("REVIEW", image=str(path), manifest=manifest)
                        if self.automatic_trigger_in_flight:
                            self.automatic_triggers_remaining -= 1
                            self.automatic_trigger_in_flight = False
                    except Exception as exc:
                        stream.write(encode_frame(NACK, response_metadata(meta, "failed", str(exc))))
                        stream.flush()
                        raise


def run_headless(config: dict, trigger: HardwareTrigger) -> None:
    events, commands, stop = queue.Queue(), queue.Queue(), threading.Event()
    Receiver(config, events, commands, stop, trigger).start()
    try:
        while True:
            print(json.dumps(events.get(), sort_keys=True), flush=True)
    except KeyboardInterrupt:
        stop.set()


def run_ui(config: dict, trigger: HardwareTrigger) -> None:
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
                ((display_size[0] - logo.width) // 2, (display_size[1] - logo.height) // 2),
            )
            image_ref["value"] = ImageTk.PhotoImage(canvas)
        label.configure(image=image_ref["value"])

    # Map a complete logo frame before receiver discovery can publish status.
    # This makes the first application-owned frame match the boot splash.
    root.update_idletasks()
    root.update()

    events, commands, stop = queue.Queue(), queue.Queue(), threading.Event()
    Receiver(config, events, commands, stop, trigger).start()

    def poll() -> None:
        try:
            while True:
                event = events.get_nowait()
                state = event["state"]
                ui_state["value"] = state
                if state == "REVIEW":
                    source = Image.open(event["image"])
                    source.thumbnail((config.get("display_width", 800), config.get("display_height", 480)))
                    image_ref["value"] = ImageTk.PhotoImage(source)
                    label.configure(image=image_ref["value"], text="")
                    def rendered(path=Path(event["image"]), manifest=event["manifest"]):
                        rendered_ns = time.monotonic_ns()
                        manifest["metrics"]["pi_monotonic_ns"]["display_callback_ns"] = rendered_ns
                        start = manifest["metrics"]["pi_monotonic_ns"].get("capture_event_received_ns", rendered_ns)
                        manifest["metrics"]["durations_ms"]["capture_event_to_display_callback"] = (rendered_ns - start) / 1_000_000
                        atomic_json(path.parent / "manifest.json", manifest)
                    root.after_idle(rendered)
                else:
                    color = "#ffb000" if state == "LOADING" else ("#ff5050" if state == "ERROR" else "white")
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="pi_app/config.json")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--trigger-once", action="store_true", help="issue one GPIO hardware-trigger pulse after connecting")
    parser.add_argument("--trigger-count", type=int, default=0, help="issue N sequential GPIO hardware-trigger pulses")
    parser.add_argument(
        "--diagnostic-usb-trigger",
        action="store_true",
        help="use explicit USB CAPTURE_REQUEST test scaffolding instead of GPIO pulses",
    )
    parser.add_argument("--corrupt-next-payload", action="store_true",
                        help="arm test-only corruption of the next requested USB image")
    args = parser.parse_args()
    with open(args.config, encoding="utf-8") as handle:
        config = json.load(handle)
    config_dir = Path(args.config).resolve().parent
    config["trigger_count"] = max(args.trigger_count, 1 if args.trigger_once else 0,
                                  int(config.get("trigger_count", 0)))
    config["corrupt_next_payload"] = args.corrupt_next_payload or bool(config.get("corrupt_next_payload", False))
    config["diagnostic_usb_trigger"] = args.diagnostic_usb_trigger
    config["storage_root"] = str((config_dir / config["storage_root"]).resolve())
    if config.get("startup_logo"):
        logo_path = Path(config["startup_logo"])
        config["startup_logo"] = str((logo_path if logo_path.is_absolute() else config_dir / logo_path).resolve())
    (Path(config["storage_root"])).mkdir(parents=True, exist_ok=True)
    trigger_pin = int(config["trigger_gpio_bcm"])
    pulse_seconds = float(config["trigger_pulse_ms"]) / 1000

    def request_shutdown(_signal_number, _frame) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)
    try:
        with HardwareTrigger(trigger_pin, pulse_seconds) as trigger:
            (run_headless if args.headless else run_ui)(config, trigger)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
