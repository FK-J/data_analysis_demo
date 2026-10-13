"""Validate declarations owned by an analysis project, not by the framework."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .config import ConfigError, load_yaml, resolve_project_path, validate_against_schema
from .validation import PLACEHOLDER_PATTERN, CheckResult, check


def load_contracts(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    path = config.get("paths", {}).get("contracts")
    if not path:
        raise ConfigError("Declare paths.contracts before evaluating project stages.")
    data = load_yaml(resolve_project_path(root, path))
    validate_against_schema(data, root / "schemas/contracts.schema.yaml", label="project contracts")
    for section in ("decisions", "sources", "metrics", "checks", "report_requirements"):
        identifiers = [item["id"] for item in data[section]]
        if len(set(identifiers)) != len(identifiers):
            raise ConfigError(f"Duplicate IDs in {section}.")
    for source in data["sources"]:
        if source.get("path"):
            resolve_project_path(root, source["path"])
    for rule in data["checks"]:
        resolve_project_path(root, rule["table"])
        if rule.get("other_table"):
            resolve_project_path(root, rule["other_table"])
        required = {
            "unique": ["keys"], "non_null": ["column"], "range": ["column"],
            "row_count": [], "sum_equals": ["column", "other_table", "other_column"],
            "column_relation": ["column", "other_column", "operator"],
        }[rule["kind"]]
        if any(key not in rule for key in required):
            raise ConfigError(f"Check {rule['id']} requires {required}.")
        if rule["kind"] in {"range", "row_count"} and not any(key in rule for key in ("min", "max", "expected")):
            raise ConfigError(f"Check {rule['id']} requires at least one bound or expected value.")
        if rule.get("min", float("-inf")) > rule.get("max", float("inf")):
            raise ConfigError(f"Check {rule['id']} has min greater than max.")
    return data


def validate_contracts(root: Path, config: dict[str, Any]) -> list[CheckResult]:
    if not config["paths"].get("contracts"):
        return [check("contracts_schema", "warn", "Project contracts are not configured; analysis readiness is unverified.")]
    try:
        load_contracts(root, config)
    except (ConfigError, FileNotFoundError, ValueError) as exc:
        return [check("contracts_schema", "fail", str(exc), config["paths"]["contracts"])]
    return [check("contracts_schema", "pass", "Project declarations satisfy the contract schema.", config["paths"]["contracts"])]


def is_complete(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip()) and not PLACEHOLDER_PATTERN.search(value)
    if isinstance(value, dict):
        return bool(value) and all(is_complete(child) for child in value.values())
    if isinstance(value, list):
        return bool(value) and all(is_complete(child) for child in value)
    return value is not None


def check_report_coverage(root: Path, config: dict[str, Any], contracts: dict[str, Any]) -> list[CheckResult]:
    if not config["deliverables"]["final_report"]:
        return [check("report_coverage", "pass", "Final report is not requested.", category="report")]
    path = resolve_project_path(root, config["paths"]["report_inputs"])
    if not path.exists():
        return [check("report_coverage", "unverified", "Report inputs are missing.", category="report")]
    data = load_yaml(path)
    requirements = contracts["report_requirements"]
    entries = data.get("coverage", [])
    identifiers = [entry["id"] for entry in entries]
    if len(set(identifiers)) != len(identifiers):
        return [check("report_coverage", "fail", "Duplicate coverage IDs.", category="report")]
    coverage = {entry["id"]: entry for entry in entries}
    requirement_ids = {item["id"] for item in requirements}
    results = []
    if not requirements:
        results.append(check("report_coverage", "unverified", "No report requirements are declared.", category="report"))
    for identifier in set(coverage) - requirement_ids:
        results.append(check("report_coverage", "fail", f"Unknown coverage ID: {identifier}.", category="report"))
    for requirement in requirements:
        entry = coverage.get(requirement["id"], {})
        status = entry.get("status")
        valid = False
        if status == "covered":
            evidence = entry.get("evidence", [])
            valid = bool(evidence)
            for reference in evidence:
                try:
                    valid = resolve_project_path(root, reference).is_file() and valid
                except ConfigError:
                    valid = False
        elif status == "not_applicable":
            valid = is_complete(entry.get("reason"))
        elif status == "missing" and not requirement["required"]:
            valid = is_complete(entry.get("reason"))
        valid = valid and is_complete(requirement["title"])
        results.append(check(
            "report_coverage", "pass" if valid else "fail",
            f"{requirement['id']}: {status or 'undeclared'}; evidence/reason {'present' if valid else 'missing or incomplete'}.",
            category="report",
        ))
    return results


def check_report_metrics(root: Path, config: dict[str, Any], contracts: dict[str, Any]) -> list[CheckResult]:
    """Compare displayed numeric values with declared result-table cells."""
    if not config["deliverables"]["final_report"]:
        return []
    from src.io import load_table
    path = resolve_project_path(root, config["paths"]["report_inputs"])
    if not path.is_file():
        return [check("report_metrics", "unverified", "Report inputs are missing.", category="report")]
    data = load_yaml(path)
    declared = {item["id"] for item in contracts["metrics"]}
    sections = [data.get("summary", {})] + data.get("business_questions", [])
    results = []
    for section in sections:
        for metric in section.get("metrics", []):
            try:
                reference = metric["source"]
                table = load_table(resolve_project_path(root, reference["path"]))
                source = float(table.iloc[reference.get("row", 0)][reference["column"]])
                displayed = float(metric["value"])
                valid = metric["id"] in declared and math.isfinite(source) and math.isfinite(displayed)
                valid = valid and abs(source - displayed) <= reference.get("tolerance", 0)
                message = f"{metric['id']}: displayed value {'matches' if valid else 'does not match'} its registered result."
            except (OSError, ValueError, KeyError, TypeError, IndexError, ImportError) as exc:
                valid = False
                message = str(exc)
            results.append(check("report_metrics", "pass" if valid else "fail", message, category="report"))
    return results or [check("report_metrics", "unverified", "No numeric metric references were provided.", category="report")]
