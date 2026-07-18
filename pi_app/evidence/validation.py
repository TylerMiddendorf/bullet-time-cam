"""Validate four-node V1 end-to-end capture evidence.

The live hardware suite writes a scenario ledger naming the capture sets produced
by each required test.  This module checks both that ledger and the persisted
media so a green result is based on JPEG/GIF bytes and camera identities, not
only process exit codes or log text.
"""

from __future__ import annotations

import json
import math
import zlib
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageSequence, ImageStat

EXPECTED_CAMERA_IDS = frozenset({1, 2, 3, 4})
CAPTURE_SCHEMA_VERSION = 2
LEDGER_SCHEMA_VERSION = 1
MAX_GIF_FRAME_RMS = 25.0


class EvidenceValidationError(AssertionError):
    """Raised when persisted four-node evidence violates the V1 contract."""


@dataclass(frozen=True)
class CaptureEvidence:
    capture_id: str
    capture_dir: Path
    manifest: dict
    successful_camera_ids: frozenset[int]
    failed_camera_ids: frozenset[int]
    transactions: frozenset[tuple[str, str, int]]


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceValidationError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceValidationError(f"{path} must contain a JSON object")
    return value


def _safe_file(capture_dir: Path, relative_name: str) -> Path:
    relative = Path(relative_name)
    if relative.is_absolute() or ".." in relative.parts or relative.name != relative_name:
        raise EvidenceValidationError(f"unsafe capture file path: {relative_name!r}")
    return capture_dir / relative


def _crc32(path: Path) -> str:
    checksum = 0
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                checksum = zlib.crc32(block, checksum)
    except OSError as exc:
        raise EvidenceValidationError(f"cannot read {path}: {exc}") from exc
    return f"{checksum & 0xFFFFFFFF:08x}"


def _frame_rms(actual: Image.Image, expected: Image.Image) -> float:
    """Return a resize-aware RGB difference score for one generated GIF frame."""
    expected_rgb = expected.convert("RGB")
    if expected_rgb.size != actual.size:
        expected_rgb = expected_rgb.resize(actual.size, Image.Resampling.LANCZOS)
    difference = ImageChops.difference(actual.convert("RGB"), expected_rgb)
    channel_rms = ImageStat.Stat(difference).rms
    return math.sqrt(sum(value * value for value in channel_rms) / len(channel_rms))


def validate_capture(
    capture_root: Path, capture_id: str, logical_cameras: dict[str, int]
) -> CaptureEvidence:
    """Validate one complete or deliberately partial four-node capture set."""
    capture_dir = capture_root / capture_id
    manifest_path = capture_dir / "manifest.json"
    manifest = _read_json(manifest_path)
    if manifest.get("schema_version") != CAPTURE_SCHEMA_VERSION:
        raise EvidenceValidationError(
            f"{capture_id}: schema_version must be {CAPTURE_SCHEMA_VERSION}"
        )
    if manifest.get("capture_id") != capture_id:
        raise EvidenceValidationError(
            f"{capture_id}: manifest capture_id is {manifest.get('capture_id')!r}"
        )
    leftovers = sorted(path.name for path in capture_dir.glob("*.part"))
    if leftovers:
        raise EvidenceValidationError(f"{capture_id}: uncommitted partial files: {leftovers}")

    camera_records = manifest.get("cameras")
    if not isinstance(camera_records, list) or len(camera_records) != 4:
        raise EvidenceValidationError(f"{capture_id}: manifest must contain four camera records")

    records_by_id: dict[int, dict] = {}
    transactions: set[tuple[str, str, int]] = set()
    successful: set[int] = set()
    failed: set[int] = set()
    for record in camera_records:
        if not isinstance(record, dict):
            raise EvidenceValidationError(f"{capture_id}: camera record must be an object")
        try:
            camera_id = int(record["logical_camera_id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise EvidenceValidationError(f"{capture_id}: invalid logical camera ID") from exc
        if camera_id not in EXPECTED_CAMERA_IDS or camera_id in records_by_id:
            raise EvidenceValidationError(f"{capture_id}: duplicate/invalid Camera {camera_id}")
        records_by_id[camera_id] = record
        status = record.get("status")
        if status == "complete":
            node_uid = str(record.get("node_uid", ""))
            if logical_cameras.get(node_uid) != camera_id:
                raise EvidenceValidationError(
                    f"{capture_id}: UID {node_uid!r} does not map to Camera {camera_id}"
                )
            try:
                transaction = (
                    node_uid,
                    str(record["boot_id"]),
                    int(record["capture_seq"]),
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise EvidenceValidationError(
                    f"{capture_id}: Camera {camera_id} lacks transaction identity"
                ) from exc
            if transaction in transactions:
                raise EvidenceValidationError(
                    f"{capture_id}: duplicate node transaction {transaction}"
                )
            transactions.add(transaction)
            successful.add(camera_id)
        elif status == "error":
            failed.add(camera_id)
        else:
            raise EvidenceValidationError(
                f"{capture_id}: Camera {camera_id} has invalid status {status!r}"
            )
    if set(records_by_id) != EXPECTED_CAMERA_IDS:
        raise EvidenceValidationError(f"{capture_id}: camera records must cover Cameras 1-4")

    file_records = manifest.get("files")
    if not isinstance(file_records, list):
        raise EvidenceValidationError(f"{capture_id}: manifest files must be a list")
    originals: dict[int, dict] = {}
    animation = None
    for record in file_records:
        if not isinstance(record, dict):
            raise EvidenceValidationError(f"{capture_id}: file record must be an object")
        role = record.get("role")
        if role == "original":
            try:
                camera_id = int(record["logical_camera_id"])
            except (KeyError, TypeError, ValueError) as exc:
                raise EvidenceValidationError(f"{capture_id}: original lacks camera ID") from exc
            if camera_id in originals:
                raise EvidenceValidationError(
                    f"{capture_id}: duplicate Camera {camera_id} original"
                )
            originals[camera_id] = record
        elif role == "animation":
            if animation is not None:
                raise EvidenceValidationError(f"{capture_id}: multiple animations recorded")
            animation = record
        else:
            raise EvidenceValidationError(f"{capture_id}: unsupported file role {role!r}")

    if set(originals) != successful:
        raise EvidenceValidationError(
            f"{capture_id}: committed originals {sorted(originals)} do not match successful cameras "
            f"{sorted(successful)}"
        )
    original_images: dict[int, Image.Image] = {}
    for camera_id, record in originals.items():
        expected_name = f"camera_{camera_id:02d}.jpg"
        if record.get("path") != expected_name:
            raise EvidenceValidationError(
                f"{capture_id}: Camera {camera_id} path must be {expected_name}"
            )
        path = _safe_file(capture_dir, expected_name)
        try:
            size = path.stat().st_size
        except OSError as exc:
            raise EvidenceValidationError(f"{capture_id}: missing {expected_name}") from exc
        if record.get("bytes") != size:
            raise EvidenceValidationError(f"{capture_id}: byte count mismatch for {expected_name}")
        if str(record.get("crc32", "")).lower() != _crc32(path):
            raise EvidenceValidationError(f"{capture_id}: CRC32 mismatch for {expected_name}")
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                original_images[camera_id] = image.convert("RGB").copy()
        except Exception as exc:
            raise EvidenceValidationError(
                f"{capture_id}: invalid JPEG {expected_name}: {exc}"
            ) from exc

    if len(successful) >= 2:
        if not isinstance(animation, dict) or animation.get("path") != "bullet_time.gif":
            raise EvidenceValidationError(f"{capture_id}: usable set lacks bullet_time.gif")
        gif_path = _safe_file(capture_dir, "bullet_time.gif")
        ordered_cameras = sorted(successful)
        expected_sequence = ordered_cameras + ordered_cameras[-2:0:-1]
        if animation.get("camera_sequence") != expected_sequence:
            raise EvidenceValidationError(
                f"{capture_id}: animation camera sequence must be {expected_sequence}"
            )
        try:
            gif_size = gif_path.stat().st_size
        except OSError as exc:
            raise EvidenceValidationError(f"{capture_id}: missing bullet_time.gif") from exc
        if animation.get("bytes") != gif_size:
            raise EvidenceValidationError(f"{capture_id}: animation byte count mismatch")
        if str(animation.get("crc32", "")).lower() != _crc32(gif_path):
            raise EvidenceValidationError(f"{capture_id}: animation CRC32 mismatch")
        try:
            with Image.open(gif_path) as image:
                frame_count = getattr(image, "n_frames", 1)
                if image.format != "GIF" or frame_count != len(expected_sequence):
                    raise EvidenceValidationError(
                        f"{capture_id}: animation frame count does not match camera sequence"
                    )
                if animation.get("frame_count") != frame_count:
                    raise EvidenceValidationError(
                        f"{capture_id}: recorded GIF frame count mismatch"
                    )
                actual_frames = [
                    frame.convert("RGB").copy() for frame in ImageSequence.Iterator(image)
                ]
            for frame_index, (frame, camera_id) in enumerate(
                zip(actual_frames, expected_sequence, strict=True)
            ):
                score = _frame_rms(frame, original_images[camera_id])
                if score > MAX_GIF_FRAME_RMS:
                    raise EvidenceValidationError(
                        f"{capture_id}: GIF frame {frame_index} does not match Camera {camera_id} "
                        f"(RMS {score:.2f})"
                    )
        except EvidenceValidationError:
            raise
        except Exception as exc:
            raise EvidenceValidationError(f"{capture_id}: invalid animation: {exc}") from exc
    elif animation is not None:
        raise EvidenceValidationError(f"{capture_id}: animation requires at least two cameras")

    error_ids = set()
    for error in manifest.get("errors", []):
        if isinstance(error, dict) and "logical_camera_id" in error:
            camera_id = int(error["logical_camera_id"])
            if camera_id in error_ids:
                raise EvidenceValidationError(
                    f"{capture_id}: duplicate error record for Camera {camera_id}"
                )
            error_ids.add(camera_id)
    if error_ids != failed:
        raise EvidenceValidationError(
            f"{capture_id}: error cameras {sorted(error_ids)} do not match failed cameras {sorted(failed)}"
        )
    expected_status = "complete" if not failed else "partial"
    if manifest.get("status") != expected_status:
        raise EvidenceValidationError(
            f"{capture_id}: status must be {expected_status!r}, got {manifest.get('status')!r}"
        )

    return CaptureEvidence(
        capture_id=capture_id,
        capture_dir=capture_dir,
        manifest=manifest,
        successful_camera_ids=frozenset(successful),
        failed_camera_ids=frozenset(failed),
        transactions=frozenset(transactions),
    )


def validate_scenario_ledger(capture_root: Path, ledger_path: Path) -> dict:
    """Validate all Checkpoint 5 live scenarios named by a hardware-run ledger."""
    ledger = _read_json(ledger_path)
    if ledger.get("schema_version") != LEDGER_SCHEMA_VERSION:
        raise EvidenceValidationError(f"ledger schema_version must be {LEDGER_SCHEMA_VERSION}")
    mappings = ledger.get("logical_cameras")
    if (
        not isinstance(mappings, dict)
        or len(mappings) != len(EXPECTED_CAMERA_IDS)
        or set(mappings.values()) != EXPECTED_CAMERA_IDS
    ):
        raise EvidenceValidationError("ledger logical_cameras must map four UIDs to Cameras 1-4")

    normal_ids = ledger.get("normal_capture_ids")
    if not isinstance(normal_ids, list) or len(normal_ids) < 25:
        raise EvidenceValidationError("ledger must name at least 25 normal captures")
    scenario_ids: list[str] = [str(value) for value in normal_ids]

    disconnects = ledger.get("disconnect_capture_ids")
    if not isinstance(disconnects, dict) or set(disconnects) != {"1", "2", "3", "4"}:
        raise EvidenceValidationError("ledger must name one disconnect capture for every camera")
    scenario_ids.extend(str(value) for value in disconnects.values())

    for name in ("corrupt_transfer", "truncated_transfer"):
        scenario = ledger.get(name)
        if (
            not isinstance(scenario, dict)
            or "capture_id" not in scenario
            or "failed_camera_id" not in scenario
            or "error_code" not in scenario
            or "recovery_capture_id" not in scenario
        ):
            raise EvidenceValidationError(f"ledger lacks {name} capture/failure/recovery details")
        scenario_ids.extend([str(scenario["capture_id"]), str(scenario["recovery_capture_id"])])

    reboot = ledger.get("reboot_between_captures")
    if not isinstance(reboot, dict):
        raise EvidenceValidationError("ledger lacks reboot_between_captures details")
    for field in ("before_capture_id", "after_capture_id", "logical_camera_id", "node_uid"):
        if field not in reboot:
            raise EvidenceValidationError(f"reboot scenario lacks {field}")
    scenario_ids.extend([str(reboot["before_capture_id"]), str(reboot["after_capture_id"])])

    if len(scenario_ids) != len(set(scenario_ids)):
        raise EvidenceValidationError("one capture ID is assigned to multiple E2E scenarios")

    evidence = {
        capture_id: validate_capture(capture_root, capture_id, mappings)
        for capture_id in scenario_ids
    }
    for capture_id in normal_ids:
        item = evidence[str(capture_id)]
        if item.successful_camera_ids != EXPECTED_CAMERA_IDS or item.failed_camera_ids:
            raise EvidenceValidationError(
                f"{capture_id}: normal capture is not a complete four-node set"
            )
    for camera_text, capture_id in disconnects.items():
        expected_failure = {int(camera_text)}
        if evidence[str(capture_id)].failed_camera_ids != expected_failure:
            raise EvidenceValidationError(
                f"{capture_id}: disconnect case must fail only Camera {camera_text}"
            )
    for name in ("corrupt_transfer", "truncated_transfer"):
        scenario = ledger[name]
        expected_failure = {int(scenario["failed_camera_id"])}
        failed_capture = evidence[str(scenario["capture_id"])]
        if failed_capture.failed_camera_ids != expected_failure:
            raise EvidenceValidationError(f"{name}: wrong failed camera")
        failed_camera_id = next(iter(expected_failure))
        error = next(
            item
            for item in failed_capture.manifest["errors"]
            if int(item["logical_camera_id"]) == failed_camera_id
        )
        if error.get("code") != scenario["error_code"]:
            raise EvidenceValidationError(f"{name}: wrong camera error code")
        recovery = evidence[str(scenario["recovery_capture_id"])]
        if recovery.successful_camera_ids != EXPECTED_CAMERA_IDS or recovery.failed_camera_ids:
            raise EvidenceValidationError(f"{name}: recovery capture is not complete")

    camera_id = int(reboot["logical_camera_id"])
    uid = str(reboot["node_uid"])
    if mappings.get(uid) != camera_id:
        raise EvidenceValidationError("reboot scenario UID does not match its logical camera")
    before_records = evidence[str(reboot["before_capture_id"])].manifest["cameras"]
    after_records = evidence[str(reboot["after_capture_id"])].manifest["cameras"]
    before = next(
        record for record in before_records if int(record["logical_camera_id"]) == camera_id
    )
    after = next(
        record for record in after_records if int(record["logical_camera_id"]) == camera_id
    )
    if before.get("node_uid") != uid or after.get("node_uid") != uid:
        raise EvidenceValidationError("reboot changed the camera UID/logical assignment")
    if str(before.get("boot_id")) == str(after.get("boot_id")):
        raise EvidenceValidationError("reboot scenario did not record a changed boot_id")

    seen_transactions: dict[tuple[str, str, int], str] = {}
    for capture_id, item in evidence.items():
        for transaction in item.transactions:
            if transaction in seen_transactions:
                raise EvidenceValidationError(
                    f"node transaction {transaction} appears in both "
                    f"{seen_transactions[transaction]} and {capture_id}"
                )
            seen_transactions[transaction] = capture_id

    return {
        "capture_count": len(evidence),
        "normal_capture_count": len(normal_ids),
        "partial_capture_count": sum(bool(item.failed_camera_ids) for item in evidence.values()),
        "camera_ids": sorted(EXPECTED_CAMERA_IDS),
        "status": "pass",
    }
