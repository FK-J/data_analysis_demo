"""Generate the analyst-facing main Notebook from project.yaml."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.project_harness.notebook import generate_notebook


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate main_analysis.ipynb from project.yaml.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument("--output", default=None, help="Optional project-relative output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = generate_notebook(args.project_root, output_path=args.output)
    print(f"Generated Notebook: {output}")


if __name__ == "__main__":
    main()
