"""Machine-enforced checks derived from the project documentation."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import nbformat
except ImportError as exc:  # pragma: no cover
    raise ImportError("Missing dependency nbformat. Install it with: pip install nbformat") from exc

from .config import (
    ConfigError,
    load_yaml,
    resolve_project_path,
    validate_against_schema,
    validate_project_config,
)
from .notebook import DEFAULT_TEMPLATE, config_digest, enabled_section_ids, template_digest
from .sql_policy import contains_write_statement


PLACEHOLDER_PATTERN = re.compile(r"待填写|\bTODO\b|\bTBD\b", re.IGNORECASE)


@dataclass(frozen=True)
class CheckResult:
    """One validation or audit result."""

    code: str
    status: str
    message: str
    path: str | None = None
    category: str = "engineering"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationReport:
    """Collection of machine-readable checks."""

    checks: list[CheckResult]

    @property
    def passed(self) -> bool:
        return not any(check.status in {"fail", "unverified"} for check in self.checks)

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "summary": {
                status: sum(check.status == status for check in self.checks)
                for status in ("pass", "warn", "fail", "unverified")
            },
            "categories": {
                category: {
                    "passed": not any(item.status in {"fail", "unverified"} for item in self.checks if item.category == category),
                    "checks": sum(item.category == category for item in self.checks),
                }
                for category in {item.category for item in self.checks}
            },
            "checks": [check.as_dict() for check in self.checks],
        }


def check(
    code: str,
    status: str,
    message: str,
    path: str | Path | None = None,
    *,
    category: str = "engineering",
) -> CheckResult:
    """Build a normalized validation result."""
    return CheckResult(code=code, status=status, message=message, path=str(path) if path else None, category=category)


def _required_paths(config: dict[str, Any]) -> list[str]:
    common = [
        "README.md",
        "agent.md",
        "project.yaml",
        "configs/analysis_config.yaml",
        ".harness/workflow.yaml",
        ".harness/template_files.yaml",
        ".harness/status.template.yaml",
        "schemas/project.schema.yaml",
        "schemas/report_inputs.schema.yaml",
        "schemas/run_manifest.schema.yaml",
        "schemas/status.schema.yaml",
        "schemas/contracts.schema.yaml",
        "schemas/plan.schema.yaml",
        "docs/project_plan_template.yaml",
        "scripts/update_progress.py",
        "templates/notebook_sections.yaml",
        config["runtime"]["notebook"],
        "scripts/init_project.py",
        "scripts/generate_notebook.py",
        "scripts/validate_project.py",
        "scripts/run_notebook.py",
        "scripts/audit_project.py",
    ]
    if config["project"]["mode"] == "project":
        common.append(config["paths"]["analysis_framework"])
        if config["deliverables"]["final_report"]:
            common.append(config["paths"]["report_structure"])
    else:
        common.extend(
            [
                "docs/analysis_framework_template.md",
                "docs/final_report_structure_template.md",
                "docs/analysis_detail_report_template.md",
                "docs/report_inputs_template.yaml",
            ]
        )
    return common


def _check_required_paths(root: Path, config: dict[str, Any]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for relative_path in _required_paths(config):
        path = resolve_project_path(root, relative_path)
        results.append(
            check(
                "required_path",
                "pass" if path.exists() else "fail",
                "Required project path exists." if path.exists() else "Required project path is missing.",
                relative_path,
            )
        )
    return results


def _check_notebook(root: Path, config: dict[str, Any]) -> list[CheckResult]:
    relative_notebook = config["runtime"]["notebook"]
    notebook_path = resolve_project_path(root, relative_notebook)
    if not notebook_path.exists():
        return [check("notebook_structure", "fail", "Main Notebook is missing.", relative_notebook)]

    try:
        notebook = nbformat.read(notebook_path, as_version=4)
    except (OSError, ValueError, TypeError) as exc:
        return [
            check("notebook_structure", "fail", f"Main Notebook cannot be read: {exc}", relative_notebook),
            check("notebook_sections", "fail", "Notebook sections cannot be verified.", relative_notebook),
        ]

    template_relative = config["runtime"].get("notebook_template", DEFAULT_TEMPLATE)
    try:
        template_path = resolve_project_path(root, template_relative)
        template = load_yaml(template_path)
        expected_sections = enabled_section_ids(config, template)
        current_template_digest = template_digest(template_path)
    except (OSError, ValueError, TypeError) as exc:
        return [
            check(
                "notebook_sections",
                "fail",
                f"Notebook section template cannot be read: {exc}",
                str(template_relative),
            )
        ]

    harness = notebook.metadata.get("harness") or {}
    actual_sections = list(harness.get("sections", []))
    results = [
        check(
            "notebook_sections",
            "pass" if actual_sections == expected_sections else "fail",
            "Notebook sections match project.yaml."
            if actual_sections == expected_sections
            else f"Notebook sections are stale. Expected {expected_sections}, got {actual_sections}.",
            relative_notebook,
        )
    ]

    current_config_digest = config_digest(config)
    recorded_config_digest = harness.get("project_config_digest")
    if not recorded_config_digest:
        results.append(
            check(
                "notebook_config_digest",
                "warn",
                "Notebook has no project-config digest; regenerate it to enable staleness checks.",
                relative_notebook,
            )
        )
    else:
        matches = recorded_config_digest == current_config_digest
        results.append(
            check(
                "notebook_config_digest",
                "pass" if matches else "fail",
                "Notebook matches the current project.yaml."
                if matches
                else "project.yaml changed after the Notebook was generated; run scripts/generate_notebook.py.",
                relative_notebook,
            )
        )

    recorded_template_digest = harness.get("template_digest")
    if not recorded_template_digest:
        results.append(
            check(
                "notebook_template_digest",
                "warn",
                "Notebook has no template digest; regenerate it to enable staleness checks.",
                relative_notebook,
            )
        )
    else:
        matches = recorded_template_digest == current_template_digest
        results.append(
            check(
                "notebook_template_digest",
                "pass" if matches else "fail",
                "Notebook matches its section template."
                if matches
                else "The Notebook section template changed after generation; run scripts/generate_notebook.py.",
                relative_notebook,
            )
        )

    code_source = "\n".join(cell.source for cell in notebook.cells if cell.cell_type == "code")
    reuses_src = "from src." in code_source or "import src." in code_source
    results.append(
        check(
            "notebook_reuses_src",
            "pass" if reuses_src else "fail",
            "Notebook calls reusable logic from src/." if reuses_src else "Notebook must call reusable logic from src/.",
            relative_notebook,
        )
    )
    return results


def _check_placeholders(root: Path, config: dict[str, Any]) -> list[CheckResult]:
    if config["project"]["mode"] == "template":
        return [check("project_placeholders", "pass", "Template mode permits placeholders in source templates.")]

    paths = [config["paths"]["analysis_framework"], config["paths"]["report_structure"]]
    if not config["deliverables"]["final_report"]:
        paths = [config["paths"]["analysis_framework"]]
    results: list[CheckResult] = []
    for relative_path in paths:
        path = resolve_project_path(root, relative_path)
        has_placeholder = path.exists() and bool(PLACEHOLDER_PATTERN.search(path.read_text(encoding="utf-8")))
        results.append(
            check(
                "project_placeholders",
                "fail" if has_placeholder else "pass",
                "Unresolved placeholders found." if has_placeholder else "No unresolved placeholders found.",
                relative_path,
            )
        )
    return results


def _check_sql_policy(root: Path, config: dict[str, Any]) -> list[CheckResult]:
    analysis_config_path = resolve_project_path(root, config["runtime"]["analysis_config"])
    if not analysis_config_path.exists():
        return [check("readonly_sql", "fail", "Analysis configuration is missing.", config["runtime"]["analysis_config"])]
    analysis_config = load_yaml(analysis_config_path)
    readonly = bool(analysis_config.get("analysis", {}).get("readonly_sql", True))
    if not readonly:
        return [check("readonly_sql", "warn", "Read-only SQL policy is disabled in analysis_config.yaml.")]

    results: list[CheckResult] = []
    for path in sorted((root / "sql").rglob("*.sql")):
        relative = path.relative_to(root)
        has_write = contains_write_statement(path.read_text(encoding="utf-8"))
        results.append(
            check(
                "readonly_sql",
                "fail" if has_write else "pass",
                "Write or DDL keyword found under read-only policy."
                if has_write
                else "SQL satisfies the conservative read-only keyword check.",
                relative,
            )
        )
    return results or [check("readonly_sql", "pass", "No SQL files require policy validation.")]


def _tracked_sensitive_files(root: Path) -> list[str] | None:
    try:
        completed = subprocess.run(
            ["git", "ls-files", "--", ".env", "configs/database.yaml"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def _check_sensitive_files(root: Path) -> list[CheckResult]:
    tracked = _tracked_sensitive_files(root)
    if tracked is None:
        return [
            check(
                "sensitive_files",
                "warn",
                "Git tracking information is unavailable; inspect private files before committing.",
            )
        ]
    return [
        check(
            "sensitive_files",
            "fail" if tracked else "pass",
            f"Sensitive files are tracked by Git: {', '.join(tracked)}"
            if tracked
            else "No known private configuration files are tracked by Git.",
        )
    ]


def _check_report_inputs(root: Path, config: dict[str, Any]) -> list[CheckResult]:
    if not config["deliverables"]["final_report"]:
        return [check("report_inputs_schema", "pass", "Final report inputs are not requested.")]
    relative_path = config["paths"]["report_inputs"]
    path = resolve_project_path(root, relative_path)
    if not path.exists():
        status = "pass" if config["project"]["mode"] == "template" else "warn"
        return [check("report_inputs_schema", status, "Report inputs have not been generated yet.", relative_path)]

    try:
        data = load_yaml(path)
        validate_against_schema(
            data,
            root / "schemas/report_inputs.schema.yaml",
            label=relative_path,
        )
    except (ConfigError, FileNotFoundError) as exc:
        return [check("report_inputs_schema", "fail", str(exc), relative_path)]

    insights_enabled = bool(data.get("insights", {}).get("enabled", False))
    if insights_enabled and not config["deliverables"]["insights"]:
        return [
            check(
                "report_inputs_schema",
                "fail",
                "Report inputs enable insights without explicit project-level approval.",
                relative_path,
            )
        ]
    return [check("report_inputs_schema", "pass", "Report inputs satisfy the schema.", relative_path)]


def _check_status_template(root: Path) -> list[CheckResult]:
    relative_path = ".harness/status.template.yaml"
    path = root / relative_path
    if not path.exists():
        return [check("status_schema", "fail", "Status template is missing.", relative_path)]
    try:
        validate_against_schema(
            load_yaml(path),
            root / "schemas/status.schema.yaml",
            label="status template",
        )
    except (ConfigError, FileNotFoundError) as exc:
        return [check("status_schema", "fail", str(exc), relative_path)]
    return [check("status_schema", "pass", "Status template satisfies its schema.", relative_path)]


def validate_project(project_root: str | Path, *, stage: str | None = None) -> ValidationReport:
    """Run structural, configuration, Notebook, SQL, and safety checks."""
    root = Path(project_root).resolve()
    results: list[CheckResult] = []
    try:
        config = validate_project_config(root)
    except (ConfigError, FileNotFoundError, ImportError) as exc:
        return ValidationReport([check("project_config", "fail", str(exc), "project.yaml")])

    results.append(check("project_config", "pass", "project.yaml satisfies its schema.", "project.yaml"))
    results.extend(_check_required_paths(root, config))
    analysis_config_path = resolve_project_path(root, config["runtime"]["analysis_config"])
    if analysis_config_path.exists():
        analysis_config = load_yaml(analysis_config_path)
        analysis_name = analysis_config.get("project", {}).get("name")
        names_match = analysis_name == config["project"]["name"]
        results.append(
            check(
                "project_name_consistency",
                "pass" if names_match else "fail",
                "Project name matches analysis_config.yaml."
                if names_match
                else f"Project name differs: project.yaml={config['project']['name']!r}, analysis_config.yaml={analysis_name!r}.",
                config["runtime"]["analysis_config"],
            )
        )
    else:
        results.append(
            check(
                "project_name_consistency",
                "fail",
                "Analysis configuration is missing.",
                config["runtime"]["analysis_config"],
            )
        )
    results.extend(_check_notebook(root, config))
    results.extend(_check_placeholders(root, config))
    results.extend(_check_sql_policy(root, config))
    results.extend(_check_sensitive_files(root))
    results.extend(_check_report_inputs(root, config))
    results.extend(_check_status_template(root))
    from .contracts import validate_contracts
    results.extend(validate_contracts(root, config))
    from .planning import validate_progress
    results.extend(validate_progress(root, config))
    if stage is not None and not any(item.status == "fail" for item in results):
        from .workflow import evaluate_stage
        try:
            results.extend(evaluate_stage(root, config, stage))
        except (ConfigError, FileNotFoundError, ValueError, KeyError, TypeError) as exc:
            results.append(check("stage_exit", "fail", str(exc), ".harness/workflow.yaml"))
    return ValidationReport(results)


def format_report(report: ValidationReport) -> str:
    """Render checks for terminal users without losing machine-readable status."""
    symbols = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "unverified": "UNVERIFIED"}
    lines = []
    for result in report.checks:
        suffix = f" ({result.path})" if result.path else ""
        lines.append(f"[{symbols[result.status]}] [{result.category}] {result.code}: {result.message}{suffix}")
    summary = report.as_dict()["summary"]
    lines.append(
        f"Summary: {summary['pass']} passed, {summary['warn']} warnings, {summary['fail']} failed, {summary['unverified']} unverified"
    )
    return "\n".join(lines)


def write_report(path: str | Path, report: ValidationReport) -> None:
    """Persist a validation or audit report as JSON."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
