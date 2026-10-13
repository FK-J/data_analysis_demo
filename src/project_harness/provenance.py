"""Bind a formal run to input/code bytes and to its generated artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .config import ConfigError, load_yaml, resolve_project_path
from .contracts import load_contracts
from .validation import CheckResult, check


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def input_fingerprints(root: Path, config: dict[str, Any]) -> dict[str, str]:
    paths = {"project.yaml", config["runtime"]["analysis_config"], config["runtime"]["notebook"],
             config["runtime"].get("notebook_template", "templates/notebook_sections.yaml"), ".harness/workflow.yaml"}
    for directory, pattern in (("src", "*.py"), ("scripts", "*.py"), ("sql", "*.sql"), ("schemas", "*.yaml")):
        paths.update(path.relative_to(root).as_posix() for path in (root / directory).rglob(pattern))
    for key in ("analysis_framework", "report_structure", "contracts"):
        if config["paths"].get(key):
            paths.add(config["paths"][key])
    if config["paths"].get("contracts"):
        contracts = load_contracts(root, config)
        paths.update(item["path"] for item in contracts["sources"] if item.get("path") and item["status"] != "excluded")
    # Templates may lack concrete business documents; a concrete project must register readable snapshots.
    return {relative: file_digest(resolve_project_path(root, relative)) for relative in sorted(paths)
            if resolve_project_path(root, relative).is_file()}


def asset_paths(value: Any):
    """Traverse ordinary and project-specific figure/table/coverage declarations."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"figures", "tables"} and isinstance(child, list):
                for item in child:
                    if isinstance(item, dict) and item.get("path"):
                        yield str(item["path"])
            elif key == "evidence" and isinstance(child, list):
                yield from (item for item in child if isinstance(item, str))
            elif key == "source" and isinstance(child, dict) and child.get("path"):
                yield str(child["path"])
            else:
                yield from asset_paths(child)
    elif isinstance(value, list):
        for child in value:
            yield from asset_paths(child)


def output_fingerprints(root: Path, config: dict[str, Any], executed: Path) -> dict[str, str]:
    paths = {executed.relative_to(root).as_posix()}
    inputs = resolve_project_path(root, config["paths"]["report_inputs"])
    if inputs.is_file():
        paths.add(inputs.relative_to(root).as_posix())
        paths.update(asset_paths(load_yaml(inputs)))
    if config["paths"].get("contracts"):
        for rule in load_contracts(root, config)["checks"]:
            paths.add(rule["table"])
            if rule.get("other_table"):
                paths.add(rule["other_table"])
    return {relative: file_digest(resolve_project_path(root, relative)) for relative in sorted(paths)
            if resolve_project_path(root, relative).is_file()}


def latest_run(root: Path) -> tuple[Path, dict[str, Any]]:
    status_path = root / ".harness/status.yaml"
    run_id = load_yaml(status_path).get("last_run_id") if status_path.is_file() else None
    if run_id:
        path = resolve_project_path(root, f"logs/runs/{run_id}/manifest.json")
    else:
        manifests = list((root / "logs/runs").glob("*/manifest.json"))
        if not manifests:
            raise FileNotFoundError("No formal run manifest was found.")
        path = max(manifests, key=lambda item: item.stat().st_mtime)
    data = json.loads(path.read_text(encoding="utf-8"))
    if path.parent.name != data.get("run_id"):
        raise ConfigError("Run identity does not match its manifest directory.")
    return path, data


def verify_run(root: Path, config: dict[str, Any]) -> list[CheckResult]:
    results = []
    try:
        path, manifest = latest_run(root)
        if manifest.get("status") != "passed":
            return [check("run_binding", "fail", "Latest formal run has not passed.")]
        recorded = manifest.get("input_fingerprints")
        if not recorded or not manifest.get("output_fingerprints"):
            return [check("run_binding", "unverified", "Run lacks input/output fingerprints; run it again.")]
        current = input_fingerprints(root, config)
        results.append(check("run_inputs", "pass" if current == recorded else "fail",
                             "Current inputs, contracts and code match the formal run." if current == recorded else "Inputs, contracts or code changed after the formal run.", path.relative_to(root)))
        for relative, digest in manifest["output_fingerprints"].items():
            artifact = resolve_project_path(root, relative)
            valid = artifact.is_file() and file_digest(artifact) == digest
            results.append(check("run_artifact", "pass" if valid else "fail", "Artifact matches this run." if valid else "Artifact is missing or changed after execution.", relative))
        executed = manifest.get("executed_notebook")
        if not executed or executed not in manifest["output_fingerprints"]:
            results.append(check("run_binding", "fail", "Executed Notebook is not fingerprinted."))
        if config["deliverables"]["final_report"]:
            inputs_relative = config["paths"]["report_inputs"]
            if inputs_relative not in manifest["output_fingerprints"]:
                results.append(check("run_binding", "fail", "Report inputs were not captured by this run.", inputs_relative))
            inputs_path = resolve_project_path(root, inputs_relative)
            if inputs_path.is_file():
                inputs = load_yaml(inputs_path)
                if inputs.get("project", {}).get("run_id") != manifest["run_id"]:
                    results.append(check("run_binding", "fail", "Report inputs do not belong to this run; export them in the Notebook."))
                for relative in asset_paths(inputs):
                    if relative not in manifest["output_fingerprints"]:
                        results.append(check("run_binding", "fail", "Referenced evidence was not captured by the run.", relative))
    except (OSError, ValueError, ConfigError, KeyError, TypeError) as exc:
        results.append(check("run_binding", "fail", str(exc)))
    return results


def bind_report(root: Path, config: dict[str, Any], output: Path) -> str:
    checks = verify_run(root, config)
    if any(item.status in {"fail", "unverified"} for item in checks):
        raise ConfigError("Report requires a successful matching run: " + "; ".join(item.message for item in checks if item.status != "pass"))
    path, manifest = latest_run(root)
    relative = output.relative_to(root).as_posix()
    manifest.setdefault("report_fingerprints", {})[relative] = file_digest(output)
    if relative not in manifest["artifacts"]:
        manifest["artifacts"].append(relative)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest["run_id"]


def verify_report(root: Path, config: dict[str, Any]) -> list[CheckResult]:
    try:
        _, manifest = latest_run(root)
        relative = config["paths"]["final_report"]
        path = resolve_project_path(root, relative)
        digest = manifest.get("report_fingerprints", {}).get(relative)
        valid = bool(digest) and path.is_file() and file_digest(path) == digest
        if valid:
            valid = f"- 运行 ID：`{manifest['run_id']}`" in path.read_text(encoding="utf-8")
        return [check("report_binding", "pass" if valid else "fail", "Report belongs to this formal run." if valid else "Report is unbound, missing or changed after generation.", relative, category="report")]
    except (OSError, ValueError, ConfigError, KeyError, TypeError) as exc:
        return [check("report_binding", "fail", str(exc), category="report")]
