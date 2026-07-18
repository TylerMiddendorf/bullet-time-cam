import io
import struct
import unittest

from pi_app.bullettime.protocol import (
    CAPTURE_REQUEST,
    HEADER,
    HEADER_PREFIX,
    IMAGE,
    MAX_METADATA,
    PING,
    VERSION,
    ProtocolError,
    crc32,
    encode_frame,
    read_frame,
)


class ProtocolTests(unittest.TestCase):
    def test_round_trip_binary_payload(self):
        payload = bytes(range(256)) * 17
        frame = read_frame(io.BytesIO(encode_frame(IMAGE, {"capture_seq": 7}, payload)))
        self.assertEqual(frame.message_type, IMAGE)
        self.assertEqual(frame.metadata["capture_seq"], 7)
        self.assertEqual(frame.payload, payload)

    def test_payload_progress_reports_bounded_chunk_delivery(self):
        payload = b"x" * (150 * 1024)
        observations = []
        frame = read_frame(
            io.BytesIO(encode_frame(IMAGE, {"node_uid": "node-a"}, payload)),
            payload_progress=lambda metadata, received, total: observations.append(
                (metadata["node_uid"], received, total)
            ),
        )
        self.assertEqual(frame.payload, payload)
        self.assertEqual([item[1] for item in observations], [65536, 131072, len(payload)])
        self.assertTrue(all(item[2] == len(payload) for item in observations))

    def test_resynchronizes_after_text(self):
        stream = io.BytesIO(b"startup diagnostics\n" + encode_frame(IMAGE, {}, b"jpeg"))
        self.assertEqual(read_frame(stream).payload, b"jpeg")

    def test_rejects_corrupt_payload(self):
        encoded = bytearray(encode_frame(IMAGE, {}, b"jpeg"))
        encoded[-1] ^= 1
        with self.assertRaises(ProtocolError):
            read_frame(io.BytesIO(encoded))

    def test_can_return_corrupt_payload_for_receiver_nack(self):
        encoded = bytearray(encode_frame(IMAGE, {"capture_seq": 8}, b"jpeg"))
        encoded[-1] ^= 1
        frame = read_frame(io.BytesIO(encoded), validate_payload_crc=False)
        self.assertEqual(frame.metadata["capture_seq"], 8)
        self.assertNotEqual(frame.payload, b"jpeg")

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

    def test_rejects_unsupported_version_even_with_valid_header_crc(self):
        encoded = bytearray(encode_frame(PING, {}))
        encoded[4] = VERSION + 1
        encoded[HEADER_PREFIX.size : HEADER.size] = struct.pack(
            "<I", crc32(encoded[: HEADER_PREFIX.size])
        )
        with self.assertRaisesRegex(ProtocolError, "unsupported header"):
            read_frame(io.BytesIO(encoded))

    def test_rejects_invalid_metadata_json_with_valid_crc(self):
        metadata = b"not-json"
        prefix = HEADER_PREFIX.pack(b"BTC1", VERSION, PING, 0, len(metadata), 0, crc32(metadata), 0)
        encoded = prefix + struct.pack("<I", crc32(prefix)) + metadata
        with self.assertRaisesRegex(ProtocolError, "invalid metadata JSON"):
            read_frame(io.BytesIO(encoded))

    def test_encode_rejects_metadata_over_limit(self):
        with self.assertRaisesRegex(ProtocolError, "configured limits"):
            encode_frame(PING, {"value": "x" * MAX_METADATA})

    def test_reads_concatenated_frames_without_losing_boundaries(self):
        stream = io.BytesIO(encode_frame(PING, {"index": 1}) + encode_frame(PING, {"index": 2}))
        self.assertEqual(read_frame(stream).metadata["index"], 1)
        self.assertEqual(read_frame(stream).metadata["index"], 2)


if __name__ == "__main__":
    unittest.main()
