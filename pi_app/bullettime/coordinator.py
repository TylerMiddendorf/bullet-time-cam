"""Deterministic four-node capture association and completion policy."""

from __future__ import annotations

import time
import uuid
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field


class CoordinationError(RuntimeError):
    """Raised when node events cannot safely belong to the active capture."""


@dataclass(frozen=True)
class CapturedImage:
    logical_camera_id: int
    node_uid: str
    boot_id: str
    capture_seq: int
    payload: bytes
    metadata: dict

    @property
    def transaction(self) -> tuple[str, str, int]:
        return self.node_uid, self.boot_id, self.capture_seq


@dataclass(frozen=True)
class CameraFailure:
    logical_camera_id: int
    code: str
    message: str


@dataclass
class CompletedCapture:
    capture_id: str
    first_started_ns: int
    completed_ns: int
    images: dict[int, CapturedImage]
    errors: dict[int, CameraFailure]
    transactions: dict[int, tuple[str, str, int]]

    @property
    def partial(self) -> bool:
        return bool(self.errors)


@dataclass
class _ActiveCapture:
    capture_id: str
    first_started_ns: int
    last_progress_ns: int
    transactions: dict[int, tuple[str, str, int]] = field(default_factory=dict)
    images: dict[int, CapturedImage] = field(default_factory=dict)
    errors: dict[int, CameraFailure] = field(default_factory=dict)


class CaptureSetCoordinator:
    """Group asynchronous node events without relying on arrival order."""

    def __init__(
        self,
        logical_cameras: dict[str, int],
        *,
        association_window_ms: int = 1000,
        no_progress_timeout_ms: int = 5000,
        capture_id_factory: Callable[[], str] | None = None,
        history_limit: int = 1024,
    ) -> None:
        camera_ids = set(logical_cameras.values())
        if not logical_cameras or len(camera_ids) != len(logical_cameras):
            raise ValueError("logical camera mapping must contain unique IDs")
        if association_window_ms <= 0 or no_progress_timeout_ms <= 0:
            raise ValueError("capture windows must be positive")
        self.logical_cameras = dict(logical_cameras)
        self.expected_camera_ids = frozenset(camera_ids)
        self.association_window_ns = association_window_ms * 1_000_000
        self.no_progress_timeout_ns = no_progress_timeout_ms * 1_000_000
        self._capture_id_factory = capture_id_factory or self._new_capture_id
        self._active: _ActiveCapture | None = None
        self._seen_order: deque[tuple[str, str, int]] = deque(maxlen=history_limit)
        self._seen: set[tuple[str, str, int]] = set()

    @staticmethod
    def _new_capture_id() -> str:
        return f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}_{uuid.uuid4().hex[:8]}"

    @property
    def active_capture_id(self) -> str | None:
        return self._active.capture_id if self._active else None

    @property
    def trigger_allowed(self) -> bool:
        return self._active is None

    def _identity(self, metadata: dict) -> tuple[int, tuple[str, str, int]]:
        uid = str(metadata.get("node_uid", ""))
        try:
            camera_id = self.logical_cameras[uid]
            transaction = (uid, str(metadata["boot_id"]), int(metadata["capture_seq"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise CoordinationError("node event has an unknown or invalid identity") from exc
        return camera_id, transaction

    def start(self, metadata: dict, now_ns: int) -> str:
        camera_id, transaction = self._identity(metadata)
        if transaction in self._seen:
            raise CoordinationError(f"duplicate completed transaction {transaction}")
        if self._active is None:
            self._active = _ActiveCapture(
                capture_id=self._capture_id_factory(),
                first_started_ns=now_ns,
                last_progress_ns=now_ns,
            )
        active = self._active
        if now_ns - active.first_started_ns > self.association_window_ns:
            raise CoordinationError("capture start arrived outside the association window")
        existing = active.transactions.get(camera_id)
        if existing is not None and existing != transaction:
            raise CoordinationError(f"Camera {camera_id} started a second capture while busy")
        if transaction in active.transactions.values() and existing != transaction:
            raise CoordinationError(f"transaction {transaction} is assigned to two cameras")
        active.transactions[camera_id] = transaction
        active.last_progress_ns = now_ns
        return active.capture_id

    def complete(self, metadata: dict, payload: bytes, now_ns: int) -> None:
        camera_id, transaction = self._identity(metadata)
        active = self._require_matching(camera_id, transaction)
        if camera_id in active.images:
            raise CoordinationError(f"Camera {camera_id} completed twice")
        active.images[camera_id] = CapturedImage(
            logical_camera_id=camera_id,
            node_uid=transaction[0],
            boot_id=transaction[1],
            capture_seq=transaction[2],
            payload=payload,
            metadata=dict(metadata),
        )
        active.last_progress_ns = now_ns

    def progress(self, metadata: dict, now_ns: int) -> None:
        """Refresh the no-progress clock for a matching in-flight transaction."""
        camera_id, transaction = self._identity(metadata)
        active = self._require_matching(camera_id, transaction)
        if camera_id in active.images or camera_id in active.errors:
            raise CoordinationError(f"Camera {camera_id} reported progress after resolution")
        active.last_progress_ns = now_ns

    def fail(self, metadata: dict, code: str, message: str, now_ns: int) -> None:
        camera_id, transaction = self._identity(metadata)
        active = self._require_matching(camera_id, transaction)
        if camera_id in active.images:
            raise CoordinationError(f"Camera {camera_id} failed after completing")
        active.errors[camera_id] = CameraFailure(camera_id, code, message)
        active.last_progress_ns = now_ns

    def _require_matching(
        self, camera_id: int, transaction: tuple[str, str, int]
    ) -> _ActiveCapture:
        if self._active is None:
            raise CoordinationError("node result arrived without an active capture")
        if self._active.transactions.get(camera_id) != transaction:
            raise CoordinationError(f"Camera {camera_id} result does not match its capture start")
        return self._active

    def ready(self) -> bool:
        if self._active is None:
            return False
        resolved = set(self._active.images) | set(self._active.errors)
        return resolved == set(self.expected_camera_ids)

    def timed_out(self, now_ns: int) -> bool:
        return bool(
            self._active and now_ns - self._active.last_progress_ns >= self.no_progress_timeout_ns
        )

    def finalize(self, now_ns: int, *, force: bool = False) -> CompletedCapture:
        if self._active is None:
            raise CoordinationError("no active capture to finalize")
        if not force and not self.ready() and not self.timed_out(now_ns):
            raise CoordinationError("capture is still making progress")
        active = self._active
        for camera_id in self.expected_camera_ids - set(active.images) - set(active.errors):
            active.errors[camera_id] = CameraFailure(
                camera_id,
                "no_progress_timeout",
                f"Camera {camera_id} did not complete before the no-progress timeout",
            )
        result = CompletedCapture(
            capture_id=active.capture_id,
            first_started_ns=active.first_started_ns,
            completed_ns=now_ns,
            images=dict(active.images),
            errors=dict(active.errors),
            transactions=dict(active.transactions),
        )
        for transaction in active.transactions.values():
            if len(self._seen_order) == self._seen_order.maxlen:
                self._seen.discard(self._seen_order[0])
            self._seen_order.append(transaction)
            self._seen.add(transaction)
        self._active = None
        return result
