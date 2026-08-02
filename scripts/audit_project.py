"""Audit Notebook execution evidence and expected delivery artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.project_harness.audit import audit_project
from src.project_harness.config import validate_project_config
from src.project_harness.status import update_status
from src.project_harness.validation import format_report, write_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit a generated data analysis project.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument("--json-output", default="logs/audit_report.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    report = audit_project(project_root)
    print(format_report(report))
    output = Path(args.json_output)
    if not output.is_absolute():
        output = project_root / output
    write_report(output, report)
    print(f"Audit report: {output}")
    config = validate_project_config(project_root)
    if report.passed and config["project"]["mode"] == "project":
        update_status(project_root, current_stage="audited", completed_stage="audited")
    raise SystemExit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
