"""Create a concrete data analysis project from this template."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.project_harness.scaffold import initialize_project


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize a Notebook-first data analysis project.")
    parser.add_argument("--output", required=True, help="New project directory outside this template repository.")
    parser.add_argument("--name", required=True, help="Lowercase project identifier, for example sales_analysis.")
    parser.add_argument("--display-name", required=True, help="Human-readable project name.")
    parser.add_argument(
        "--analysis-type",
        choices=["business_analysis", "statistical_analysis", "machine_learning", "custom"],
        default="business_analysis",
    )
    parser.add_argument(
        "--data-source",
        choices=["local_file", "database", "mixed"],
        default="local_file",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_path = initialize_project(
        args.output,
        name=args.name,
        display_name=args.display_name,
        analysis_type=args.analysis_type,
        data_source=args.data_source,
    )
    print(f"Initialized project: {project_path}")
    print("Next: complete docs/analysis_framework.md and reports/final/final_report_structure.md.")


if __name__ == "__main__":
    main()
