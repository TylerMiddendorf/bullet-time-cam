import io
import unittest

from pi_app.bullettime.protocol import CAPTURE_REQUEST, IMAGE, PING, ProtocolError, encode_frame, read_frame


class ProtocolTests(unittest.TestCase):
    def test_round_trip_binary_payload(self):
        payload = bytes(range(256)) * 17
        frame = read_frame(io.BytesIO(encode_frame(IMAGE, {"capture_seq": 7}, payload)))
        self.assertEqual(frame.message_type, IMAGE)
        self.assertEqual(frame.metadata["capture_seq"], 7)
        self.assertEqual(frame.payload, payload)

    def test_resynchronizes_after_text(self):
        stream = io.BytesIO(b"startup diagnostics\n" + encode_frame(IMAGE, {}, b"jpeg"))
        self.assertEqual(read_frame(stream).payload, b"jpeg")

    def test_rejects_corrupt_payload(self):
        encoded = bytearray(encode_frame(IMAGE, {}, b"jpeg"))
        encoded[-1] ^= 1
        with self.assertRaises(ProtocolError):
            read_frame(io.BytesIO(encoded))

    def test_capture_request_fixture(self):
        frame = read_frame(io.BytesIO(encode_frame(CAPTURE_REQUEST, {"reason": "test"})))
        self.assertEqual(frame.message_type, CAPTURE_REQUEST)
        self.assertEqual(frame.metadata["reason"], "test")

    def test_partial_frame_is_not_idle_timeout(self):
        encoded = encode_frame(IMAGE, {}, b"jpeg")
        with self.assertRaises(ProtocolError):
            read_frame(io.BytesIO(encoded[:-2]))

    def test_ping_fixture(self):
        frame = read_frame(io.BytesIO(encode_frame(PING, {"host": "test"})))
        self.assertEqual(frame.message_type, PING)


if __name__ == "__main__":
    unittest.main()
