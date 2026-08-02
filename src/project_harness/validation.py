"""Machine-enforced checks derived from the project documentation."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

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
from .notebook import DEFAULT_TEMPLATE, enabled_section_ids


PLACEHOLDER_PATTERN = re.compile(r"待填写|\bTODO\b|\bTBD\b", re.IGNORECASE)
WRITE_SQL_PATTERN = re.compile(
    r"\b(insert|update|delete|drop|truncate|create|alter|replace|merge|grant|revoke)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CheckResult:
    """One validation or audit result."""

    code: str
    status: str
    message: str
    path: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationReport:
    """Collection of machine-readable checks."""

    checks: list[CheckResult]

    @property
    def passed(self) -> bool:
        return not any(check.status == "fail" for check in self.checks)

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "summary": {
                status: sum(check.status == status for check in self.checks)
                for status in ("pass", "warn", "fail")
            },
            "checks": [check.as_dict() for check in self.checks],
        }


def check(
    code: str,
    status: str,
    message: str,
    path: str | Path | None = None,
) -> CheckResult:
    """Build a normalized validation result."""
    return CheckResult(code=code, status=status, message=message, path=str(path) if path else None)


def _required_paths(config: dict[str, Any]) -> list[str]:
    common = [
        "README.md",
        "agent.md",
        "project.yaml",
        "configs/analysis_config.yaml",
        ".harness/workflow.yaml",
        ".harness/status.template.yaml",
        "schemas/project.schema.yaml",
        "schemas/report_inputs.schema.yaml",
        "schemas/run_manifest.schema.yaml",
        "schemas/status.schema.yaml",
        "templates/notebook_sections.yaml",
        config["runtime"]["notebook"],
        "scripts/init_project.py",
        "scripts/generate_notebook.py",
        "scripts/validate_project.py",
        "scripts/run_notebook.py",
        "scripts/audit_project.py",
    ]
    if config["project"]["mode"] == "project":
        common.extend(
            [
                config["paths"]["analysis_framework"],
                config["paths"]["report_structure"],
            ]
        )
    else:
        common.extend(
            [
                "docs/analysis_framework_template.md",
                "docs/final_report_structure_template.md",
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
    notebook_path = resolve_project_path(root, config["runtime"]["notebook"])
    if not notebook_path.exists():
        return [check("notebook_structure", "fail", "Main Notebook is missing.", config["runtime"]["notebook"])]

    notebook = nbformat.read(notebook_path, as_version=4)
    template = load_yaml(root / DEFAULT_TEMPLATE)
    expected_sections = enabled_section_ids(config, template)
    actual_sections = list(notebook.metadata.get("harness", {}).get("sections", []))
    results = [
        check(
            "notebook_sections",
            "pass" if actual_sections == expected_sections else "fail",
            "Notebook sections match project.yaml."
            if actual_sections == expected_sections
            else f"Notebook sections are stale. Expected {expected_sections}, got {actual_sections}.",
            config["runtime"]["notebook"],
        )
    ]
    code_source = "\n".join(cell.source for cell in notebook.cells if cell.cell_type == "code")
    results.append(
        check(
            "notebook_reuses_src",
            "pass" if "from src." in code_source or "import src." in code_source else "fail",
            "Notebook calls reusable logic from src/."
            if "from src." in code_source or "import src." in code_source
            else "Notebook must call reusable logic from src/.",
            config["runtime"]["notebook"],
        )
    )
    return results


def _check_placeholders(root: Path, config: dict[str, Any]) -> list[CheckResult]:
    if config["project"]["mode"] == "template":
        return [check("project_placeholders", "pass", "Template mode permits placeholders in source templates.")]

    paths = [config["paths"]["analysis_framework"], config["paths"]["report_structure"]]
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


def _strip_sql_literals_and_comments(sql: str) -> str:
    sql = re.sub(r"'(?:''|[^'])*'", "''", sql)
    sql = re.sub(r'"(?:""|[^"])*"', '""', sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"(--|#).*?$", " ", sql, flags=re.MULTILINE)
    return sql


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
        normalized = _strip_sql_literals_and_comments(path.read_text(encoding="utf-8"))
        has_write = bool(WRITE_SQL_PATTERN.search(normalized))
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


def validate_project(project_root: str | Path) -> ValidationReport:
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
    return ValidationReport(results)


def format_report(report: ValidationReport) -> str:
    """Render checks for terminal users without losing machine-readable status."""
    symbols = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}
    lines = []
    for result in report.checks:
        suffix = f" ({result.path})" if result.path else ""
        lines.append(f"[{symbols[result.status]}] {result.code}: {result.message}{suffix}")
    summary = report.as_dict()["summary"]
    lines.append(
        f"Summary: {summary['pass']} passed, {summary['warn']} warnings, {summary['fail']} failed"
    )
    return "\n".join(lines)


def write_report(path: str | Path, report: ValidationReport) -> None:
    """Persist a validation or audit report as JSON."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
