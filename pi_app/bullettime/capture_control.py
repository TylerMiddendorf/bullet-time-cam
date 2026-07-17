"""Selection between the normal hardware trigger and explicit USB diagnostics."""

from __future__ import annotations

import time

from .gpio_trigger import HardwareTrigger
from .protocol import CAPTURE_REQUEST, encode_frame


def initiate_capture(stream, trigger: HardwareTrigger, diagnostic_usb_trigger: bool) -> str:
    """Start exactly one capture using the selected, explicit trigger path."""
    if diagnostic_usb_trigger:
        request = {
            "host": "camerapi",
            "requested_monotonic_ns": time.monotonic_ns(),
            "reason": "explicit_diagnostic_usb_trigger",
        }
        stream.write(encode_frame(CAPTURE_REQUEST, request))
        stream.flush()
        return "Diagnostic USB capture requested..."
    trigger.pulse()
    return f"Hardware trigger pulsed for {int(trigger.pulse_seconds * 1000)} ms..."
