"""Create a concrete analysis project from this template repository."""

from __future__ import annotations

import shutil
import re
from pathlib import Path

from .config import load_project_config, load_yaml, write_yaml
from .notebook import generate_notebook


TEMPLATE_ROOT = Path(__file__).resolve().parents[2]
IGNORED_NAMES = {
    ".git",
    ".ipynb_checkpoints",
    ".pytest_cache",
    "__pycache__",
    "status.yaml",
}

ANALYSIS_PRESETS = {
    "business_analysis": {"statistics": False, "modeling": False},
    "statistical_analysis": {"statistics": True, "modeling": False},
    "machine_learning": {"statistics": True, "modeling": True},
    "custom": {},
}


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _copy_ignore(directory: str, names: list[str]) -> set[str]:
    ignored = {name for name in names if name in IGNORED_NAMES or name.endswith(".pyc")}
    if Path(directory).name in {"logs", "raw", "interim", "processed", "external", "figures", "tables", "final"}:
        ignored.update(name for name in names if name != ".gitkeep")
    return ignored


def initialize_project(
    output_dir: str | Path,
    *,
    name: str,
    display_name: str,
    analysis_type: str = "business_analysis",
    data_source: str = "local_file",
    source_root: str | Path = TEMPLATE_ROOT,
) -> Path:
    """Copy the template, materialize project artifacts, and generate the main Notebook."""
    if analysis_type not in ANALYSIS_PRESETS:
        raise ValueError(f"Unsupported analysis type: {analysis_type}")
    if data_source not in {"local_file", "database", "mixed"}:
        raise ValueError(f"Unsupported data source: {data_source}")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
        raise ValueError("Project name must use lowercase letters, numbers, and underscores.")
    if not display_name.strip():
        raise ValueError("Display name must not be empty.")

    source = Path(source_root).resolve()
    target = Path(output_dir).resolve()
    if target == source or _is_within(target, source):
        raise ValueError("Output directory must be outside the template repository.")
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {target}")

    shutil.copytree(source, target, dirs_exist_ok=True, ignore=_copy_ignore)

    config = load_project_config(target)
    config["project"].update(
        {
            "name": name,
            "display_name": display_name,
            "mode": "project",
            "analysis_type": analysis_type,
        }
    )
    config["data"]["source_type"] = data_source
    uses_database = data_source in {"database", "mixed"}
    config["modules"]["database"] = uses_database
    config["modules"]["sql"] = uses_database
    config["modules"].update(ANALYSIS_PRESETS[analysis_type])
    write_yaml(target / "project.yaml", config)

    analysis_config_path = target / config["runtime"]["analysis_config"]
    analysis_config = load_yaml(analysis_config_path)
    analysis_config.setdefault("project", {})["name"] = name
    write_yaml(analysis_config_path, analysis_config)

    analysis_framework = target / config["paths"]["analysis_framework"]
    analysis_framework.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(target / "docs/analysis_framework_template.md", analysis_framework)

    report_structure = target / config["paths"]["report_structure"]
    report_structure.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(target / "docs/final_report_structure_template.md", report_structure)

    status_template_path = target / ".harness/status.template.yaml"
    status_template = load_yaml(status_template_path)
    status_template["project_name"] = name
    write_yaml(status_template_path, status_template)

    generate_notebook(target)
    return target
