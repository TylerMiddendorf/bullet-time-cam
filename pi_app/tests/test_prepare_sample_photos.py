import tempfile
import unittest
from pathlib import Path

from PIL import Image

from pi_app.tools.prepare_sample_photos import prepare_sample_photos


class PrepareSamplePhotosTests(unittest.TestCase):
    def test_generates_complete_and_camera_four_missing_sets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "photos"
            paths = prepare_sample_photos(root)

            self.assertEqual(len(paths), 27)
            for capture_number in range(1, 7):
                for camera_id in range(1, 5):
                    self.assertTrue(
                        (root / f"cam{camera_id}" / f"photo_{capture_number:04d}.jpg").is_file()
                    )
            self.assertTrue((root / "cam3" / "photo_0007.jpg").is_file())
            self.assertFalse((root / "cam4" / "photo_0007.jpg").exists())
            with Image.open(root / "cam1" / "photo_0001.jpg") as image:
                self.assertEqual(image.size, (800, 600))
                self.assertEqual(image.format, "JPEG")


if __name__ == "__main__":
    unittest.main()
