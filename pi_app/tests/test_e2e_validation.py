import json
import tempfile
import unittest
import zlib
from pathlib import Path

from PIL import Image

from pi_app.evidence.validation import (
    EvidenceValidationError,
    validate_capture,
    validate_scenario_ledger,
)


UIDS = {
    "UID-CAMERA-1": 1,
    "UID-CAMERA-2": 2,
    "UID-CAMERA-3": 3,
    "UID-CAMERA-4": 4,
}


class EvidenceBuilder:
    def __init__(self, root: Path):
        self.root = root
        self.sequence = {camera_id: 0 for camera_id in UIDS.values()}
        self.boot_ids = {camera_id: f"boot-{camera_id}-a" for camera_id in UIDS.values()}

    def reboot(self, camera_id: int):
        self.boot_ids[camera_id] = f"boot-{camera_id}-b"
        self.sequence[camera_id] = 0

    def capture(self, capture_id: str, failed=()):
        failed = set(failed)
        capture_dir = self.root / capture_id
        capture_dir.mkdir()
        cameras = []
        files = []
        frames = []
        for uid, camera_id in UIDS.items():
            if camera_id in failed:
                cameras.append({"logical_camera_id": camera_id, "status": "error"})
                continue
            self.sequence[camera_id] += 1
            name = f"camera_{camera_id:02d}.jpg"
            path = capture_dir / name
            image = Image.new("RGB", (8, 6), (camera_id * 40, 20, 100))
            image.save(path, "JPEG")
            payload = path.read_bytes()
            cameras.append({
                "logical_camera_id": camera_id,
                "node_uid": uid,
                "boot_id": self.boot_ids[camera_id],
                "capture_seq": self.sequence[camera_id],
                "status": "complete",
            })
            files.append({
                "path": name,
                "role": "original",
                "logical_camera_id": camera_id,
                "bytes": len(payload),
                "crc32": f"{zlib.crc32(payload) & 0xFFFFFFFF:08x}",
            })
            frames.append(image)
        if len(frames) >= 2:
            gif_frames = frames + list(reversed(frames[1:-1]))
            gif_path = capture_dir / "bullet_time.gif"
            gif_frames[0].save(
                gif_path,
                save_all=True,
                append_images=gif_frames[1:],
                duration=100,
                loop=0,
                format="GIF",
            )
            gif_payload = gif_path.read_bytes()
            successful_ids = sorted(set(UIDS.values()) - failed)
            files.append({
                "path": "bullet_time.gif",
                "role": "animation",
                "bytes": len(gif_payload),
                "crc32": f"{zlib.crc32(gif_payload) & 0xFFFFFFFF:08x}",
                "frame_count": len(gif_frames),
                "camera_sequence": successful_ids + successful_ids[-2:0:-1],
            })
        manifest = {
            "schema_version": 2,
            "capture_id": capture_id,
            "status": "partial" if failed else "complete",
            "cameras": cameras,
            "files": files,
            "errors": [
                {"logical_camera_id": camera_id, "code": "test_fault", "message": "injected"}
                for camera_id in sorted(failed)
            ],
        }
        (capture_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        return capture_id


class FourNodeEvidenceValidationTests(unittest.TestCase):
    def test_accepts_complete_and_each_single_camera_partial_set(self):
        with tempfile.TemporaryDirectory() as temp:
            builder = EvidenceBuilder(Path(temp))
            complete = builder.capture("complete")
            self.assertEqual(
                validate_capture(Path(temp), complete, UIDS).successful_camera_ids,
                frozenset({1, 2, 3, 4}),
            )
            for camera_id in range(1, 5):
                capture_id = builder.capture(f"missing-{camera_id}", failed={camera_id})
                result = validate_capture(Path(temp), capture_id, UIDS)
                self.assertEqual(result.failed_camera_ids, frozenset({camera_id}))
                self.assertFalse((result.capture_dir / f"camera_{camera_id:02d}.jpg").exists())

    def test_rejects_corrupt_and_truncated_originals(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            builder = EvidenceBuilder(root)
            corrupt_id = builder.capture("corrupt")
            corrupt_path = root / corrupt_id / "camera_02.jpg"
            corrupt_path.write_bytes(corrupt_path.read_bytes()[:-1] + b"x")
            with self.assertRaisesRegex(EvidenceValidationError, "CRC32 mismatch"):
                validate_capture(root, corrupt_id, UIDS)

            truncated_id = builder.capture("truncated")
            truncated_path = root / truncated_id / "camera_03.jpg"
            truncated_path.write_bytes(truncated_path.read_bytes()[:20])
            manifest_path = root / truncated_id / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            record = next(item for item in manifest["files"] if item.get("logical_camera_id") == 3)
            payload = truncated_path.read_bytes()
            record["bytes"] = len(payload)
            record["crc32"] = f"{zlib.crc32(payload) & 0xFFFFFFFF:08x}"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(EvidenceValidationError, "invalid JPEG"):
                validate_capture(root, truncated_id, UIDS)

    def test_rejects_partial_files_wrong_identity_and_duplicate_transaction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            builder = EvidenceBuilder(root)
            partial_id = builder.capture("part-leftover")
            (root / partial_id / "camera_04.jpg.part").write_bytes(b"partial")
            with self.assertRaisesRegex(EvidenceValidationError, "uncommitted partial"):
                validate_capture(root, partial_id, UIDS)

            wrong_id = builder.capture("wrong-identity")
            manifest_path = root / wrong_id / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["cameras"][1]["node_uid"] = "UID-CAMERA-1"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(EvidenceValidationError, "does not map"):
                validate_capture(root, wrong_id, UIDS)

            wrong_animation_id = builder.capture("wrong-animation-order")
            animation_manifest_path = root / wrong_animation_id / "manifest.json"
            animation_manifest = json.loads(
                animation_manifest_path.read_text(encoding="utf-8")
            )
            animation_record = next(
                item for item in animation_manifest["files"] if item.get("role") == "animation"
            )
            animation_record["camera_sequence"] = [1, 3, 2, 4, 2, 3]
            animation_manifest_path.write_text(json.dumps(animation_manifest), encoding="utf-8")
            with self.assertRaisesRegex(EvidenceValidationError, "animation camera sequence"):
                validate_capture(root, wrong_animation_id, UIDS)

    def test_full_ledger_covers_25_normals_disconnects_faults_reboot_and_isolation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            builder = EvidenceBuilder(root)
            normals = [builder.capture(f"normal-{index:02d}") for index in range(25)]
            disconnects = {
                str(camera_id): builder.capture(f"disconnect-{camera_id}", failed={camera_id})
                for camera_id in range(1, 5)
            }
            corrupt = builder.capture("corrupt-transfer", failed={2})
            truncated = builder.capture("truncated-transfer", failed={3})
            before = builder.capture("before-reboot")
            builder.reboot(4)
            after = builder.capture("after-reboot")
            ledger = {
                "schema_version": 1,
                "logical_cameras": UIDS,
                "normal_capture_ids": normals,
                "disconnect_capture_ids": disconnects,
                "corrupt_transfer": {"capture_id": corrupt, "failed_camera_id": 2},
                "truncated_transfer": {"capture_id": truncated, "failed_camera_id": 3},
                "reboot_between_captures": {
                    "before_capture_id": before,
                    "after_capture_id": after,
                    "logical_camera_id": 4,
                    "node_uid": "UID-CAMERA-4",
                },
            }
            ledger_path = root / "ledger.json"
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            result = validate_scenario_ledger(root, ledger_path)
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["normal_capture_count"], 25)
            self.assertEqual(result["capture_count"], 33)
            self.assertEqual(result["partial_capture_count"], 6)

            # Reusing one real transaction in another set must fail the suite,
            # even if both individual manifests and files remain internally valid.
            after_manifest_path = root / after / "manifest.json"
            after_manifest = json.loads(after_manifest_path.read_text(encoding="utf-8"))
            before_manifest = json.loads((root / before / "manifest.json").read_text(encoding="utf-8"))
            after_manifest["cameras"][0]["boot_id"] = before_manifest["cameras"][0]["boot_id"]
            after_manifest["cameras"][0]["capture_seq"] = before_manifest["cameras"][0]["capture_seq"]
            after_manifest_path.write_text(json.dumps(after_manifest), encoding="utf-8")
            with self.assertRaisesRegex(EvidenceValidationError, "appears in both"):
                validate_scenario_ledger(root, ledger_path)


if __name__ == "__main__":
    unittest.main()
