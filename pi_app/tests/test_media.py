import io
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageSequence

from pi_app.bullettime.coordinator import CameraFailure, CapturedImage, CompletedCapture
from pi_app.bullettime.media import animation_sequence, commit_capture_set
from pi_app.evidence.validation import validate_capture

UIDS = {f"UID-{camera_id}": camera_id for camera_id in range(1, 5)}


def jpeg(camera_id):
    output = io.BytesIO()
    Image.new("RGB", (16, 12), (camera_id * 50, 20, 100)).save(output, "JPEG")
    return output.getvalue()


def large_jpeg(camera_id):
    output = io.BytesIO()
    image = Image.new("RGB", (800, 600))
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            pixels[x, y] = (
                (x + camera_id * 31) % 256,
                (y + camera_id * 47) % 256,
                (x + y + camera_id * 59) % 256,
            )
    image.save(output, "JPEG", quality=90)
    return output.getvalue()


def capture(failed=()):
    failed = set(failed)
    images = {
        camera_id: CapturedImage(
            camera_id,
            f"UID-{camera_id}",
            f"boot-{camera_id}",
            1,
            jpeg(camera_id),
            {},
        )
        for camera_id in range(1, 5)
        if camera_id not in failed
    }
    errors = {
        camera_id: CameraFailure(camera_id, "camera_unavailable", "injected")
        for camera_id in failed
    }
    return CompletedCapture("capture-a", 1_000_000, 21_000_000, images, errors, {})


class MediaTests(unittest.TestCase):
    def test_animation_sequence_omits_duplicate_endpoints(self):
        self.assertEqual(animation_sequence([1, 2, 3, 4]), [1, 2, 3, 4, 3, 2])
        self.assertEqual(animation_sequence([1, 3, 4]), [1, 3, 4, 3])
        self.assertEqual(animation_sequence([2]), [2])

    def test_commits_complete_set_and_real_gif_in_camera_order(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            review_path, manifest = commit_capture_set(
                root, capture(), storage={"transport": "usb", "available": True}
            )

            self.assertEqual(review_path.name, "bullet_time.gif")
            self.assertEqual(manifest["status"], "complete")
            self.assertEqual(
                next(item for item in manifest["files"] if item["role"] == "animation")[
                    "camera_sequence"
                ],
                [1, 2, 3, 4, 3, 2],
            )
            with Image.open(review_path) as image:
                self.assertEqual(len(list(ImageSequence.Iterator(image))), 6)
            preview_record = next(
                item for item in manifest["files"] if item["role"] == "library_preview"
            )
            preview_path = review_path.parent / preview_record["path"]
            self.assertTrue(preview_path.is_file())
            with Image.open(preview_path) as preview:
                self.assertEqual(preview.format, "JPEG")
                self.assertLessEqual(preview.width, 240)
                self.assertLessEqual(preview.height, 135)
            self.assertEqual(
                validate_capture(root, "capture-a", UIDS).failed_camera_ids, frozenset()
            )

    def test_commits_partial_set_with_camera_specific_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            review_path, manifest = commit_capture_set(
                root, capture({4}), storage={"transport": "usb"}
            )
            self.assertTrue(review_path.is_file())
            self.assertEqual(manifest["status"], "partial")
            self.assertEqual(manifest["errors"][0]["logical_camera_id"], 4)
            result = validate_capture(root, "capture-a", UIDS)
            self.assertEqual(result.successful_camera_ids, frozenset({1, 2, 3}))
            self.assertEqual(result.failed_camera_ids, frozenset({4}))

    def test_gif_uses_display_fit_palette_frames_with_bounded_fidelity(self):
        captured = capture()
        captured.images = {
            camera_id: CapturedImage(
                camera_id,
                f"UID-{camera_id}",
                f"boot-{camera_id}",
                1,
                large_jpeg(camera_id),
                {},
            )
            for camera_id in range(1, 5)
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            review_path, _ = commit_capture_set(
                root,
                captured,
                storage={"transport": "usb"},
                gif_max_width=640,
            )

            with Image.open(review_path) as image:
                frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(image)]
            self.assertEqual(len(frames), 6)
            self.assertTrue(all(frame.size == (640, 480) for frame in frames))
            self.assertLess(review_path.stat().st_size, 1_500_000)
            self.assertEqual(
                validate_capture(root, "capture-a", UIDS).successful_camera_ids,
                frozenset({1, 2, 3, 4}),
            )


if __name__ == "__main__":
    unittest.main()
