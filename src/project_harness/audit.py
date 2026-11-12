"""Delivery audit for Notebook outputs, reports, and execution evidence."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .config import (
    ConfigError,
    detail_report_enabled,
    detail_report_path,
    load_yaml,
    resolve_project_path,
    validate_project_config,
)
from .provenance import asset_paths
from .validation import PLACEHOLDER_PATTERN, ValidationReport, check, validate_project


def _non_placeholder_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return [path for path in directory.iterdir() if path.is_file() and path.name != ".gitkeep"]


def _has_text(values: Any) -> bool:
    return any(str(item).strip() for item in (values or []) if item is not None)


def _section_conclusion_gaps(report_inputs: dict[str, Any]) -> list[str]:
    gaps: list[str] = []
    summary = report_inputs.get("summary", {}) or {}
    if not _has_text(summary.get("conclusions") or summary.get("key_results")):
        gaps.append("summary")
    for question in report_inputs.get("business_questions", []) or []:
        if not isinstance(question, dict):
            continue
        identifier = str(question.get("id") or "Q?")
        if not _has_text(question.get("conclusions") or question.get("key_results")):
            gaps.append(identifier)
    detail = report_inputs.get("detail", {}) or {}
    for section in detail.get("sections", []) or []:
        if not isinstance(section, dict):
            continue
        identifier = str(section.get("id") or "D?")
        if not _has_text(section.get("conclusions")):
            gaps.append(identifier)
    return gaps


def _report_links(root: Path, path: Path) -> list[str]:
    """Return project-relative links or assets that do not resolve."""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".html", ".htm"}:
        references = re.findall(r'(?:href|src)="([^"]+)"', text)
    else:
        references = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text)
    missing: list[str] = []
    for reference in references:
        reference = reference.strip()
        if not reference or reference.startswith(("http://", "https://", "#", "mailto:", "data:", "javascript:")):
            continue
        target = reference.split("#", 1)[0]
        if not target:
            continue
        resolved = (path.parent / target).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            missing.append(reference)
            continue
        if not resolved.is_file():
            missing.append(reference)
    return missing


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
    from .workflow import evaluate_stage
    try:
        results.extend(evaluate_stage(root, config, "audited"))
    except (ConfigError, FileNotFoundError, ValueError, KeyError, TypeError) as exc:
        results.append(check("stage_exit", "fail", str(exc), category="analysis"))
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
        gaps = _section_conclusion_gaps(report_inputs)
        results.append(
            check(
                "report_section_conclusions",
                "pass" if not gaps else "fail",
                "Every summary, business question and detail section has a conclusion."
                if not gaps
                else "Missing section conclusions: " + ", ".join(gaps) + ".",
                config["paths"]["report_inputs"],
                category="report",
            )
        )
        for relative_path in dict.fromkeys(asset_paths(report_inputs)):
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
        artifacts = [(config["paths"]["final_report"], "final_report")]
        if detail_report_enabled(config):
            artifacts.append((detail_report_path(config), "detail_report"))
        for relative, code in artifacts:
            report_path = resolve_project_path(root, relative)
            exists = report_path.exists()
            has_placeholders = exists and bool(PLACEHOLDER_PATTERN.search(report_path.read_text(encoding="utf-8")))
            valid = exists and not has_placeholders
            results.append(
                check(
                    code,
                    "pass" if valid else "fail",
                    f"{relative} exists and contains no unresolved placeholders."
                    if valid
                    else f"{relative} is missing or contains unresolved placeholders.",
                    relative,
                    category="report",
                )
            )
            if exists:
                missing = _report_links(root, report_path)
                results.append(
                    check(
                        "report_links",
                        "pass" if not missing else "fail",
                        f"{relative}: all relative links and assets resolve."
                        if not missing
                        else f"{relative}: unresolved links or assets: {', '.join(missing)}.",
                        relative,
                        category="report",
                    )
                )

    return ValidationReport(results)
