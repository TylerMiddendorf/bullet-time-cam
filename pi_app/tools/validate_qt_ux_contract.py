"""Validate the Qt UX contract without importing Qt or third-party packages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pi_app.qt_validation.contract import CONTRACT_PATH, validate_contract


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract",
        type=Path,
        default=CONTRACT_PATH,
        help="path to ux_contract.json",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit a stable JSON report instead of a one-line summary",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = validate_contract(contract_path=args.contract)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    elif report.ok:
        print(f"PASS Qt UX contract v{report.contract_version}: {report.route_count} routes")
    else:
        print(f"FAIL Qt UX contract: {len(report.errors)} error(s)")
        for error in report.errors:
            print(f"- {error}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
