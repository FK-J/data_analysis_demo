"""Validate project plans and generate an up-to-date user-facing progress summary."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.project_harness.config import validate_project_config
from src.project_harness.planning import register_change, write_progress


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate progress after every new requirement, change or task update.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument("--change-id", help="Register a new/revised requirement already present in the change log.")
    parser.add_argument("--summary", help="Describe the new or revised requirement.")
    parser.add_argument("--tasks", nargs="+", help="Affected task IDs; accepted downstream tasks require revalidation.")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    config = validate_project_config(root)
    try:
        if any((args.change_id, args.summary, args.tasks)):
            if not all((args.change_id, args.summary, args.tasks)):
                parser.error("--change-id, --summary and --tasks must be used together.")
            register_change(root, config, args.change_id, args.summary, args.tasks)
        path = write_progress(root, config)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"Cannot generate progress: {exc}\n")
    print(path.read_text(encoding="utf-8"))
    print(f"Progress summary: {path}")


if __name__ == "__main__":
    main()
