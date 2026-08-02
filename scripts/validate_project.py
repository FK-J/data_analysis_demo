"""Run structural and safety checks for the current analysis project."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.project_harness.validation import format_report, validate_project, write_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a generated data analysis project.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument("--json-output", default=None, help="Optional path for the JSON validation report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = validate_project(args.project_root)
    print(format_report(report))
    if args.json_output:
        write_report(args.json_output, report)
    raise SystemExit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
