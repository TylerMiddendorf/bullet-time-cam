import os
import unittest
from pathlib import Path

from pi_app.evidence.validation import validate_scenario_ledger


@unittest.skipUnless(
    os.environ.get("FOUR_NODE_E2E_CAPTURE_ROOT") and os.environ.get("FOUR_NODE_E2E_LEDGER"),
    "set FOUR_NODE_E2E_CAPTURE_ROOT and FOUR_NODE_E2E_LEDGER after the live hardware sequence",
)
class LiveFourNodeHardwareEvidenceTests(unittest.TestCase):
    def test_required_live_scenarios_and_persisted_artifacts(self):
        result = validate_scenario_ledger(
            Path(os.environ["FOUR_NODE_E2E_CAPTURE_ROOT"]),
            Path(os.environ["FOUR_NODE_E2E_LEDGER"]),
        )
        self.assertEqual(result["status"], "pass")
        self.assertGreaterEqual(result["normal_capture_count"], 25)


if __name__ == "__main__":
    unittest.main()
