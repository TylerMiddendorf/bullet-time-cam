"""Binary-safe BTC1 framing shared by the Pi and ESP32 camera node."""

from __future__ import annotations

import json
import struct
import time
import zlib
from dataclasses import dataclass
from typing import BinaryIO

MAGIC = b"BTC1"
VERSION = 1
HEADER_PREFIX = struct.Struct("<4sBBHIIII")
HEADER = struct.Struct("<4sBBHIIIII")
MAX_METADATA = 4096
MAX_PAYLOAD = 8 * 1024 * 1024

HELLO = 1
CAPTURE_STARTED = 2
IMAGE = 3
TRANSFER_COMPLETE = 4
ERROR = 5
LOG = 6
CAPTURE_REQUEST = 7
ACK = 0x80
NACK = 0x81


class ProtocolError(RuntimeError):
    pass


@dataclass(frozen=True)
class Frame:
    message_type: int
    metadata: dict
    payload: bytes
    flags: int = 0
    payload_started_ns: int | None = None
    payload_completed_ns: int | None = None


def crc32(data: bytes, seed: int = 0) -> int:
    return zlib.crc32(data, seed) & 0xFFFFFFFF


def encode_frame(message_type: int, metadata: dict, payload: bytes = b"", flags: int = 0) -> bytes:
    metadata_bytes = json.dumps(metadata, separators=(",", ":"), sort_keys=True).encode("utf-8")
    if len(metadata_bytes) > MAX_METADATA or len(payload) > MAX_PAYLOAD:
        raise ProtocolError("frame exceeds configured limits")
    prefix = HEADER_PREFIX.pack(
        MAGIC, VERSION, message_type, flags, len(metadata_bytes), len(payload),
        crc32(metadata_bytes), crc32(payload),
    )
    return prefix + struct.pack("<I", crc32(prefix)) + metadata_bytes + payload


def _read_exact(stream: BinaryIO, length: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < length:
        chunk = stream.read(length - len(chunks))
        if not chunk:
            raise ProtocolError(f"partial frame: received {len(chunks)} of {length} bytes")
        chunks.extend(chunk)
    return bytes(chunks)


def _seek_magic(stream: BinaryIO) -> None:
    window = bytearray()
    while True:
        byte = stream.read(1)
        if not byte:
            raise TimeoutError("idle while seeking BTC1 magic")
        window.extend(byte)
        if len(window) > len(MAGIC):
            del window[0]
        if bytes(window) == MAGIC:
            return


def read_frame(stream: BinaryIO) -> Frame:
    _seek_magic(stream)
    rest = _read_exact(stream, HEADER.size - len(MAGIC))
    header = MAGIC + rest
    magic, version, message_type, flags, metadata_len, payload_len, metadata_crc, payload_crc, header_crc = HEADER.unpack(header)
    if magic != MAGIC or version != VERSION:
        raise ProtocolError("unsupported header")
    if crc32(header[: HEADER_PREFIX.size]) != header_crc:
        raise ProtocolError("header CRC mismatch")
    if metadata_len > MAX_METADATA or payload_len > MAX_PAYLOAD:
        raise ProtocolError("declared frame exceeds limits")
    metadata_bytes = _read_exact(stream, metadata_len)
    if crc32(metadata_bytes) != metadata_crc:
        raise ProtocolError("metadata CRC mismatch")
    payload_started_ns = time.monotonic_ns()
    payload = _read_exact(stream, payload_len)
    payload_completed_ns = time.monotonic_ns()
    if crc32(payload) != payload_crc:
        raise ProtocolError("payload CRC mismatch")
    try:
        metadata = json.loads(metadata_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("invalid metadata JSON") from exc
    return Frame(message_type, metadata, payload, flags, payload_started_ns, payload_completed_ns)
