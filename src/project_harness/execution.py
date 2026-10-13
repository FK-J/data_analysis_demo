"""Headless Notebook execution with recoverable run manifests."""

from __future__ import annotations

import json
import subprocess
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

try:
    import nbformat
    from nbclient import NotebookClient
except ImportError as exc:  # pragma: no cover
    raise ImportError("Missing Notebook runtime. Install it with: pip install nbformat nbclient") from exc

from .config import resolve_project_path, validate_against_schema, validate_project_config
from .notebook import write_notebook
from .status import update_status
from .provenance import input_fingerprints, output_fingerprints


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]


def _git_commit(root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def _write_manifest(path: Path, manifest: dict[str, Any], root: Path) -> None:
    validate_against_schema(
        manifest,
        root / "schemas/run_manifest.schema.yaml",
        label="run manifest",
    )
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def execute_notebook(
    project_root: str | Path,
    *,
    output_path: str | Path | None = None,
    preflight_checks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute the configured main Notebook and always preserve its run manifest."""
    root = Path(project_root).resolve()
    config = validate_project_config(root)
    notebook_path = resolve_project_path(root, config["runtime"]["notebook"])
    run_id = _run_id()
    run_dir = root / "logs" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    executed_path = (
        resolve_project_path(root, output_path)
        if output_path is not None
        else run_dir / "executed_main_analysis.ipynb"
    )
    executed_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "manifest.json"

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "project_name": config["project"]["name"],
        "status": "running",
        "started_at": _timestamp(),
        "finished_at": None,
        "notebook": notebook_path.relative_to(root).as_posix(),
        "executed_notebook": executed_path.relative_to(root).as_posix(),
        "git_commit": _git_commit(root),
        "error": None,
        "checks": preflight_checks or [],
        "artifacts": [],
        "input_fingerprints": input_fingerprints(root, config),
        "output_fingerprints": {},
        "report_fingerprints": {},
    }
    _write_manifest(manifest_path, manifest, root)
    update_status(root, last_run_id=run_id, last_run_status="running")

    notebook = nbformat.v4.new_notebook()
    try:
        notebook = nbformat.read(notebook_path, as_version=4)
        # Only the executed copy receives this context; source Notebook remains untouched.
        notebook.cells.insert(0, nbformat.v4.new_code_cell(
            f"import os\nos.environ['ANALYSIS_RUN_ID'] = {run_id!r}",
            metadata={"tags": ["harness-run-context"]},
        ))
        client = NotebookClient(
            notebook,
            timeout=int(config["runtime"]["notebook_timeout_seconds"]),
            kernel_name=config["runtime"]["notebook_kernel"],
            resources={"metadata": {"path": str(root)}},
        )
        client.execute()
        if config["project"]["mode"] == "project":
            from .workflow import evaluate_stage
            stage_checks = evaluate_stage(root, config, "analyzed")
            manifest["checks"].extend(item.as_dict() for item in stage_checks)
            if any(item.status in {"fail", "unverified"} for item in stage_checks):
                raise ValueError("Analysis stage did not pass: " + "; ".join(item.message for item in stage_checks if item.status in {"fail", "unverified"}))
        if input_fingerprints(root, config) != manifest["input_fingerprints"]:
            raise ValueError("Registered inputs, code or contracts changed during execution; rerun with stable inputs.")
        manifest["status"] = "passed"
        manifest["artifacts"].append(executed_path.relative_to(root).as_posix())
        update_status(
            root,
            current_stage="validated",
            completed_stage="validated",
            last_run_id=run_id,
            last_run_status="passed",
        )
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["error"] = "".join(traceback.format_exception_only(type(exc), exc)).strip()
        update_status(root, last_run_id=run_id, last_run_status="failed")
    finally:
        write_notebook(notebook, executed_path)
        try:
            manifest["output_fingerprints"] = output_fingerprints(root, config, executed_path)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            manifest["status"] = "failed"
            manifest["error"] = manifest["error"] or str(exc)
            update_status(root, last_run_id=run_id, last_run_status="failed")
        manifest["finished_at"] = _timestamp()
        _write_manifest(manifest_path, manifest, root)

    return {"manifest": manifest, "manifest_path": manifest_path, "executed_notebook": executed_path}
