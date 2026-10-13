"""Create a concrete analysis project from this template repository."""

from __future__ import annotations

import shutil
import re
from pathlib import Path

from .config import load_project_config, load_yaml, resolve_project_path, write_yaml
from .notebook import generate_notebook


TEMPLATE_ROOT = Path(__file__).resolve().parents[2]
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


def _copy_template(source: Path, target: Path) -> None:
    """Only ship files explicitly owned by the framework distribution."""
    manifest = load_yaml(source / ".harness/template_files.yaml")
    paths = manifest.get("files", [])
    if not paths or len(set(paths)) != len(paths):
        raise ValueError("Template file manifest must contain a nonempty, unique file list.")
    files = [(resolve_project_path(source, relative), resolve_project_path(target, relative)) for relative in paths]
    if any(not path.is_file() for path, _ in files):
        raise FileNotFoundError("A declared framework template file is missing.")
    for source_path, destination in files:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination)


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
    if load_project_config(source)["project"]["mode"] != "template":
        raise ValueError("Initialize from a framework in template mode, not from an existing business project.")
    target = Path(output_dir).resolve()
    if target == source or _is_within(target, source):
        raise ValueError("Output directory must be outside the template repository.")
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {target}")

    _copy_template(source, target)

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
    config["runtime"].pop("notebook_template", None)
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

    # A new analysis owns its own history; framework changes are not inherited as project changes.
    (target / "docs/change_execution_log.md").write_text(
        "# 需求变更执行记录\n\n本项目的变更记录从初始化开始；使用规范见 `09_change_management_standard.md`。\n\n## 变更记录\n", encoding="utf-8",
    )
    (target / "docs/framework_issue_log.md").write_text(
        "# 框架使用问题与迭代记录\n\n仅记录本项目发现的通用框架缺陷，业务问题记录在项目契约或质量结果中。\n\n"
        "| Issue ID | 问题与证据 | 根因/处理建议 | Change ID | 状态 |\n| --- | --- | --- | --- | --- |\n", encoding="utf-8",
    )
    (target / "README.md").write_text(
        f"# {display_name}\n\n本项目由标准数据分析流程框架初始化。\n\n"
        "先阅读 `docs/framework_usage.md`，填写 `docs/analysis_framework.md`、报告结构和 `configs/project_contracts.yaml`。\n"
        "业务逻辑放在项目 `src/`，由 `notebooks/main_analysis.ipynb` 调用；框架工具位于 `src/project_harness/`。\n",
        encoding="utf-8",
    )

    plan_path = resolve_project_path(target, config["paths"].get("plan", "docs/project_plan.yaml"))
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(target / "docs/project_plan_template.yaml", plan_path)
    from .planning import write_progress
    write_progress(target, config)

    generate_notebook(target)
    return target
