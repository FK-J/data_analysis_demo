"""Generate the conclusion summary and the detailed analysis report.

Default behavior is intentionally conservative:
- the Markdown summary renders metadata, core conclusions, key metrics, key
  figures and an index into the detailed HTML;
- the HTML report renders the full analysis process, evidence, tables and
  per-section conclusions;
- no business insight is generated automatically and no large language model
  is called.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise ImportError("Missing dependency PyYAML. Install it with: pip install PyYAML") from exc


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.project_harness.config import (
    ConfigError,
    detail_report_enabled,
    detail_report_path,
    resolve_project_path,
    validate_against_schema,
    validate_project_config,
)
from src.project_harness.status import update_status
from src.project_harness.provenance import bind_report, latest_run, verify_run
from src.project_harness.contracts import check_report_coverage, check_report_metrics, load_contracts
from src.project_harness.validation import PLACEHOLDER_PATTERN, ValidationReport, format_report, validate_project
from src.reporting.report import render_detail_html, render_summary_markdown


DEFAULT_INPUT = PROJECT_ROOT / "reports" / "final" / "report_inputs.yaml"
DEFAULT_SUMMARY_OUTPUT = PROJECT_ROOT / "reports" / "final" / "final_analysis_report.md"
DEFAULT_DETAIL_OUTPUT = PROJECT_ROOT / "reports" / "final" / "analysis_detail.html"


def load_report_inputs(input_path: Path, *, project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Load report inputs from YAML."""
    if not input_path.exists():
        raise FileNotFoundError(
            f"Report input file not found: {input_path}. "
            "Copy docs/report_inputs_template.yaml to reports/final/report_inputs.yaml "
            "and fill in the exported results first."
        )

    with input_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError("Report input YAML must contain a top-level mapping.")

    validate_against_schema(
        data,
        project_root / "schemas" / "report_inputs.schema.yaml",
        label="report inputs",
    )

    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the conclusion summary and detailed analysis report.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument(
        "--input",
        default=None,
        help="Path to report input YAML. Defaults to reports/final/report_inputs.yaml.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to the summary Markdown. Defaults to reports/final/final_analysis_report.md.",
    )
    parser.add_argument(
        "--detail-output",
        default=None,
        help="Path to the detailed HTML. Defaults to reports/final/analysis_detail.html.",
    )
    parser.add_argument(
        "--format",
        choices=["both", "md", "html"],
        default="both",
        help="Render both deliverables by default; use md or html for local iteration only.",
    )
    parser.add_argument(
        "--with-insights",
        action="store_true",
        help="Render pre-written insights in the detailed HTML. This does not call a large language model.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.project_root).resolve()
    config = validate_project_config(root)
    declared_summary = config["paths"]["final_report"]
    declared_detail = detail_report_path(config)
    input_path = resolve_project_path(root, args.input or config["paths"]["report_inputs"])
    summary_path = resolve_project_path(root, args.output or declared_summary)
    detail_path = resolve_project_path(root, args.detail_output or declared_detail)
    if input_path != resolve_project_path(root, config["paths"]["report_inputs"]):
        raise ConfigError("Declare custom report input paths in project.yaml so the report remains auditable.")
    if summary_path != resolve_project_path(root, declared_summary):
        raise ConfigError("Declare custom summary report paths in project.yaml so the report remains auditable.")
    if detail_path != resolve_project_path(root, declared_detail):
        raise ConfigError("Declare custom detail report paths in project.yaml so the report remains auditable.")
    if not config["deliverables"]["final_report"]:
        raise ConfigError("Final report generation is disabled in project.yaml.")
    if args.format in {"both", "html"} and not detail_report_enabled(config):
        raise ConfigError("Detailed report generation is disabled in project.yaml.")

    preflight = validate_project(root, stage="analyzed")
    print(format_report(preflight))
    if not preflight.passed:
        raise SystemExit(1)
    run_checks = ValidationReport(verify_run(root, config))
    if not run_checks.passed:
        print(format_report(run_checks))
        raise SystemExit(1)

    data = load_report_inputs(input_path, project_root=root)
    contracts = load_contracts(root, config)
    coverage = ValidationReport(check_report_coverage(root, config, contracts) + check_report_metrics(root, config, contracts))
    if not coverage.passed:
        print(format_report(coverage))
        raise SystemExit(1)
    if args.with_insights and not config["deliverables"]["insights"]:
        raise ConfigError("Enable deliverables.insights before rendering requested insight text.")

    _, manifest = latest_run(root)
    data["project"]["run_id"] = manifest["run_id"]
    data["project"]["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    outputs: list[Path] = []
    if args.format in {"both", "md"}:
        summary = render_summary_markdown(
            data,
            project_root=root,
            output_path=summary_path,
            detail_path=detail_path,
        )
        if PLACEHOLDER_PATTERN.search(summary):
            raise ConfigError("Rendered summary contains unresolved placeholders; complete the report inputs first.")
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")
        outputs.append(summary_path)

    if args.format in {"both", "html"}:
        detail = render_detail_html(
            data,
            project_root=root,
            output_path=detail_path,
            summary_path=summary_path,
            with_insights=bool(args.with_insights),
        )
        if PLACEHOLDER_PATTERN.search(detail):
            raise ConfigError("Rendered detail report contains unresolved placeholders; complete the report inputs first.")
        detail_path.parent.mkdir(parents=True, exist_ok=True)
        detail_path.write_text(detail, encoding="utf-8")
        outputs.append(detail_path)

    bind_report(root, config, outputs)
    update_status(root, current_stage="reported", completed_stage="reported")
    for output in outputs:
        print(f"Generated report: {output}")
    if args.format != "both":
        print("Note: formal delivery binds both the summary and the detailed report; run without --format for delivery.")


if __name__ == "__main__":
    main()
