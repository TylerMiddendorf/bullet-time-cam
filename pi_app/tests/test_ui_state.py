import unittest

from pi_app.bullettime.ui import PresentationState


class PresentationStateTests(unittest.TestCase):
    def test_loading_replaces_the_previous_review_and_blocks_idle_preservation(self):
        state = PresentationState()
        state.apply({"state": "REVIEW", "image": "old.gif"})
        loading = state.apply({"state": "LOADING", "message": "Capturing"})
        self.assertIsNone(loading.image)
        self.assertTrue(state.capture_in_progress)

        error = state.apply({"state": "ERROR", "message": "Camera 4 failed"})
        self.assertIsNone(error.image)
        self.assertEqual(error.color, "#ff5050")

    def test_partial_review_keeps_animation_and_camera_error_together(self):
        state = PresentationState()
        state.apply({"state": "LOADING", "message": "Capturing"})
        review = state.apply(
            {
                "state": "REVIEW_WITH_ERROR",
                "image": "partial.gif",
                "message": "Camera 4: no progress timeout",
            }
        )
        self.assertEqual(review.image, "partial.gif")
        self.assertIn("Camera 4", review.text)
        self.assertFalse(state.capture_in_progress)

    def test_idle_ready_and_error_events_do_not_discard_latest_review(self):
        state = PresentationState()
        state.apply({"state": "REVIEW", "image": "latest.gif"})
        self.assertEqual(state.apply({"state": "READY"}).image, "latest.gif")
        self.assertEqual(
            state.apply({"state": "ERROR", "message": "Camera disconnected"}).image,
            "latest.gif",
        )


if __name__ == "__main__":
    unittest.main()
