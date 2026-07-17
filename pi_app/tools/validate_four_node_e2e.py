"""Validate persisted evidence from the live four-node E2E test sequence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pi_app.evidence.validation import validate_scenario_ledger


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-root", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()
    result = validate_scenario_ledger(args.capture_root, args.ledger)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
