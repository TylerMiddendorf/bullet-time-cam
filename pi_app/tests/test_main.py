import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pi_app.bullettime.main import load_config, parse_args


class MainConfigurationTests(unittest.TestCase):
    def test_load_config_resolves_logo_and_applies_cli_capture_controls(self):
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "startup_logo": "../assets/logo.png",
                        "trigger_count": 2,
                        "corrupt_next_payload": False,
                    }
                ),
                encoding="utf-8",
            )
            args = argparse.Namespace(
                config=str(config_path),
                trigger_count=3,
                trigger_once=False,
                corrupt_next_payload=True,
                truncate_camera_id=3,
                diagnostic_usb_trigger=True,
                allow_incomplete_node_set=True,
            )
            config = load_config(args)

            self.assertEqual(config["trigger_count"], 3)
            self.assertTrue(config["corrupt_next_payload"])
            self.assertEqual(config["truncate_camera_id"], 3)
            self.assertTrue(config["diagnostic_usb_trigger"])
            self.assertTrue(config["allow_incomplete_node_set"])
            self.assertEqual(
                Path(config["startup_logo"]),
                (config_path.parent / "../assets/logo.png").resolve(),
            )

    def test_trigger_once_never_reduces_configured_trigger_count(self):
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "config.json"
            config_path.write_text('{"trigger_count":5}', encoding="utf-8")
            args = argparse.Namespace(
                config=str(config_path),
                trigger_count=0,
                trigger_once=True,
                corrupt_next_payload=False,
                truncate_camera_id=0,
                diagnostic_usb_trigger=False,
                allow_incomplete_node_set=False,
            )
            self.assertEqual(load_config(args)["trigger_count"], 5)

    def test_parse_args_defaults_to_normal_hardware_trigger(self):
        with patch("sys.argv", ["bullet-time"]):
            args = parse_args()
        self.assertFalse(args.headless)
        self.assertFalse(args.diagnostic_usb_trigger)
        self.assertFalse(args.allow_incomplete_node_set)
        self.assertEqual(args.truncate_camera_id, 0)
        self.assertEqual(args.trigger_count, 0)
        self.assertIsNone(args.initial_route)
        self.assertEqual(args.quit_after_seconds, 0)
        self.assertEqual(args.capture_after_seconds, 0)

    def test_bounded_ui_validation_arguments_enter_capture_and_auto_quit(self):
        with patch(
            "sys.argv",
            [
                "bullet-time",
                "--initial-route",
                "capture",
                "--quit-after-seconds",
                "12.5",
                "--capture-after-seconds",
                "5",
            ],
        ):
            args = parse_args()
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "config.json"
            config_path.write_text("{}", encoding="utf-8")
            args.config = str(config_path)
            config = load_config(args)
        self.assertEqual(config["initial_route"], "capture")
        self.assertEqual(config["quit_after_ms"], 12_500)
        self.assertEqual(config["capture_after_ms"], 5_000)


if __name__ == "__main__":
    unittest.main()
