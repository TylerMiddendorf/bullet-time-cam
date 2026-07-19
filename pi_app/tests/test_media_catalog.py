import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from pi_app.bullettime.media_catalog import (
    delete_catalog_entry,
    load_catalog_animation,
    scan_capture_catalog,
)


def published_capture(
    root: Path, capture_id: str, *, partial: bool = False, preview: bool = True
) -> Path:
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
    files = [{"path": animation.name, "role": "animation"}]
    if preview:
        preview_path = directory / "library_preview.jpg"
        frames[0].copy().save(preview_path, "JPEG", quality=72)
        files.append({"path": preview_path.name, "role": "library_preview"})
    manifest = {
        "schema_version": 2,
        "capture_id": capture_id,
        "status": "partial" if partial else "complete",
        "cameras": cameras,
        "files": files,
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
            self.assertTrue(catalog.entries[1].thumbnail_bytes.startswith(b"\xff\xd8\xff"))
            self.assertEqual(catalog.entries[1].thumbnail_mime, "image/jpeg")

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

    def test_only_initially_visible_entries_decode_eager_thumbnails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index in range(8):
                published_capture(root, f"20260718T12{index:02d}00Z_capture{index}", preview=False)

            catalog = scan_capture_catalog(root)

            self.assertEqual(len(catalog.entries), 8)
            self.assertTrue(all(entry.thumbnail_bytes for entry in catalog.entries[:6]))
            self.assertTrue(all(not entry.thumbnail_bytes for entry in catalog.entries[6:]))
            self.assertEqual(catalog.skipped_count, 0)

    def test_capture_time_previews_load_for_the_entire_catalog_without_gif_decode(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index in range(12):
                published_capture(root, f"capture-{index:02d}")

            with patch(
                "pi_app.bullettime.media_catalog.Image.open",
                side_effect=AssertionError("catalog should not decode GIFs with previews"),
            ):
                catalog = scan_capture_catalog(root)

            self.assertEqual(len(catalog.entries), 12)
            self.assertTrue(all(entry.thumbnail_bytes for entry in catalog.entries))
            self.assertTrue(all(entry.thumbnail_mime == "image/jpeg" for entry in catalog.entries))

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

    def test_delete_removes_exact_validated_capture_set_and_refresh_excludes_it(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            deleted = published_capture(root, "capture-delete")
            retained = published_capture(root, "capture-retain")
            entry = next(
                item
                for item in scan_capture_catalog(root).entries
                if item.capture_id == "capture-delete"
            )

            delete_catalog_entry(root, entry)

            self.assertFalse(deleted.exists())
            self.assertTrue(retained.is_dir())
            self.assertEqual(
                [item.capture_id for item in scan_capture_catalog(root).entries],
                ["capture-retain"],
            )

    def test_delete_rejects_entry_outside_active_root_or_changed_since_scan(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            active_root = base / "active"
            other_root = base / "other"
            active_root.mkdir()
            other_root.mkdir()
            outside = published_capture(other_root, "outside")
            outside_entry = scan_capture_catalog(other_root).entries[0]

            with self.assertRaisesRegex(ValueError, "outside the active USB library"):
                delete_catalog_entry(active_root, outside_entry)
            self.assertTrue(outside.is_dir())

            changed = published_capture(active_root, "changed")
            changed_entry = scan_capture_catalog(active_root).entries[0]
            (changed / "manifest.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "no longer a valid published capture"):
                delete_catalog_entry(active_root, changed_entry)
            self.assertTrue(changed.is_dir())


if __name__ == "__main__":
    unittest.main()
