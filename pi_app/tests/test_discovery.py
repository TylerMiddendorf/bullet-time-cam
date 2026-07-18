import unittest
from unittest.mock import patch

from pi_app.bullettime.discovery import discover_ports


class DiscoveryTests(unittest.TestCase):
    def test_prefers_stable_by_id_order_and_deduplicates_real_devices(self):
        with (
            patch(
                "pi_app.bullettime.discovery.glob.glob",
                side_effect=[
                    ["/dev/serial/by-id/camera-a", "/dev/serial/by-id/camera-b"],
                    ["/dev/ttyACM0", "/dev/ttyACM1"],
                    [],
                ],
            ),
            patch(
                "pi_app.bullettime.discovery.os.path.realpath",
                side_effect=lambda path: {
                    "/dev/serial/by-id/camera-a": "/dev/ttyACM0",
                    "/dev/serial/by-id/camera-b": "/dev/ttyACM1",
                }.get(path, path),
            ),
        ):
            self.assertEqual(discover_ports(), ["/dev/ttyACM0", "/dev/ttyACM1"])


if __name__ == "__main__":
    unittest.main()
