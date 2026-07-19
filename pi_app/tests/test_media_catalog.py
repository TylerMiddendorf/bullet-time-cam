import json
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from pi_app.bullettime.media_catalog import (
    load_catalog_animation,
    scan_capture_catalog,
)


def published_capture(root: Path, capture_id: str, *, partial: bool = False) -> Path:
    directory = root / capture_id
    directory.mkdir()
    animation = directory / "bullet_time.gif"
    frames = [Image.new("RGB", (24, 16), color) for color in ("red", "green")]
    frames[0].save(
        animation,
        save_all=True,
        append_images=frames[1:],
        duration=[80, 120],
        loop=0,
    )
    cameras = [
        {"logical_camera_id": camera_id, "status": "complete"}
        for camera_id in range(1, 4 if partial else 5)
    ]
    if partial:
        cameras.append({"logical_camera_id": 4, "status": "error"})
    manifest = {
        "schema_version": 2,
        "capture_id": capture_id,
        "status": "partial" if partial else "complete",
        "cameras": cameras,
        "files": [{"path": animation.name, "role": "animation"}],
    }
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return directory


class MediaCatalogTests(unittest.TestCase):
    def test_catalog_lists_complete_and_partial_published_sets_newest_first(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            published_capture(root, "20260718T120000Z_complete")
            published_capture(root, "20260718T130000Z_partial", partial=True)

            catalog = scan_capture_catalog(root)

            self.assertEqual(catalog.status, "ready")
            self.assertEqual(
                [entry.capture_id for entry in catalog.entries],
                ["20260718T130000Z_partial", "20260718T120000Z_complete"],
            )
            self.assertEqual(catalog.entries[0].status, "partial")
            self.assertEqual(catalog.entries[0].view_count, 3)
            self.assertEqual(catalog.entries[0].failed_camera_ids, (4,))
            self.assertEqual(catalog.entries[1].view_count, 4)
            self.assertTrue(catalog.entries[1].thumbnail_png.startswith(b"\x89PNG"))

    def test_corrupt_missing_and_unreadable_entries_are_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            valid = published_capture(root, "valid")
            self.assertTrue(valid.is_dir())

            malformed = root / "malformed"
            malformed.mkdir()
            (malformed / "manifest.json").write_text("{not-json", encoding="utf-8")

            missing = published_capture(root, "missing")
            (missing / "bullet_time.gif").unlink()

            corrupt = published_capture(root, "corrupt")
            (corrupt / "bullet_time.gif").write_bytes(b"not-an-image")

            staging = root / ".20260718T140000Z_deadbeef.part"
            staging.mkdir()

            catalog = scan_capture_catalog(root)

            self.assertEqual([entry.capture_id for entry in catalog.entries], ["valid"])
            self.assertEqual(catalog.skipped_count, 3)

    def test_empty_catalog_is_ready_and_nonfatal(self):
        with tempfile.TemporaryDirectory() as temp:
            catalog = scan_capture_catalog(Path(temp))
            self.assertEqual(catalog.status, "ready")
            self.assertEqual(catalog.entries, ())
            self.assertEqual(catalog.skipped_count, 0)

    def test_removed_media_is_reported_during_scan_and_open(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "BulletTime"
            root.mkdir()
            published_capture(root, "capture-a")
            entry = scan_capture_catalog(root).entries[0]

            shutil.rmtree(root)

            removed = scan_capture_catalog(root)
            self.assertEqual(removed.status, "removed")
            with self.assertRaises(OSError):
                load_catalog_animation(entry, (800, 480))


if __name__ == "__main__":
    unittest.main()
