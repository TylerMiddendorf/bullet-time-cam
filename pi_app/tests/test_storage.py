import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from pi_app.bullettime.storage import (
    StorageUnavailable,
    UsbMount,
    UsbStorageResolver,
    atomic_json,
    commit_capture,
    discover_usb_mounts,
)


class UsbStorageResolverTests(unittest.TestCase):
    def mount(self, path: Path, name: str = "MEDIA") -> UsbMount:
        mountpoint = path / name
        mountpoint.mkdir()
        return UsbMount(mountpoint, "/dev/sda1", "exfat", "8:1")

    def test_selects_usb_mount_and_creates_capture_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            mount = self.mount(Path(temp))
            resolver = UsbStorageResolver(
                capture_directory="BulletTime/Captures",
                auto_mount=False,
                mount_discovery=lambda: [mount],
            )
            root = resolver.resolve()
            self.assertEqual(root, mount.mountpoint / "BulletTime" / "Captures")
            self.assertTrue(root.is_dir())
            self.assertEqual(resolver.manifest_details()["transport"], "usb")

    def test_preferred_mount_name_wins_when_multiple_drives_exist(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            first = self.mount(parent, "ARCHIVE")
            preferred = self.mount(parent, "CAMERA_MEDIA")
            resolver = UsbStorageResolver(
                preferred_mount_name="CAMERA_MEDIA",
                auto_mount=False,
                mount_discovery=lambda: [first, preferred],
            )
            self.assertEqual(resolver.resolve(), preferred.mountpoint / "BulletTime")

    def test_automatic_mount_rescans_before_failing(self):
        with tempfile.TemporaryDirectory() as temp:
            mount = self.mount(Path(temp))
            scans = iter([[], [mount]])
            mount_calls = []
            resolver = UsbStorageResolver(
                mount_discovery=lambda: next(scans),
                automounter=lambda: mount_calls.append(True) or [],
            )
            self.assertEqual(resolver.resolve(), mount.mountpoint / "BulletTime")
            self.assertEqual(mount_calls, [True])

    def test_missing_drive_does_not_fall_back_to_boot_storage(self):
        resolver = UsbStorageResolver(auto_mount=False, mount_discovery=lambda: [])
        with self.assertRaisesRegex(StorageUnavailable, "No writable USB storage"):
            resolver.resolve()
        self.assertEqual(resolver.manifest_details(), {"transport": "usb", "available": False})

    def test_rejects_capture_directory_escape(self):
        with self.assertRaises(ValueError):
            UsbStorageResolver(capture_directory="../captures")

    def test_mountinfo_parser_keeps_only_writable_usb_filesystems(self):
        with tempfile.TemporaryDirectory() as temp:
            mountinfo = Path(temp) / "mountinfo"
            mountinfo.write_text(
                "36 25 8:1 / /media/user/CAMERA\\040MEDIA rw,nosuid,nodev - exfat /dev/sda1 rw\n"
                "37 25 179:2 / / rw,relatime - ext4 /dev/mmcblk0p2 rw\n"
                "38 25 8:2 / /media/user/READONLY ro,nosuid,nodev - exfat /dev/sdb1 ro\n",
                encoding="utf-8",
            )
            with patch(
                "pi_app.bullettime.storage.is_usb_block_device",
                side_effect=lambda major_minor, _sysfs: major_minor.startswith("8:"),
            ):
                mounts = discover_usb_mounts(mountinfo, Path("unused"))
            self.assertEqual(len(mounts), 1)
            self.assertEqual(mounts[0].mountpoint, Path("/media/user/CAMERA MEDIA"))
            self.assertEqual(mounts[0].source, "/dev/sda1")


class AtomicPersistenceTests(unittest.TestCase):
    def jpeg(self) -> bytes:
        output = io.BytesIO()
        Image.new("RGB", (8, 6), "navy").save(output, "JPEG")
        return output.getvalue()

    def test_commit_capture_exposes_only_a_complete_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path, manifest = commit_capture(
                root,
                {"node_uid": "UID-1", "capture_seq": 1},
                self.jpeg(),
                {"storage": {"transport": "usb"}},
            )

            self.assertTrue(path.is_file())
            self.assertEqual(json.loads((path.parent / "manifest.json").read_text()), manifest)
            self.assertEqual([item.name for item in root.iterdir()], [manifest["capture_id"]])
            self.assertFalse(any(root.rglob("*.part")))

    def test_atomic_json_preserves_old_value_and_removes_partial_on_replace_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            path.write_text('{"status":"old"}', encoding="utf-8")
            with patch("pi_app.bullettime.storage.os.replace", side_effect=OSError("full")):
                with self.assertRaisesRegex(OSError, "full"):
                    atomic_json(path, {"status": "new"})

            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"status": "old"})
            self.assertFalse(path.with_suffix(".json.part").exists())

    def test_failed_commit_does_not_publish_a_capture_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch("pi_app.bullettime.storage.atomic_json", side_effect=OSError("removed")):
                with self.assertRaisesRegex(OSError, "removed"):
                    commit_capture(root, {"node_uid": "UID-1"}, self.jpeg(), {})

            self.assertEqual(list(root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
