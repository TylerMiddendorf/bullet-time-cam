import json
import shutil
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path


class FirmwareHostTests(unittest.TestCase):
    def test_preview_is_additive_and_preserves_capture_protocol_values(self):
        repository = Path(__file__).resolve().parents[2]
        protocol = (repository / "button_capture" / "btc_protocol.h").read_text(encoding="utf-8")
        config = (repository / "button_capture" / "firmware_config.h").read_text(encoding="utf-8")

        expected_messages = {
            "MSG_HELLO": 1,
            "MSG_CAPTURE_STARTED": 2,
            "MSG_IMAGE": 3,
            "MSG_TRANSFER_COMPLETE": 4,
            "MSG_ERROR": 5,
            "MSG_LOG": 6,
            "MSG_CAPTURE_REQUEST": 7,
            "MSG_PING": 8,
            "MSG_TEST_CORRUPT_NEXT_IMAGE": 9,
            "MSG_PREVIEW_REQUEST": 10,
            "MSG_PREVIEW_IMAGE": 11,
        }
        for name, value in expected_messages.items():
            self.assertIn(f"constexpr uint8_t {name} = {value};", protocol)
        self.assertIn("CAPTURE_WIDTH = 2048", config)
        self.assertIn("CAPTURE_HEIGHT = 1536", config)
        self.assertIn("CAPTURE_FRAME_SIZE = FRAMESIZE_QXGA", config)
        self.assertIn("PREVIEW_WIDTH = 320", config)
        self.assertIn("PREVIEW_HEIGHT = 240", config)
        self.assertIn("MAX_PREVIEW_JPEG_BYTES = 64 * 1024", config)
        self.assertIn("PREVIEW_FRAME_ATTEMPTS = 3", config)

    def test_preview_restores_still_mode_and_checks_trigger_before_transfer(self):
        repository = Path(__file__).resolve().parents[2]
        source = (repository / "button_capture" / "camera_capture.cpp").read_text(encoding="utf-8")
        preview = source[
            source.index("bool sendPreviewFrame()") : source.index("bool capturePhoto()")
        ]

        restore = preview.rindex("setFrameSize(sensor, CAPTURE_FRAME_SIZE)")
        trigger = preview.rindex("sharedTriggerPressed()")
        transfer = preview.index("sendFrame(MSG_PREVIEW_IMAGE")
        self.assertLess(restore, trigger)
        self.assertLess(trigger, transfer)
        self.assertIn("frame->len > MAX_PREVIEW_JPEG_BYTES", preview)
        self.assertIn("attempt < PREVIEW_FRAME_ATTEMPTS", preview)

    def test_registered_nodes_receive_distinct_transfer_slots(self):
        repository = Path(__file__).resolve().parents[2]
        config = json.loads((repository / "pi_app" / "config.json").read_text(encoding="utf-8"))
        slots = {uid: zlib.crc32(uid.encode("ascii")) % 4 for uid in config["logical_cameras"]}
        self.assertEqual(set(slots.values()), {0, 1, 2, 3})

    @unittest.skipUnless(shutil.which("g++"), "g++ is required for the firmware host regression")
    def test_ack_identity_tokens_match_exact_numeric_values(self):
        repository = Path(__file__).resolve().parents[2]
        header_dir = repository / "button_capture"
        source = r"""
#include "metadata_match.h"

int main() {
  if (!metadataContainsExactToken("{\"capture_seq\":1}", "\"capture_seq\":1")) return 1;
  if (metadataContainsExactToken("{\"capture_seq\":10}", "\"capture_seq\":1")) return 2;
  if (metadataContainsExactToken("{\"boot_id\":1234}", "\"boot_id\":123")) return 3;
  if (!metadataContainsExactToken("{\"node_uid\":\"ABC\",\"capture_seq\":2}",
                                  "\"node_uid\":\"ABC\"")) return 4;
  return 0;
}
"""
        with tempfile.TemporaryDirectory() as temp:
            temp_dir = Path(temp)
            source_path = temp_dir / "metadata_match_test.cpp"
            executable = temp_dir / "metadata_match_test.exe"
            source_path.write_text(source, encoding="utf-8")
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    f"-I{header_dir}",
                    str(source_path),
                    "-o",
                    str(executable),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run([str(executable)], check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
