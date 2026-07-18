import io
import json
import queue
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from pi_app.bullettime.protocol import ACK, NACK, read_frame
from pi_app.bullettime.receiver import Receiver, response_metadata


class FakeStream(io.BytesIO):
    def flush(self):
        pass


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

    def pulse(self):
        pass


def jpeg():
    output = io.BytesIO()
    Image.new("RGB", (8, 6), "teal").save(output, "JPEG")
    return output.getvalue()


class ReceiverCompletionTests(unittest.TestCase):
    def receiver(self, root):
        events = queue.Queue()
        receiver = Receiver(
            {"logical_cameras": {"UID-1": 1}},
            events,
            queue.Queue(),
            threading.Event(),
            FakeTrigger(),
            FakeStorage(root),
        )
        return receiver, events

    def pending(self, receiver, key):
        payload = jpeg()
        receiver.pending_images[key] = {
            "metadata": {
                "node_uid": "UID-1",
                "boot_id": "boot-1",
                "capture_seq": 1,
                "transfer_started_us": 100,
            },
            "payload": payload,
            "state": {
                "capture_event_received_ns": 1_000_000,
                "payload_receive_started_ns": 2_000_000,
                "payload_received_ns": 3_000_000,
                "resource_samples": [],
                "trigger_source": "physical_shared_bus",
            },
            "processing_started_ns": 3_100_000,
            "processing_completed_ns": 3_200_000,
            "expected_crc32": "00000000",
            "computed_crc32": "00000000",
            "serial_port": "test-port",
        }

    def test_ack_is_sent_only_after_manifest_and_original_are_committed(self):
        with tempfile.TemporaryDirectory() as temp:
            receiver, events = self.receiver(Path(temp))
            key = ("UID-1", "boot-1", 1)
            self.pending(receiver, key)
            stream = FakeStream()
            receiver._complete_transfer(
                stream,
                key,
                {
                    "node_uid": "UID-1",
                    "boot_id": "boot-1",
                    "capture_seq": 1,
                    "transfer_completed_us": 300,
                    "status": "written",
                },
            )

            response = read_frame(io.BytesIO(stream.getvalue()))
            self.assertEqual(response.message_type, ACK)
            event = events.get_nowait()
            self.assertEqual(event["state"], "REVIEW")
            image_path = Path(event["image"])
            self.assertTrue(image_path.is_file())
            manifest = json.loads((image_path.parent / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["capture_id"], image_path.parent.name)

    def test_commit_failure_sends_nack_and_never_sends_ack(self):
        with tempfile.TemporaryDirectory() as temp:
            receiver, _ = self.receiver(Path(temp))
            key = ("UID-1", "boot-1", 1)
            self.pending(receiver, key)
            stream = FakeStream()
            with patch(
                "pi_app.bullettime.receiver.commit_capture", side_effect=OSError("drive full")
            ):
                with self.assertRaisesRegex(OSError, "drive full"):
                    receiver._complete_transfer(
                        stream,
                        key,
                        {
                            "node_uid": "UID-1",
                            "boot_id": "boot-1",
                            "capture_seq": 1,
                            "transfer_completed_us": 300,
                        },
                    )
            responses = []
            encoded = io.BytesIO(stream.getvalue())
            while encoded.tell() < len(stream.getvalue()):
                responses.append(read_frame(encoded).message_type)
            self.assertEqual(responses, [NACK])

    def test_missing_image_sends_targeted_nack(self):
        with tempfile.TemporaryDirectory() as temp:
            receiver, _ = self.receiver(Path(temp))
            stream = FakeStream()
            metadata = {"node_uid": "UID-1", "boot_id": "boot-1", "capture_seq": 9}
            receiver._complete_transfer(stream, ("UID-1", "boot-1", 9), metadata)
            response = read_frame(io.BytesIO(stream.getvalue()))
            self.assertEqual(response.message_type, NACK)
            self.assertEqual(response.metadata["error"], "missing matching IMAGE")

    def test_response_metadata_truncates_errors_for_bounded_control_frames(self):
        response = response_metadata(
            {"node_uid": "UID-1", "boot_id": "boot-1", "capture_seq": 1},
            "failed",
            "x" * 200,
        )
        self.assertEqual(len(response["error"]), 96)


if __name__ == "__main__":
    unittest.main()
