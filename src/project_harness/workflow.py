"""Evaluate stage exits; preflight never requires future run artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import ConfigError, load_yaml, resolve_project_path
from .contracts import check_report_coverage, check_report_metrics, is_complete, load_contracts
from .validation import CheckResult, check


def evaluate_stage(root: Path, config: dict[str, Any], stage: str) -> list[CheckResult]:
    workflow = load_yaml(root / ".harness/workflow.yaml")
    stages = workflow["stages"]
    identifiers = [item["id"] for item in stages]
    if len(set(identifiers)) != len(identifiers) or stage not in identifiers:
        raise ConfigError(f"Unknown or duplicate workflow stage: {stage}")
    if config["project"]["mode"] == "template":
        return [check("stage_exit", "warn", "Template mode has no business stage completion evidence.")]
    try:
        contracts = load_contracts(root, config)
    except (ConfigError, FileNotFoundError, ValueError) as exc:
        return [check("stage_exit", "unverified", str(exc), category="analysis")]
    results = []
    active_stages = stages[:identifiers.index(stage) + 1]
    for definition in active_stages:
        for relative in definition.get("requires", []):
            aliases = {
                "notebooks/main_analysis.ipynb": config["runtime"]["notebook"],
                "docs/analysis_framework.md": config["paths"]["analysis_framework"],
                "reports/final/final_report_structure.md": config["paths"]["report_structure"],
                "reports/final/report_inputs.yaml": config["paths"]["report_inputs"],
                "reports/final/final_analysis_report.md": config["paths"]["final_report"],
            }
            relative = aliases.get(relative, relative)
            if relative in {config["paths"]["report_inputs"], config["paths"]["report_structure"], config["paths"]["final_report"]} and not config["deliverables"]["final_report"]:
                continue
            path = resolve_project_path(root, relative)
            results.append(check("stage_artifact", "pass" if path.is_file() else "fail", f"{definition['id']}: required evidence.", relative))
        for gate in definition.get("gates", []):
            if gate == "decisions":
                if not contracts["decisions"]:
                    results.append(check("decision_readiness", "unverified", "No decisions are declared.", category="analysis"))
                for decision in contracts["decisions"]:
                    due = identifiers.index(decision["resolve_by_stage"]) <= identifiers.index(stage)
                    if due:
                        passed = decision["status"] == "confirmed" and is_complete(decision) and is_complete(decision["evidence"])
                        results.append(check("decision_readiness", "pass" if passed else "fail", f"{decision['id']}: {decision['status']}; confirmation evidence required.", category="analysis"))
            elif gate == "sources":
                if not contracts["sources"]:
                    results.append(check("data_admission", "unverified", "No data admission conclusions are declared.", category="analysis"))
                admitted = []
                for source in contracts["sources"]:
                    passed = source["status"] != "pending" and is_complete({key: value for key, value in source.items() if key != "reason"}) and is_complete(source["evidence"])
                    if source["status"] in {"limited", "excluded"}:
                        passed = passed and is_complete(source["reason"])
                    if source["status"] in {"usable", "limited"}:
                        admitted.append(source)
                        passed = passed and bool(source.get("path")) and resolve_project_path(root, source["path"]).is_file()
                    results.append(check("data_admission", "pass" if passed else "fail", f"{source['id']}: {source['status']}; semantic evidence and usable input snapshot required.", category="analysis"))
                if contracts["sources"] and not admitted:
                    results.append(check("data_admission", "fail", "All sources are excluded; revise the analysis scope.", category="analysis"))
            elif gate == "metrics":
                if not contracts["metrics"]:
                    results.append(check("metric_contract", "unverified", "No core metrics are declared.", category="analysis"))
                for metric in contracts["metrics"]:
                    results.append(check("metric_contract", "pass" if is_complete(metric) else "fail", f"{metric['id']}: grain, population, numerator, denominator, window and version.", category="analysis"))
            elif gate in {"data_checks", "analysis_checks"}:
                from src.quality import run_table_checks
                results.extend(run_table_checks(root, contracts["checks"], category="data" if gate == "data_checks" else "analysis"))
            elif gate == "report_coverage":
                results.extend(check_report_coverage(root, config, contracts))
            elif gate == "report_metrics":
                results.extend(check_report_metrics(root, config, contracts))
            elif gate == "run_evidence":
                from .provenance import verify_run
                results.extend(verify_run(root, config))
            elif gate == "report_binding":
                from .provenance import verify_report
                if config["deliverables"]["final_report"]:
                    results.extend(verify_report(root, config))
            elif gate == "delivery_artifacts":
                from .provenance import latest_run
                try:
                    _, manifest = latest_run(root)
                    recorded = manifest.get("output_fingerprints", {})
                    for kind in ("figures", "tables"):
                        if not config["deliverables"][kind]:
                            continue
                        paths = list((root / "reports" / kind).glob("*"))
                        captured = [path for path in paths if path.is_file() and path.relative_to(root).as_posix() in recorded]
                        results.append(check("delivery_artifacts", "pass" if captured else "fail", f"{kind}: {len(captured)} files captured by this run.", category="report"))
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    results.append(check("delivery_artifacts", "fail", str(exc), category="report"))
            else:
                results.append(check("stage_gate", "fail", f"Unknown gate: {gate}."))
    return results
