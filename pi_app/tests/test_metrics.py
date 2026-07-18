import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pi_app.bullettime.metrics import resource_sample


class MetricsTests(unittest.TestCase):
    def test_resource_sample_uses_active_storage_path_and_records_phase(self):
        process = MagicMock()
        process.cpu_times.return_value = SimpleNamespace(user=1.25, system=0.5)
        process.memory_info.return_value = SimpleNamespace(rss=1234)
        with tempfile.TemporaryDirectory() as temp:
            storage = Path(temp)
            with (
                patch("pi_app.bullettime.metrics.psutil.Process", return_value=process),
                patch(
                    "pi_app.bullettime.metrics.psutil.virtual_memory",
                    return_value=SimpleNamespace(available=5678),
                ),
                patch(
                    "pi_app.bullettime.metrics.psutil.disk_usage",
                    return_value=SimpleNamespace(free=9012),
                ) as disk_usage,
                patch("pi_app.bullettime.metrics.psutil.getloadavg", return_value=(0.25, 0, 0)),
                patch("pi_app.bullettime.metrics.time.monotonic_ns", return_value=42),
            ):
                sample = resource_sample("payload_received", storage)

            disk_usage.assert_called_once_with(storage)
            self.assertEqual(sample["phase"], "payload_received")
            self.assertEqual(sample["pi_monotonic_ns"], 42)
            self.assertEqual(sample["storage_free_bytes"], 9012)

    def test_missing_storage_path_falls_back_to_root(self):
        process = MagicMock()
        process.cpu_times.return_value = SimpleNamespace(user=0, system=0)
        process.memory_info.return_value = SimpleNamespace(rss=0)
        with (
            patch("pi_app.bullettime.metrics.psutil.Process", return_value=process),
            patch(
                "pi_app.bullettime.metrics.psutil.virtual_memory",
                return_value=SimpleNamespace(available=0),
            ),
            patch(
                "pi_app.bullettime.metrics.psutil.disk_usage",
                return_value=SimpleNamespace(free=0),
            ) as disk_usage,
            patch("pi_app.bullettime.metrics.psutil.getloadavg", return_value=(0, 0, 0)),
        ):
            sample = resource_sample("fallback", Path("definitely-missing-storage-path"))
        disk_usage.assert_called_once_with(Path("/"))
        self.assertEqual(sample["storage_sample_path"], str(Path("/")))


if __name__ == "__main__":
    unittest.main()
