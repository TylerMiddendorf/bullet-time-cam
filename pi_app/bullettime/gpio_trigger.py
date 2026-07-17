"""Safe, injectable Raspberry Pi hardware-trigger output."""

from __future__ import annotations

import threading
import time
from typing import Protocol


class GpioBackend(Protocol):
    """Minimal backend used by :class:`HardwareTrigger`."""

    def claim_output(self, pin: int, initial: int) -> None: ...

    def write(self, pin: int, level: int) -> None: ...

    def close(self, pin: int) -> None: ...


class LgpioBackend:
    """Raspberry Pi OS Trixie lgpio character-device backend."""

    def __init__(self, gpiochip: int = 0) -> None:
        try:
            import lgpio
        except ImportError as exc:
            raise RuntimeError(
                "lgpio is unavailable; install the pinned Raspberry Pi OS python3-lgpio package"
            ) from exc
        self._lgpio = lgpio
        self._handle = lgpio.gpiochip_open(gpiochip)
        self._claimed = False

    def claim_output(self, pin: int, initial: int) -> None:
        self._lgpio.gpio_claim_output(self._handle, pin, initial)
        self._claimed = True

    def write(self, pin: int, level: int) -> None:
        self._lgpio.gpio_write(self._handle, pin, level)

    def close(self, pin: int) -> None:
        try:
            if self._claimed:
                self._lgpio.gpio_free(self._handle, pin)
        finally:
            self._claimed = False
            self._lgpio.gpiochip_close(self._handle)


class HardwareTrigger:
    """Own one active-high transistor-control output and keep it fail-safe LOW."""

    def __init__(
        self,
        pin: int,
        pulse_seconds: float,
        backend: GpioBackend | None = None,
        sleep=time.sleep,
    ) -> None:
        if pin < 0:
            raise ValueError("GPIO pin must be non-negative")
        if pulse_seconds <= 0:
            raise ValueError("trigger pulse must be positive")
        self.pin = pin
        self.pulse_seconds = pulse_seconds
        self._backend = backend if backend is not None else LgpioBackend()
        self._sleep = sleep
        self._lock = threading.Lock()
        self._closed = False
        try:
            self._backend.claim_output(self.pin, 0)
            # An explicit write documents and enforces the idle state even if a
            # backend's claim behavior changes.
            self._backend.write(self.pin, 0)
        except Exception:
            try:
                self._backend.close(self.pin)
            finally:
                self._closed = True
            raise

    def pulse(self) -> None:
        with self._lock:
            if self._closed:
                raise RuntimeError("hardware trigger is closed")
            try:
                self._backend.write(self.pin, 1)
                self._sleep(self.pulse_seconds)
            finally:
                self._backend.write(self.pin, 0)

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            try:
                self._backend.write(self.pin, 0)
            finally:
                self._closed = True
                self._backend.close(self.pin)

    def __enter__(self) -> "HardwareTrigger":
        return self

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        self.close()
