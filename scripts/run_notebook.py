"""Headlessly reproduce the configured main Notebook and preserve evidence."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.project_harness.execution import execute_notebook
from src.project_harness.validation import format_report, validate_project


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Headlessly execute main_analysis.ipynb.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument("--output", default=None, help="Optional project-relative executed Notebook path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    preflight = validate_project(args.project_root)
    print(format_report(preflight))
    if not preflight.passed:
        print("Notebook execution stopped because preflight validation failed.")
        raise SystemExit(1)

    result = execute_notebook(
        args.project_root,
        output_path=args.output,
        preflight_checks=[item.as_dict() for item in preflight.checks],
    )
    manifest = result["manifest"]
    print(f"Run status: {manifest['status']}")
    print(f"Executed Notebook: {result['executed_notebook']}")
    print(f"Run manifest: {result['manifest_path']}")
    if manifest["status"] != "passed":
        print(f"Execution error: {manifest['error']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
