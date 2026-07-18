import io
import json
import queue
import tempfile
import threading
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from pi_app.bullettime.coordinator import CaptureSetCoordinator
from pi_app.bullettime.protocol import ACK, IMAGE, NACK, Frame
from pi_app.bullettime.receiver import Receiver, response_metadata, transaction_key

UIDS = {f"UID-{camera_id}": camera_id for camera_id in range(1, 5)}


class FakeStorage:
    def __init__(self, root):
        self.root = root
        self.active_root = root

    def resolve(self):
        return self.root

    def manifest_details(self):
        return {"transport": "usb", "available": True, "capture_root": str(self.root)}


class FakeTrigger:
    pulse_seconds = 0.1

    def __init__(self):
        self.pulse_count = 0

    def pulse(self):
        self.pulse_count += 1


class FakeSession:
    def __init__(self, camera_id):
        self.port = f"test-port-{camera_id}"
        self.node_uid = f"UID-{camera_id}"
        self.current_metadata = None
        self.sent = []
        self.fault_armed = threading.Event()

    def send(self, message_type, metadata):
        self.sent.append((message_type, metadata))


def jpeg(camera_id):
    output = io.BytesIO()
    Image.new("RGB", (16, 12), (camera_id * 50, 30, 90)).save(output, "JPEG")
    return output.getvalue()


def metadata(camera_id, sequence=1):
    payload = jpeg(camera_id)
    return {
        "node_uid": f"UID-{camera_id}",
        "boot_id": f"boot-{camera_id}",
        "capture_seq": sequence,
        "logical_camera_id": camera_id,
        "jpeg_bytes": len(payload),
        "jpeg_crc32": f"{zlib.crc32(payload) & 0xFFFFFFFF:08x}",
        "trigger_accepted_us": 100,
        "acquisition_started_us": 200,
        "frame_ready_us": 300,
        "transfer_started_us": 400,
    }


class ReceiverCompletionTests(unittest.TestCase):
    def setUp(self):
        self.resource_patch = patch(
            "pi_app.bullettime.receiver.resource_sample", return_value={"phase": "test"}
        )
        self.resource_patch.start()

    def tearDown(self):
        self.resource_patch.stop()

    def receiver(self, root):
        events = queue.Queue()
        receiver = Receiver(
            {
                "logical_cameras": UIDS,
                "capture_association_ms": 100,
                "no_progress_timeout_ms": 500,
            },
            events,
            queue.Queue(),
            threading.Event(),
            FakeTrigger(),
            FakeStorage(root),
        )
        receiver.coordinator = CaptureSetCoordinator(
            UIDS,
            association_window_ms=100,
            no_progress_timeout_ms=500,
            capture_id_factory=lambda: "capture-a",
        )
        return receiver, events

    def transfer(self, receiver, session, camera_id, *, bad_crc=False, start_ns=1_000_000):
        meta = metadata(camera_id)
        receiver._capture_started(session, meta, start_ns)
        payload = jpeg(camera_id)
        if bad_crc:
            meta["jpeg_crc32"] = "00000000"
        frame = Frame(
            IMAGE,
            meta,
            payload,
            payload_started_ns=start_ns + 1_000_000,
            payload_completed_ns=start_ns + 2_000_000,
        )
        receiver._image_received(session, meta, frame, start_ns + 2_000_000)
        receiver._transfer_complete(
            session,
            {
                **meta,
                "transfer_completed_us": 900,
                "status": "written",
            },
            start_ns + 3_000_000,
        )

    def test_acks_all_nodes_only_after_atomic_set_and_gif_commit(self):
        with tempfile.TemporaryDirectory() as temp:
            receiver, events = self.receiver(Path(temp))
            receiver.automatic_triggers_remaining = 1
            receiver.automatic_trigger_in_flight = True
            sessions = {camera_id: FakeSession(camera_id) for camera_id in range(1, 5)}
            for camera_id in (3, 1, 4, 2):
                self.transfer(
                    receiver,
                    sessions[camera_id],
                    camera_id,
                    start_ns=camera_id * 1_000_000,
                )

            for session in sessions.values():
                self.assertEqual([message for message, _ in session.sent], [ACK])
            review = None
            while not events.empty():
                event = events.get_nowait()
                if event["state"] == "REVIEW":
                    review = event
            self.assertIsNotNone(review)
            image_path = Path(review["image"])
            self.assertEqual(image_path.name, "bullet_time.gif")
            manifest = json.loads((image_path.parent / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "complete")
            self.assertEqual(len(manifest["cameras"]), 4)
            self.assertEqual(
                len([item for item in manifest["files"] if item["role"] == "original"]), 4
            )
            self.assertTrue(receiver.automatic_run_completed.is_set())

    def test_timeout_commits_three_view_partial_and_identifies_missing_camera(self):
        with tempfile.TemporaryDirectory() as temp:
            receiver, events = self.receiver(Path(temp))
            sessions = {camera_id: FakeSession(camera_id) for camera_id in range(1, 5)}
            for camera_id in (1, 2, 3):
                self.transfer(
                    receiver, sessions[camera_id], camera_id, start_ns=camera_id * 1_000_000
                )
            receiver._finalize_if_ready(600_000_000)

            event = None
            while not events.empty():
                candidate = events.get_nowait()
                if candidate["state"] == "REVIEW_WITH_ERROR":
                    event = candidate
            self.assertIsNotNone(event)
            self.assertIn("Camera 4", event["message"])
            self.assertEqual(event["manifest"]["status"], "partial")
            self.assertEqual([message for message, _ in sessions[1].sent], [ACK])
            self.assertEqual(sessions[4].sent, [])

    def test_corrupt_camera_is_nacked_while_other_views_are_committed(self):
        with tempfile.TemporaryDirectory() as temp:
            receiver, events = self.receiver(Path(temp))
            sessions = {camera_id: FakeSession(camera_id) for camera_id in range(1, 5)}
            self.transfer(receiver, sessions[2], 2, bad_crc=True, start_ns=2_000_000)
            for camera_id in (1, 3, 4):
                self.transfer(
                    receiver, sessions[camera_id], camera_id, start_ns=camera_id * 1_000_000
                )

            self.assertEqual([message for message, _ in sessions[2].sent], [NACK])
            for camera_id in (1, 3, 4):
                self.assertEqual([message for message, _ in sessions[camera_id].sent], [ACK])
            reviews = []
            while not events.empty():
                event = events.get_nowait()
                if event["state"] == "REVIEW_WITH_ERROR":
                    reviews.append(event)
            self.assertEqual(reviews[-1]["manifest"]["errors"][0]["logical_camera_id"], 2)
            self.assertEqual(reviews[-1]["manifest"]["errors"][0]["code"], "jpeg_checksum_mismatch")

    def test_commit_failure_nacks_every_success_and_publishes_no_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            receiver, _ = self.receiver(Path(temp))
            sessions = {camera_id: FakeSession(camera_id) for camera_id in range(1, 5)}
            with patch(
                "pi_app.bullettime.receiver.commit_capture_set", side_effect=OSError("drive full")
            ):
                for camera_id in range(1, 5):
                    self.transfer(
                        receiver, sessions[camera_id], camera_id, start_ns=camera_id * 1_000_000
                    )
            for session in sessions.values():
                self.assertEqual([message for message, _ in session.sent], [NACK])
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_missing_image_sends_targeted_nack(self):
        with tempfile.TemporaryDirectory() as temp:
            receiver, _ = self.receiver(Path(temp))
            session = FakeSession(1)
            meta = metadata(1)
            receiver._capture_started(session, meta, 1_000_000)
            receiver._transfer_complete(session, meta, 2_000_000)
            self.assertEqual(session.sent[0][0], NACK)
            self.assertEqual(session.sent[0][1]["error"], "missing matching IMAGE")

    def test_disconnect_during_transfer_becomes_typed_camera_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            receiver, _ = self.receiver(Path(temp))
            session = FakeSession(3)
            meta = metadata(3)
            receiver._capture_started(session, meta, 1_000_000)
            session.current_metadata = meta
            receiver.sessions_by_uid[session.node_uid] = session
            receiver.session_disconnected(session, OSError("cable removed"))
            self.assertEqual(receiver.coordinator._active.errors[3].code, "transfer_truncated")

    def test_failed_serial_port_reconnect_is_backed_off(self):
        with tempfile.TemporaryDirectory() as temp:
            receiver, _ = self.receiver(Path(temp))
            receiver.session_retry_after_ns["/dev/ttyACM0"] = 2_000_000_000

            with (
                patch(
                    "pi_app.bullettime.receiver.discover_ports",
                    return_value=["/dev/ttyACM0"],
                ),
                patch(
                    "pi_app.bullettime.receiver.time.monotonic_ns",
                    side_effect=[1_000_000_000, 2_000_000_000],
                ),
                patch("pi_app.bullettime.receiver.NodeSession") as session_class,
            ):
                receiver._refresh_sessions()
                session_class.assert_not_called()
                receiver._refresh_sessions()

            session_class.assert_called_once_with(receiver, "/dev/ttyACM0")
            session_class.return_value.start.assert_called_once_with()

    def test_explicit_truncation_hook_closes_selected_stream_once_mid_payload(self):
        with tempfile.TemporaryDirectory() as temp:
            receiver, events = self.receiver(Path(temp))
            receiver.truncate_camera_id = 2
            receiver.truncate_after_bytes = 64
            session = FakeSession(2)
            session.stream = unittest.mock.Mock()
            meta = metadata(2)

            receiver.payload_progress(session, meta, 63, 1000)
            session.stream.close.assert_not_called()
            receiver.payload_progress(session, meta, 64, 1000)
            receiver.payload_progress(session, meta, 128, 1000)

            session.stream.close.assert_called_once_with()
            self.assertTrue(receiver.truncate_fault_triggered)
            self.assertIn("after 64/1000", events.get_nowait()["message"])

    def test_automatic_capture_waits_until_all_four_sessions_are_connected(self):
        with tempfile.TemporaryDirectory() as temp:
            receiver, _ = self.receiver(Path(temp))
            receiver.automatic_triggers_remaining = 1
            receiver._process_commands()
            self.assertEqual(receiver.trigger.pulse_count, 0)
            self.assertIsNone(receiver.pending_trigger)

            receiver.sessions_by_uid = {
                f"UID-{camera_id}": FakeSession(camera_id) for camera_id in range(1, 5)
            }
            receiver.sessions_by_uid["UID-2"].current_metadata = metadata(2)
            receiver._process_commands()
            self.assertEqual(receiver.trigger.pulse_count, 0)
            receiver.sessions_by_uid["UID-2"].current_metadata = None
            receiver._process_commands()
            self.assertEqual(receiver.trigger.pulse_count, 1)
            self.assertTrue(receiver.automatic_trigger_in_flight)

    def test_explicit_incomplete_node_mode_allows_bounded_automatic_capture(self):
        with tempfile.TemporaryDirectory() as temp:
            receiver, _ = self.receiver(Path(temp))
            receiver.allow_incomplete_node_set = True
            receiver.automatic_triggers_remaining = 1
            receiver.sessions_by_uid = {
                f"UID-{camera_id}": FakeSession(camera_id) for camera_id in range(1, 4)
            }

            receiver._process_commands()

            self.assertEqual(receiver.trigger.pulse_count, 1)
            self.assertTrue(receiver.automatic_trigger_in_flight)

    def test_unanswered_automatic_trigger_exits_without_repeating(self):
        with tempfile.TemporaryDirectory() as temp:
            receiver, events = self.receiver(Path(temp))
            receiver.automatic_triggers_remaining = 1
            receiver.automatic_trigger_in_flight = True
            receiver.pending_trigger = {"source": "pi_gpio17", "issued_ns": 1}

            receiver._expire_unanswered_trigger(600_000_001)
            receiver._process_commands()

            self.assertEqual(receiver.automatic_triggers_remaining, 0)
            self.assertFalse(receiver.automatic_trigger_in_flight)
            self.assertTrue(receiver.automatic_run_completed.is_set())
            self.assertEqual(receiver.trigger.pulse_count, 0)
            self.assertEqual(events.get_nowait()["message"], "No camera reported capture start")

    def test_response_metadata_truncates_errors_for_bounded_control_frames(self):
        response = response_metadata(
            {"node_uid": "UID-1", "boot_id": "boot-1", "capture_seq": 1},
            "failed",
            "x" * 200,
        )
        self.assertEqual(len(response["error"]), 96)
        self.assertEqual(transaction_key(response), ("UID-1", "boot-1", 1))


if __name__ == "__main__":
    unittest.main()
