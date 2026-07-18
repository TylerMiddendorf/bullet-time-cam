import unittest

from pi_app.bullettime.coordinator import CaptureSetCoordinator, CoordinationError

UIDS = {f"UID-{camera_id}": camera_id for camera_id in range(1, 5)}


def metadata(camera_id, sequence=1, boot="boot-a"):
    return {
        "node_uid": f"UID-{camera_id}",
        "boot_id": f"{boot}-{camera_id}",
        "capture_seq": sequence,
    }


class CaptureSetCoordinatorTests(unittest.TestCase):
    def coordinator(self):
        capture_ids = iter(["capture-a", "capture-b", "capture-c"])
        return CaptureSetCoordinator(
            UIDS,
            association_window_ms=100,
            no_progress_timeout_ms=500,
            capture_id_factory=lambda: next(capture_ids),
        )

    def test_groups_shuffled_four_camera_results(self):
        coordinator = self.coordinator()
        for offset, camera_id in enumerate((3, 1, 4, 2)):
            self.assertEqual(
                coordinator.start(metadata(camera_id), offset * 1_000_000), "capture-a"
            )
        for offset, camera_id in enumerate((2, 4, 1, 3), start=10):
            coordinator.complete(
                metadata(camera_id), f"jpeg-{camera_id}".encode(), offset * 1_000_000
            )

        self.assertTrue(coordinator.ready())
        result = coordinator.finalize(20_000_000)
        self.assertEqual(set(result.images), {1, 2, 3, 4})
        self.assertFalse(result.partial)
        self.assertTrue(coordinator.trigger_allowed)

    def test_timeout_preserves_successes_and_identifies_missing_camera(self):
        coordinator = self.coordinator()
        for camera_id in (1, 2, 3):
            coordinator.start(metadata(camera_id), camera_id * 1_000_000)
            coordinator.complete(metadata(camera_id), b"jpeg", (camera_id + 10) * 1_000_000)

        self.assertFalse(coordinator.ready())
        self.assertTrue(coordinator.timed_out(600_000_000))
        result = coordinator.finalize(600_000_000)
        self.assertEqual(set(result.images), {1, 2, 3})
        self.assertEqual(result.errors[4].code, "no_progress_timeout")

    def test_payload_progress_refreshes_timeout_for_active_transaction(self):
        coordinator = self.coordinator()
        coordinator.start(metadata(1), 0)
        coordinator.progress(metadata(1), 400_000_000)
        self.assertFalse(coordinator.timed_out(800_000_000))
        self.assertTrue(coordinator.timed_out(901_000_000))

    def test_explicit_transfer_failure_closes_a_usable_partial_set(self):
        coordinator = self.coordinator()
        for camera_id in range(1, 5):
            coordinator.start(metadata(camera_id), camera_id * 1_000_000)
        for camera_id in (1, 3, 4):
            coordinator.complete(metadata(camera_id), b"jpeg", (camera_id + 10) * 1_000_000)
        coordinator.fail(
            metadata(2),
            "jpeg_checksum_mismatch",
            "computed checksum did not match metadata",
            20_000_000,
        )

        self.assertTrue(coordinator.ready())
        result = coordinator.finalize(21_000_000)
        self.assertEqual(set(result.images), {1, 3, 4})
        self.assertEqual(result.errors[2].code, "jpeg_checksum_mismatch")

    def test_rejects_second_trigger_late_arrival_and_cross_set_reuse(self):
        coordinator = self.coordinator()
        coordinator.start(metadata(1), 0)
        with self.assertRaisesRegex(CoordinationError, "second capture"):
            coordinator.start(metadata(1, sequence=2), 1_000_000)
        with self.assertRaisesRegex(CoordinationError, "association window"):
            coordinator.start(metadata(2), 200_000_000)

        coordinator.complete(metadata(1), b"jpeg", 2_000_000)
        coordinator.finalize(600_000_000)
        with self.assertRaisesRegex(CoordinationError, "duplicate completed transaction"):
            coordinator.start(metadata(1), 700_000_000)

    def test_node_reboot_keeps_logical_identity_with_a_new_transaction(self):
        coordinator = self.coordinator()
        for camera_id in range(1, 5):
            coordinator.start(metadata(camera_id), camera_id)
            coordinator.complete(metadata(camera_id), b"jpeg", camera_id + 10)
        coordinator.finalize(20)

        for camera_id in range(1, 5):
            reboot = metadata(camera_id, sequence=1, boot="boot-b")
            coordinator.start(reboot, 1_000 + camera_id)
            coordinator.complete(reboot, b"jpeg", 2_000 + camera_id)
        result = coordinator.finalize(3_000)
        self.assertEqual(result.images[4].logical_camera_id, 4)
        self.assertEqual(result.images[4].boot_id, "boot-b-4")


if __name__ == "__main__":
    unittest.main()
