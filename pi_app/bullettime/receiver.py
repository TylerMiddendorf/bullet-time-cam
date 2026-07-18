"""Camera-node serial receiver and one-node capture transaction coordinator."""

from __future__ import annotations

import io
import queue
import threading
import time
import zlib

import serial
from PIL import Image

from . import APP_VERSION
from .capture_control import initiate_capture
from .discovery import discover_ports
from .gpio_trigger import HardwareTrigger
from .metrics import resource_sample
from .protocol import (
    ACK,
    CAPTURE_STARTED,
    ERROR,
    HELLO,
    IMAGE,
    LOG,
    NACK,
    PING,
    TEST_CORRUPT_NEXT_IMAGE,
    TRANSFER_COMPLETE,
    encode_frame,
    read_frame,
)
from .storage import StorageUnavailable, UsbStorageResolver, atomic_json, commit_capture


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
    """Discover a node, process framed transactions, and publish UI events."""

    def __init__(
        self,
        config: dict,
        events: queue.Queue,
        commands: queue.Queue,
        stop: threading.Event,
        trigger: HardwareTrigger,
        storage: UsbStorageResolver,
    ):
        super().__init__(daemon=True)
        self.config, self.events, self.commands, self.stop = config, events, commands, stop
        self.trigger = trigger
        self.storage = storage
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
        with serial.Serial(
            port,
            self.config.get("serial_baud", 115200),
            timeout=10,
            write_timeout=10,
        ) as stream:
            stream.write(
                encode_frame(
                    PING,
                    {"host": "camerapi", "requested_monotonic_ns": time.monotonic_ns()},
                )
            )
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
            try:
                storage_root = self.storage.resolve()
                self.send_status(
                    "READY",
                    message=f"Camera 1 connected: {port}\nUSB storage: {storage_root}\nTap to capture",
                )
            except StorageUnavailable as exc:
                self.send_status("ERROR", message=str(exc))
            while not self.stop.is_set():
                automatic_request = (
                    self.automatic_triggers_remaining > 0 and not self.automatic_trigger_in_flight
                )
                request_capture = automatic_request
                try:
                    while self.commands.get_nowait() == "CAPTURE":
                        request_capture = True
                except queue.Empty:
                    pass
                if request_capture:
                    try:
                        self.storage.resolve()
                    except StorageUnavailable as exc:
                        self.send_status("ERROR", message=str(exc))
                        request_capture = False
                if request_capture:
                    if self.corrupt_next_payload:
                        stream.write(
                            encode_frame(
                                TEST_CORRUPT_NEXT_IMAGE,
                                {
                                    "host": "camerapi",
                                    "reason": "live_nack_test",
                                },
                            )
                        )
                        stream.flush()
                        self.corrupt_next_payload = False
                    trigger_issued_ns = time.monotonic_ns()
                    self.pending_trigger = {
                        "source": (
                            "diagnostic_usb" if self.diagnostic_usb_trigger else "pi_gpio17"
                        ),
                        "issued_ns": trigger_issued_ns,
                    }
                    loading_message = initiate_capture(
                        stream, self.trigger, self.diagnostic_usb_trigger
                    )
                    if automatic_request:
                        self.automatic_trigger_in_flight = True
                    self.send_status("LOADING", message=loading_message)
                try:
                    # The receiver validates IMAGE payload CRC itself so it can
                    # send a targeted NACK containing the transaction metadata.
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
                    association_ns = (
                        int(self.config.get("trigger_event_association_ms", 1000)) * 1_000_000
                    )
                    if (
                        self.pending_trigger
                        and now - self.pending_trigger["issued_ns"] <= association_ns
                    ):
                        trigger_source = self.pending_trigger["source"]
                    self.pending_trigger = None
                    self.capture[key] = {
                        "capture_event_received_ns": now,
                        "trigger_source": trigger_source,
                        "resource_samples": [
                            resource_sample("capture_started", self.storage.active_root)
                        ],
                    }
                    self.send_status("LOADING", message="Capturing image...")
                elif frame.message_type == IMAGE:
                    state = self.capture.setdefault(
                        key, {"capture_event_received_ns": now, "resource_samples": []}
                    )
                    state["payload_receive_started_ns"] = frame.payload_started_ns
                    state["payload_received_ns"] = frame.payload_completed_ns
                    state["resource_samples"].append(
                        resource_sample("payload_received", self.storage.active_root)
                    )
                    try:
                        if meta.get("jpeg_bytes") != len(frame.payload):
                            raise RuntimeError("JPEG metadata length mismatch")
                        expected_crc = str(meta.get("jpeg_crc32", "")).lower()
                        computed_crc = f"{zlib.crc32(frame.payload) & 0xFFFFFFFF:08x}"
                        if expected_crc != computed_crc:
                            raise RuntimeError("JPEG metadata checksum mismatch")
                        processing_started_ns = time.monotonic_ns()
                        with Image.open(io.BytesIO(frame.payload)) as candidate:
                            candidate.verify()
                        processing_completed_ns = time.monotonic_ns()
                        self.pending_images[key] = {
                            "metadata": meta,
                            "payload": frame.payload,
                            "state": state,
                            "processing_started_ns": processing_started_ns,
                            "processing_completed_ns": processing_completed_ns,
                            "expected_crc32": expected_crc,
                            "computed_crc32": computed_crc,
                            "serial_port": port,
                        }
                    except Exception as exc:
                        stream.write(
                            encode_frame(NACK, response_metadata(meta, "failed", str(exc)))
                        )
                        stream.flush()
                        self.rejected_images.add(key)
                        message = f"NACK sent: {exc}"
                        print(message, flush=True)
                        self.send_status("ERROR", message=message)
                elif frame.message_type == ERROR:
                    self.send_status("ERROR", message=meta.get("message", "Node error"))
                elif frame.message_type == LOG:
                    # Diagnostics must not replace the latest review image.
                    continue
                elif frame.message_type == TRANSFER_COMPLETE:
                    self._complete_transfer(stream, key, meta)

    def _complete_transfer(self, stream, key: tuple, metadata: dict) -> None:
        if key in self.rejected_images:
            self.rejected_images.remove(key)
            return
        pending = self.pending_images.pop(key, None)
        if pending is None:
            stream.write(
                encode_frame(
                    NACK,
                    response_metadata(metadata, "failed", "missing matching IMAGE"),
                )
            )
            stream.flush()
            return
        try:
            image_meta = pending["metadata"]
            image_meta["transfer_completed_us"] = metadata.get("transfer_completed_us")
            image_meta["transfer_status"] = metadata.get("status")
            state = pending["state"]
            scalar_times = {name: value for name, value in state.items() if name.endswith("_ns")}
            node_times = {name: value for name, value in image_meta.items() if name.endswith("_us")}
            metrics = {
                "trigger_source": state.get("trigger_source", "unknown"),
                "pi_monotonic_ns": scalar_times,
                "node_monotonic_us": node_times,
                "durations_ms": {
                    "capture_event_to_payload_received": (
                        state["payload_received_ns"] - state["capture_event_received_ns"]
                    )
                    / 1_000_000,
                    "host_payload_receive": (
                        state["payload_received_ns"] - state["payload_receive_started_ns"]
                    )
                    / 1_000_000,
                    "jpeg_decode_validation": (
                        pending["processing_completed_ns"] - pending["processing_started_ns"]
                    )
                    / 1_000_000,
                    "node_transfer": (
                        node_times["transfer_completed_us"] - node_times["transfer_started_us"]
                    )
                    / 1000,
                },
                "resource_samples": state["resource_samples"],
                "integrity": {
                    "expected_crc32": pending["expected_crc32"],
                    "computed_crc32": pending["computed_crc32"],
                    "checksum_ok": True,
                },
                "app_version": APP_VERSION,
                "serial_port": pending["serial_port"],
            }
            capture_root = self.storage.resolve()
            metrics["storage"] = self.storage.manifest_details()
            path, manifest = commit_capture(capture_root, image_meta, pending["payload"], metrics)
            committed_ns = time.monotonic_ns()
            manifest["metrics"]["pi_monotonic_ns"]["original_committed_ns"] = committed_ns
            manifest["metrics"]["durations_ms"]["payload_to_commit"] = (
                committed_ns - state["payload_received_ns"]
            ) / 1_000_000
            atomic_json(path.parent / "manifest.json", manifest)
            stream.write(encode_frame(ACK, response_metadata(image_meta, "committed")))
            stream.flush()
            self.send_status("REVIEW", image=str(path), manifest=manifest)
            if self.automatic_trigger_in_flight:
                self.automatic_triggers_remaining -= 1
                self.automatic_trigger_in_flight = False
        except Exception as exc:
            stream.write(encode_frame(NACK, response_metadata(metadata, "failed", str(exc))))
            stream.flush()
            raise
