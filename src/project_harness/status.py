"""Persistent local status for notebook-first analysis runs."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import load_project_config, load_yaml, validate_against_schema, write_yaml


STATUS_PATH = Path(".harness/status.yaml")
STATUS_TEMPLATE_PATH = Path(".harness/status.template.yaml")


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def load_status(project_root: str | Path) -> dict[str, Any]:
    """Load local status, falling back to the committed status template."""
    root = Path(project_root).resolve()
    status_path = root / STATUS_PATH
    if status_path.exists():
        return load_yaml(status_path)

    template_path = root / STATUS_TEMPLATE_PATH
    status = load_yaml(template_path) if template_path.exists() else {"schema_version": 1}
    config = load_project_config(root)
    status["project_name"] = config["project"]["name"]
    return status


def update_status(
    project_root: str | Path,
    *,
    current_stage: str | None = None,
    completed_stage: str | None = None,
    last_run_id: str | None = None,
    last_run_status: str | None = None,
    remaining_risks: list[str] | None = None,
) -> dict[str, Any]:
    """Update the local current status without changing the project contract."""
    root = Path(project_root).resolve()
    status = load_status(root)
    completed = list(status.get("completed_stages") or [])
    if completed_stage and completed_stage not in completed:
        completed.append(completed_stage)

    if current_stage is not None:
        status["current_stage"] = current_stage
    if last_run_id is not None:
        status["last_run_id"] = last_run_id
    if last_run_status is not None:
        status["last_run_status"] = last_run_status
    if remaining_risks is not None:
        status["remaining_risks"] = remaining_risks
    status["completed_stages"] = completed
    status["updated_at"] = utc_now()
    validate_against_schema(
        status,
        root / "schemas/status.schema.yaml",
        label="local project status",
    )
    write_yaml(root / STATUS_PATH, status)
    return status
