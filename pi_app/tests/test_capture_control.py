import io
import unittest

from pi_app.bullettime.capture_control import initiate_capture
from pi_app.bullettime.protocol import CAPTURE_REQUEST, read_frame


class FakeTrigger:
    pulse_seconds = 0.1

    def __init__(self):
        self.pulse_count = 0

    def pulse(self):
        self.pulse_count += 1


class FakeStream(io.BytesIO):
    def __init__(self):
        super().__init__()
        self.flush_count = 0

    def flush(self):
        self.flush_count += 1


class CaptureControlTests(unittest.TestCase):
    def test_normal_action_pulses_once_without_usb_request(self):
        stream = FakeStream()
        trigger = FakeTrigger()
        message = initiate_capture(stream, trigger, diagnostic_usb_trigger=False)
        self.assertEqual(trigger.pulse_count, 1)
        self.assertEqual(stream.getvalue(), b"")
        self.assertEqual(stream.flush_count, 0)
        self.assertIn("100 ms", message)

    def test_diagnostic_action_uses_only_usb_request(self):
        stream = FakeStream()
        trigger = FakeTrigger()
        initiate_capture(stream, trigger, diagnostic_usb_trigger=True)
        self.assertEqual(trigger.pulse_count, 0)
        frame = read_frame(io.BytesIO(stream.getvalue()))
        self.assertEqual(frame.message_type, CAPTURE_REQUEST)
        self.assertEqual(frame.metadata["reason"], "explicit_diagnostic_usb_trigger")


if __name__ == "__main__":
    unittest.main()
