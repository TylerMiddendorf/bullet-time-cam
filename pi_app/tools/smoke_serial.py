"""Bounded serial startup smoke test for the connected camera node."""

import argparse
import time

import serial


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="/dev/ttyACM0")
    parser.add_argument("--seconds", type=float, default=15)
    args = parser.parse_args()
    markers = [b"Camera ready: 2048x1536 JPEG", b"microSD ready:", b"Ready. Pull the shared trigger LOW"]
    collected = bytearray()
    with serial.Serial(args.port, 115200, timeout=0.2) as stream:
        stream.dtr = False
        stream.rts = True
        time.sleep(0.1)
        stream.rts = False
        deadline = time.monotonic() + args.seconds
        while time.monotonic() < deadline and not all(marker in collected for marker in markers):
            collected.extend(stream.read(4096))
    text = collected.decode("utf-8", errors="replace")
    print(text)
    missing = [marker.decode() for marker in markers if marker not in collected]
    if missing:
        raise SystemExit("Missing startup markers: " + ", ".join(missing))
    if b"Stopped." in collected:
        raise SystemExit("Firmware entered stopped state")
    print("Startup verification passed: camera, microSD, and trigger ready.")


if __name__ == "__main__":
    main()
