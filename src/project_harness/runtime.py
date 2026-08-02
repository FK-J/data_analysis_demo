"""Runtime preparation called by the generated main Notebook."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import numpy as np

from .config import load_yaml, resolve_project_path, validate_project_config
from .status import update_status


def prepare_notebook_context(project_root: str | Path) -> dict[str, Any]:
    """Validate configuration, initialize deterministic state, and prepare output paths."""
    root = Path(project_root).resolve()
    project_config = validate_project_config(root)
    analysis_config_path = resolve_project_path(root, project_config["runtime"]["analysis_config"])
    analysis_config = load_yaml(analysis_config_path)

    random_seed = int(analysis_config.get("project", {}).get("random_seed", 42))
    random.seed(random_seed)
    np.random.seed(random_seed)

    for relative_path in analysis_config.get("paths", {}).values():
        resolve_project_path(root, relative_path).mkdir(parents=True, exist_ok=True)
    for key in ("report_inputs", "final_report"):
        resolve_project_path(root, project_config["paths"][key]).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    if project_config["project"]["mode"] == "project":
        required = (
            project_config["paths"]["analysis_framework"],
            project_config["paths"]["report_structure"],
        )
        missing = [path for path in required if not resolve_project_path(root, path).exists()]
        if missing:
            raise FileNotFoundError("Required confirmed project artifacts are missing: " + ", ".join(missing))

    update_status(root, current_stage="discovery", completed_stage="discovery")
    return {
        "project_root": root,
        "project_config": project_config,
        "analysis_config": analysis_config,
        "random_seed": random_seed,
    }
