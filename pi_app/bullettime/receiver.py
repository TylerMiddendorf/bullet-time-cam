"""Concurrent camera-node sessions and four-node capture-set coordination."""

from __future__ import annotations

import io
import logging
import queue
import threading
import time
import zlib

from PIL import Image

from . import APP_VERSION
from .coordinator import CaptureSetCoordinator, CoordinationError
from .discovery import discover_ports
from .gpio_trigger import HardwareTrigger
from .media import commit_capture_set
from .metrics import resource_sample
from .protocol import (
    ACK,
    CAPTURE_REQUEST,
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
from .storage import StorageUnavailable, UsbStorageResolver

LOGGER = logging.getLogger(__name__)


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


def transaction_key(metadata: dict) -> tuple[str, str, int]:
    return (
        str(metadata.get("node_uid", "")),
        str(metadata.get("boot_id", "")),
        int(metadata.get("capture_seq", 0)),
    )


class NodeSession(threading.Thread):
    """Own one serial stream while forwarding framed events to the coordinator."""

    def __init__(self, owner: Receiver, port: str):
        super().__init__(daemon=True, name=f"camera-session:{port}")
        self.owner = owner
        self.port = port
        self.node_uid: str | None = None
        self.stream = None
        self.write_lock = threading.Lock()
        self.current_metadata: dict | None = None
        self.fault_armed = threading.Event()

    def send(self, message_type: int, metadata: dict) -> None:
        if self.stream is None:
            raise RuntimeError(f"camera session is not connected: {self.port}")
        with self.write_lock:
            self.stream.write(encode_frame(message_type, metadata))
            self.stream.flush()

    def run(self) -> None:
        import serial

        try:
            with serial.Serial(
                self.port,
                self.owner.config.get("serial_baud", 115200),
                timeout=float(self.owner.config.get("serial_read_timeout_seconds", 10)),
                write_timeout=10,
            ) as stream:
                self.stream = stream
                self.send(
                    PING,
                    {"host": "camerapi", "requested_monotonic_ns": time.monotonic_ns()},
                )
                hello = self._wait_for_hello()
                self.node_uid = self.owner.session_connected(self, hello.metadata)
                while not self.owner.stop.is_set():
                    try:
                        frame = read_frame(
                            stream,
                            validate_payload_crc=False,
                            payload_progress=lambda metadata, received, total: (
                                self.owner.payload_progress(self, metadata, received, total)
                            ),
                        )
                    except TimeoutError:
                        continue
                    if (
                        frame.message_type == LOG
                        and frame.metadata.get("message") == "TEST_CORRUPTION_ARMED"
                    ):
                        self.fault_armed.set()
                    self.owner.handle_frame(self, frame)
        except Exception as exc:  # serial/protocol hardware boundary
            self.owner.session_disconnected(self, exc)
        finally:
            self.stream = None

    def _wait_for_hello(self):
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and not self.owner.stop.is_set():
            try:
                frame = read_frame(self.stream)
            except TimeoutError:
                continue
            if frame.message_type == HELLO:
                return frame
        raise RuntimeError("camera HELLO timeout")


class Receiver(threading.Thread):
    """Discover all nodes, group one press, persist it, and publish UI events."""

    def __init__(
        self,
        config: dict,
        events: queue.Queue,
        commands: queue.Queue,
        stop: threading.Event,
        trigger: HardwareTrigger,
        storage: UsbStorageResolver,
    ):
        super().__init__(daemon=True, name="camera-coordinator")
        self.config, self.events, self.commands, self.stop = config, events, commands, stop
        self.trigger = trigger
        self.storage = storage
        self.logical_cameras = {
            str(uid): int(camera_id) for uid, camera_id in config.get("logical_cameras", {}).items()
        }
        if set(self.logical_cameras.values()) != {1, 2, 3, 4}:
            raise ValueError("logical_cameras must map exactly one UID to each Camera 1-4")
        self.coordinator = CaptureSetCoordinator(
            self.logical_cameras,
            association_window_ms=int(config.get("capture_association_ms", 250)),
            no_progress_timeout_ms=int(config.get("no_progress_timeout_ms", 5000)),
        )
        self.lock = threading.RLock()
        self.sessions: dict[str, NodeSession] = {}
        self.sessions_by_uid: dict[str, NodeSession] = {}
        self.session_retry_after_ns: dict[str, int] = {}
        self.capture_state: dict[tuple[str, str, int], dict] = {}
        self.pending_images: dict[tuple[str, str, int], dict] = {}
        self.pending_acks: dict[int, tuple[NodeSession, dict]] = {}
        self.rejected_images: dict[tuple[str, str, int], str] = {}
        self.automatic_triggers_remaining = int(config.get("trigger_count", 0))
        self.automatic_trigger_in_flight = False
        self.next_automatic_trigger_ns = 0
        self.diagnostic_usb_trigger = bool(config.get("diagnostic_usb_trigger", False))
        self.corrupt_next_payload = bool(config.get("corrupt_next_payload", False))
        self.truncate_camera_id = int(config.get("truncate_camera_id", 0))
        self.truncate_after_bytes = int(config.get("truncate_after_bytes", 64 * 1024))
        self.truncate_fault_triggered = False
        self.allow_incomplete_node_set = bool(config.get("allow_incomplete_node_set", False))
        self.pending_trigger: dict | None = None
        self.automatic_run_completed = threading.Event()

    def send_status(self, state: str, **values) -> None:
        self.events.put({"state": state, **values})

    def run(self) -> None:
        while not self.stop.is_set():
            self._refresh_sessions()
            self._process_commands()
            with self.lock:
                self._finalize_if_ready(time.monotonic_ns())
                self._expire_unanswered_trigger(time.monotonic_ns())
            self.stop.wait(0.05)

    def _refresh_sessions(self) -> None:
        discovered = set(discover_ports())
        now_ns = time.monotonic_ns()
        with self.lock:
            self.session_retry_after_ns = {
                port: retry_after_ns
                for port, retry_after_ns in self.session_retry_after_ns.items()
                if port in discovered
            }
            for port, session in list(self.sessions.items()):
                if not session.is_alive() and session.stream is None:
                    self.sessions.pop(port, None)
            for port in sorted(discovered):
                if port not in self.sessions and now_ns >= self.session_retry_after_ns.get(port, 0):
                    session = NodeSession(self, port)
                    self.sessions[port] = session
                    session.start()
            connected = len(self.sessions_by_uid)
        if not discovered and connected == 0 and self.coordinator.trigger_allowed:
            self.send_status("ERROR", message="No camera nodes found")

    def session_connected(self, session: NodeSession, hello_metadata: dict) -> str:
        uid = str(hello_metadata.get("node_uid", ""))
        camera_id = self.logical_cameras.get(uid)
        if camera_id is None:
            raise RuntimeError(f"Unregistered node UID: {uid}")
        with self.lock:
            existing = self.sessions_by_uid.get(uid)
            if existing is not None and existing is not session:
                raise RuntimeError(f"Duplicate session for Camera {camera_id}: {uid}")
            self.sessions_by_uid[uid] = session
            self.session_retry_after_ns.pop(session.port, None)
            connected = len(self.sessions_by_uid)
        try:
            storage_root = self.storage.resolve()
            self.send_status(
                "READY",
                message=(
                    f"{connected}/4 cameras connected\nUSB storage: {storage_root}\nTap to capture"
                ),
            )
        except StorageUnavailable as exc:
            self.send_status("ERROR", message=str(exc))
        return uid

    def session_disconnected(self, session: NodeSession, exc: Exception) -> None:
        with self.lock:
            if not self.stop.is_set():
                reconnect_ns = int(float(self.config.get("reconnect_seconds", 1.0)) * 1e9)
                self.session_retry_after_ns[session.port] = time.monotonic_ns() + max(
                    reconnect_ns, 50_000_000
                )
            active_before = self.coordinator.active_capture_id
            uid = session.node_uid
            if uid and self.sessions_by_uid.get(uid) is session:
                self.sessions_by_uid.pop(uid, None)
            current = session.current_metadata
            if current is not None:
                key = transaction_key(current)
                try:
                    self.coordinator.fail(
                        current,
                        "transfer_truncated",
                        (
                            f"Camera {self.logical_cameras.get(uid)} transfer interrupted "
                            f"on {session.port}: {exc}"
                        ),
                        time.monotonic_ns(),
                    )
                    self.pending_images.pop(key, None)
                    self.rejected_images[key] = "transfer_truncated"
                except CoordinationError:
                    pass
                session.current_metadata = None
                self._finalize_if_ready(time.monotonic_ns())
            connected = len(self.sessions_by_uid)
            capture_was_finalized = bool(
                active_before and self.coordinator.active_capture_id is None
            )
        if not self.stop.is_set() and not capture_was_finalized:
            camera_id = self.logical_cameras.get(uid)
            LOGGER.warning("Camera %s disconnected on %s: %s", camera_id, session.port, exc)
            message = (
                f"Camera {camera_id} disconnected\n{connected}/4 cameras connected"
                if camera_id is not None
                else f"Camera connection lost\n{connected}/4 cameras connected"
            )
            self.send_status(
                "LOADING" if self.coordinator.active_capture_id else "ERROR",
                message=message,
            )

    def _process_commands(self) -> None:
        requested = False
        try:
            while self.commands.get_nowait() == "CAPTURE":
                requested = True
        except queue.Empty:
            pass
        now_ns = time.monotonic_ns()
        with self.lock:
            automatic = (
                self.automatic_triggers_remaining > 0
                and not self.automatic_trigger_in_flight
                and (
                    self.allow_incomplete_node_set
                    and len(self.sessions_by_uid) > 0
                    or len(self.sessions_by_uid) == len(self.logical_cameras)
                )
                and all(
                    session.current_metadata is None for session in self.sessions_by_uid.values()
                )
                and now_ns >= self.next_automatic_trigger_ns
            )
        if requested or automatic:
            self._request_capture(automatic=automatic)

    def _request_capture(self, *, automatic: bool) -> None:
        with self.lock:
            if not self.coordinator.trigger_allowed or self.pending_trigger is not None:
                self.send_status("LOADING", message="Capture already in progress")
                return
            if any(
                session.current_metadata is not None for session in self.sessions_by_uid.values()
            ):
                self.send_status(
                    "LOADING", message="Waiting for all cameras to finish the prior capture"
                )
                return
            try:
                self.storage.resolve()
            except StorageUnavailable as exc:
                self.send_status("ERROR", message=str(exc))
                return
            sessions = list(self.sessions_by_uid.values())
            if not sessions:
                self.send_status("ERROR", message="No registered camera nodes are connected")
                return
            if self.corrupt_next_payload:
                target_id = int(self.config.get("corrupt_camera_id", 1))
                target = next(
                    (
                        session
                        for uid, session in self.sessions_by_uid.items()
                        if self.logical_cameras[uid] == target_id
                    ),
                    None,
                )
                if target is None:
                    self.send_status("ERROR", message=f"Camera {target_id} is not connected")
                    return
                target.fault_armed.clear()
                target.send(
                    TEST_CORRUPT_NEXT_IMAGE,
                    {"host": "camerapi", "reason": "live_four_node_nack_test"},
                )
                if not target.fault_armed.wait(timeout=2):
                    self.send_status(
                        "ERROR", message=f"Camera {target_id} did not acknowledge fault arming"
                    )
                    return
                self.corrupt_next_payload = False
            issued_ns = time.monotonic_ns()
            source = "diagnostic_usb" if self.diagnostic_usb_trigger else "pi_gpio17"
            self.pending_trigger = {"source": source, "issued_ns": issued_ns}
            if self.diagnostic_usb_trigger:
                for session in sessions:
                    session.send(
                        CAPTURE_REQUEST,
                        {"host": "camerapi", "reason": "explicit_diagnostic_usb_trigger"},
                    )
                loading_message = "Diagnostic USB capture requested on all connected cameras"
            else:
                self.trigger.pulse()
                loading_message = (
                    f"Hardware trigger pulsed for {self.trigger.pulse_seconds * 1000:.0f} ms"
                )
            if automatic:
                self.automatic_trigger_in_flight = True
            self.send_status("LOADING", message=loading_message)

    def _expire_unanswered_trigger(self, now_ns: int) -> None:
        if self.pending_trigger is None or self.coordinator.active_capture_id is not None:
            return
        timeout_ns = int(self.config.get("no_progress_timeout_ms", 5000)) * 1_000_000
        if now_ns - self.pending_trigger["issued_ns"] >= timeout_ns:
            self.pending_trigger = None
            self._finish_automatic_attempt(now_ns)
            self.send_status("ERROR", message="No camera reported capture start")

    def _finish_automatic_attempt(self, now_ns: int) -> None:
        if not self.automatic_trigger_in_flight:
            return
        self.automatic_triggers_remaining = max(0, self.automatic_triggers_remaining - 1)
        self.automatic_trigger_in_flight = False
        if self.automatic_triggers_remaining == 0:
            self.automatic_run_completed.set()
        self.next_automatic_trigger_ns = (
            now_ns + int(self.config.get("automatic_rearm_ms", 150)) * 1_000_000
        )

    def handle_frame(self, session: NodeSession, frame) -> None:
        now_ns = time.monotonic_ns()
        metadata = dict(frame.metadata)
        uid = str(metadata.get("node_uid", session.node_uid or ""))
        if uid != session.node_uid or uid not in self.logical_cameras:
            raise RuntimeError(f"Unexpected node identity on {session.port}: {uid}")
        metadata["logical_camera_id"] = self.logical_cameras[uid]
        with self.lock:
            if frame.message_type == CAPTURE_STARTED:
                self._capture_started(session, metadata, now_ns)
            elif frame.message_type == IMAGE:
                self._image_received(session, metadata, frame, now_ns)
            elif frame.message_type == TRANSFER_COMPLETE:
                self._transfer_complete(session, metadata, now_ns)
            elif frame.message_type == ERROR:
                self._node_error(session, metadata, now_ns)
            elif frame.message_type in {HELLO, LOG}:
                return

    def payload_progress(
        self, session: NodeSession, metadata: dict, received: int, total: int
    ) -> None:
        if received <= 0 or total <= 0 or metadata.get("node_uid") != session.node_uid:
            return
        with self.lock:
            try:
                self.coordinator.progress(metadata, time.monotonic_ns())
            except CoordinationError:
                pass
            camera_id = self.logical_cameras.get(str(session.node_uid))
            if (
                self.truncate_camera_id == camera_id
                and not self.truncate_fault_triggered
                and self.truncate_after_bytes <= received < total
                and session.stream is not None
            ):
                self.truncate_fault_triggered = True
                self.send_status(
                    "LOADING",
                    message=(
                        f"Test interruption: Camera {camera_id} serial stream closed "
                        f"after {received}/{total} IMAGE bytes"
                    ),
                )
                session.stream.close()

    def _capture_started(self, session: NodeSession, metadata: dict, now_ns: int) -> None:
        key = transaction_key(metadata)
        try:
            capture_id = self.coordinator.start(metadata, now_ns)
        except CoordinationError as exc:
            self.rejected_images[key] = "capture_association_rejected"
            self.send_status("LOADING", message=f"Camera event rejected: {exc}")
            return
        source = "physical_shared_bus"
        association_ns = int(self.config.get("trigger_event_association_ms", 1000)) * 1_000_000
        if self.pending_trigger and now_ns - self.pending_trigger["issued_ns"] <= association_ns:
            source = self.pending_trigger["source"]
        session.current_metadata = metadata
        self.capture_state[key] = {
            "capture_event_received_ns": now_ns,
            "trigger_source": source,
            "resource_samples": [resource_sample("capture_started", self.storage.active_root)],
        }
        self.send_status(
            "LOADING",
            message=f"Capture {capture_id}: Camera {metadata['logical_camera_id']} started",
        )

    def _image_received(self, session: NodeSession, metadata: dict, frame, now_ns: int) -> None:
        key = transaction_key(metadata)
        if key in self.rejected_images:
            return
        state = self.capture_state.get(key)
        if state is None:
            self.rejected_images[key] = "missing_capture_start"
            return
        state["payload_receive_started_ns"] = frame.payload_started_ns
        state["payload_received_ns"] = frame.payload_completed_ns
        state["resource_samples"].append(
            resource_sample("payload_received", self.storage.active_root)
        )
        try:
            if metadata.get("jpeg_bytes") != len(frame.payload):
                raise RuntimeError("JPEG metadata length mismatch")
            expected_crc = str(metadata.get("jpeg_crc32", "")).lower()
            computed_crc = f"{zlib.crc32(frame.payload) & 0xFFFFFFFF:08x}"
            if expected_crc != computed_crc:
                raise RuntimeError("JPEG metadata checksum mismatch")
            processing_started_ns = time.monotonic_ns()
            with Image.open(io.BytesIO(frame.payload)) as candidate:
                candidate.verify()
            processing_completed_ns = time.monotonic_ns()
            self.pending_images[key] = {
                "metadata": metadata,
                "payload": frame.payload,
                "state": state,
                "processing_started_ns": processing_started_ns,
                "processing_completed_ns": processing_completed_ns,
                "expected_crc32": expected_crc,
                "computed_crc32": computed_crc,
                "serial_port": session.port,
            }
        except Exception as exc:
            code = (
                "jpeg_checksum_mismatch"
                if "checksum" in str(exc).lower()
                else "jpeg_validation_failed"
            )
            self.coordinator.fail(metadata, code, str(exc), now_ns)
            self.rejected_images[key] = code
            self.send_status(
                "LOADING",
                message=f"Camera {metadata['logical_camera_id']} failed; finishing remaining views",
            )

    def _transfer_complete(self, session: NodeSession, metadata: dict, now_ns: int) -> None:
        key = transaction_key(metadata)
        if key in self.rejected_images:
            reason = self.rejected_images.pop(key)
            session.send(NACK, response_metadata(metadata, "failed", reason))
            session.current_metadata = None
            self._finalize_if_ready(now_ns)
            return
        pending = self.pending_images.pop(key, None)
        if pending is None:
            session.send(
                NACK,
                response_metadata(metadata, "failed", "missing matching IMAGE"),
            )
            return
        image_metadata = pending["metadata"]
        image_metadata["transfer_completed_us"] = metadata.get("transfer_completed_us")
        image_metadata["transfer_status"] = metadata.get("status")
        state = pending["state"]
        scalar_times = {name: value for name, value in state.items() if name.endswith("_ns")}
        node_times = {name: value for name, value in image_metadata.items() if name.endswith("_us")}
        image_metadata["host_metrics"] = {
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
        self.coordinator.complete(image_metadata, pending["payload"], now_ns)
        camera_id = int(image_metadata["logical_camera_id"])
        self.pending_acks[camera_id] = (session, image_metadata)
        session.current_metadata = None
        self._finalize_if_ready(now_ns)

    def _node_error(self, session: NodeSession, metadata: dict, now_ns: int) -> None:
        message = str(metadata.get("message", "Node error"))
        try:
            self.coordinator.fail(metadata, "node_error", message, now_ns)
            session.current_metadata = None
            self._finalize_if_ready(now_ns)
        except CoordinationError:
            self.send_status("ERROR", message=f"Camera node error: {message}")

    def _finalize_if_ready(self, now_ns: int) -> None:
        if self.coordinator.active_capture_id is None:
            return
        if not self.coordinator.ready() and not self.coordinator.timed_out(now_ns):
            return
        completed = self.coordinator.finalize(now_ns)
        try:
            capture_root = self.storage.resolve()
            review_path, manifest = commit_capture_set(
                capture_root,
                completed,
                storage=self.storage.manifest_details(),
                gif_frame_ms=int(self.config.get("gif_frame_ms", 150)),
                gif_max_width=int(self.config.get("gif_max_width", 800)),
            )
            for camera_id, (session, metadata) in list(self.pending_acks.items()):
                if camera_id in completed.images:
                    session.send(ACK, response_metadata(metadata, "committed"))
            failed = sorted(completed.errors)
            if failed:
                message = "; ".join(
                    f"Camera {camera_id}: {completed.errors[camera_id].message}"
                    for camera_id in failed
                )
                state = "REVIEW_WITH_ERROR" if review_path.is_file() else "ERROR"
                self.send_status(
                    state,
                    image=str(review_path) if review_path.is_file() else None,
                    manifest=manifest,
                    message=message,
                )
            else:
                self.send_status("REVIEW", image=str(review_path), manifest=manifest)
        except Exception as exc:
            for session, metadata in self.pending_acks.values():
                try:
                    session.send(NACK, response_metadata(metadata, "failed", str(exc)))
                except Exception:
                    pass
            self.send_status("ERROR", message=f"Capture set was not committed: {exc}")
        finally:
            self.pending_acks.clear()
            self.capture_state.clear()
            self.pending_images.clear()
            self.rejected_images.clear()
            self.pending_trigger = None
            self._finish_automatic_attempt(time.monotonic_ns())
