"""Delivery audit for Notebook outputs, reports, and execution evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .config import ConfigError, load_yaml, resolve_project_path, validate_project_config
from .validation import PLACEHOLDER_PATTERN, CheckResult, ValidationReport, check, validate_project


def _non_placeholder_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return [path for path in directory.iterdir() if path.is_file() and path.name != ".gitkeep"]


def _asset_paths(report_inputs: dict[str, Any]) -> Iterable[str]:
    summary = report_inputs.get("summary", {})
    for key in ("figures", "tables"):
        for asset in summary.get(key, []) or []:
            if isinstance(asset, dict) and asset.get("path"):
                yield str(asset["path"])
    for question in report_inputs.get("business_questions", []) or []:
        if not isinstance(question, dict):
            continue
        for key in ("figures", "tables"):
            for asset in question.get(key, []) or []:
                if isinstance(asset, dict) and asset.get("path"):
                    yield str(asset["path"])


def _latest_manifest(root: Path) -> Path | None:
    manifests = list((root / "logs" / "runs").glob("*/manifest.json"))
    return max(manifests, key=lambda path: path.stat().st_mtime) if manifests else None


def audit_project(project_root: str | Path) -> ValidationReport:
    """Validate project structure and verify concrete delivery evidence."""
    root = Path(project_root).resolve()
    base_report = validate_project(root)
    results = list(base_report.checks)
    if not base_report.passed:
        return ValidationReport(results)

    config = validate_project_config(root)
    if config["project"]["mode"] == "template":
        results.append(
            check(
                "delivery_artifacts",
                "warn",
                "Template mode audits the scaffold only; generate a concrete project to audit deliverables.",
            )
        )
        return ValidationReport(results)

    deliverables = config["deliverables"]
    for key, relative_dir in (("figures", "reports/figures"), ("tables", "reports/tables")):
        if deliverables[key]:
            files = _non_placeholder_files(root / relative_dir)
            results.append(
                check(
                    f"delivery_{key}",
                    "pass" if files else "fail",
                    f"Found {len(files)} delivered {key}." if files else f"No delivered {key} found.",
                    relative_dir,
                )
            )

    report_inputs_path = resolve_project_path(root, config["paths"]["report_inputs"])
    if report_inputs_path.exists():
        report_inputs = load_yaml(report_inputs_path)
        serialized = json.dumps(report_inputs, ensure_ascii=False)
        results.append(
            check(
                "report_placeholders",
                "fail" if PLACEHOLDER_PATTERN.search(serialized) else "pass",
                "Report inputs contain unresolved placeholders."
                if PLACEHOLDER_PATTERN.search(serialized)
                else "Report inputs contain no unresolved placeholders.",
                config["paths"]["report_inputs"],
            )
        )
        for relative_path in _asset_paths(report_inputs):
            try:
                asset_path = resolve_project_path(root, relative_path)
            except ConfigError:
                results.append(
                    check(
                        "report_asset_reference",
                        "fail",
                        "Referenced report asset must stay inside the project root.",
                        relative_path,
                    )
                )
                continue
            results.append(
                check(
                    "report_asset_reference",
                    "pass" if asset_path.exists() else "fail",
                    "Referenced report asset exists."
                    if asset_path.exists()
                    else "Referenced report asset is missing.",
                    relative_path,
                )
            )

    if deliverables["final_report"]:
        final_report = resolve_project_path(root, config["paths"]["final_report"])
        final_report_exists = final_report.exists()
        final_report_has_placeholders = final_report_exists and bool(
            PLACEHOLDER_PATTERN.search(final_report.read_text(encoding="utf-8"))
        )
        results.append(
            check(
                "final_report",
                "pass" if final_report_exists and not final_report_has_placeholders else "fail",
                "Final report exists and contains no unresolved placeholders."
                if final_report_exists and not final_report_has_placeholders
                else "Final report is missing or contains unresolved placeholders.",
                config["paths"]["final_report"],
            )
        )

    manifest_path = _latest_manifest(root)
    if manifest_path is None:
        results.append(check("notebook_execution", "fail", "No headless Notebook run manifest was found."))
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        passed = manifest.get("status") == "passed"
        results.append(
            check(
                "notebook_execution",
                "pass" if passed else "fail",
                "Latest headless Notebook execution passed."
                if passed
                else "Latest headless Notebook execution did not pass.",
                manifest_path.relative_to(root),
            )
        )
    return ValidationReport(results)
