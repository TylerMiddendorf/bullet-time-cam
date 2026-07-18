import io
import threading
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from pi_app.bullettime.ui import PresentationState, run_headless


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

        retry_error = state.apply(
            {"state": "ERROR", "message": "/dev/ttyACM0: Device or resource busy"}
        )
        self.assertEqual(retry_error.state, "REVIEW_WITH_ERROR")
        self.assertEqual(retry_error.image, "partial.gif")
        self.assertIn("Camera 4", retry_error.text)
        self.assertNotIn("ttyACM", retry_error.text)

    def test_idle_ready_and_error_events_do_not_discard_latest_review(self):
        state = PresentationState()
        state.apply({"state": "REVIEW", "image": "latest.gif"})
        self.assertEqual(state.apply({"state": "READY"}).image, "latest.gif")
        self.assertEqual(
            state.apply({"state": "ERROR", "message": "Camera disconnected"}).image,
            "latest.gif",
        )


class HeadlessTests(unittest.TestCase):
    def test_bounded_run_exits_after_printing_manifest_despite_queued_errors(self):
        class FakeReceiver:
            def __init__(self, _config, events, _commands, _stop, _trigger, _storage):
                self.events = events
                self.automatic_run_completed = threading.Event()

            def start(self):
                self.events.put(
                    {
                        "state": "REVIEW_WITH_ERROR",
                        "manifest": {"capture_id": "capture-a", "status": "partial"},
                    }
                )
                for _ in range(10):
                    self.events.put({"state": "ERROR", "message": "port busy"})
                self.automatic_run_completed.set()

            def join(self, timeout):
                self.join_timeout = timeout

        output = io.StringIO()
        with (
            patch("pi_app.bullettime.receiver.Receiver", FakeReceiver),
            redirect_stdout(output),
        ):
            run_headless({"trigger_count": 1}, object(), object())

        self.assertEqual(len(output.getvalue().splitlines()), 1)
        self.assertIn('"capture_id": "capture-a"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
