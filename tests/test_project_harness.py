from __future__ import annotations

import shutil
from pathlib import Path

import nbformat
import pandas as pd
import pytest

from src.project_harness.audit import audit_project
from src.project_harness.config import ConfigError, load_project_config, validate_project_config, write_yaml
from src.project_harness.notebook import generate_notebook
from src.project_harness.scaffold import initialize_project
from src.project_harness.validation import validate_project
from src.quality import build_quality_summary
from src.reporting import export_dataframe, write_report_inputs


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _copy_notebook_contract(target: Path) -> dict:
    (target / "schemas").mkdir(parents=True)
    (target / "templates").mkdir(parents=True)
    shutil.copyfile(PROJECT_ROOT / "schemas/project.schema.yaml", target / "schemas/project.schema.yaml")
    shutil.copyfile(
        PROJECT_ROOT / "templates/notebook_sections.yaml",
        target / "templates/notebook_sections.yaml",
    )
    config = load_project_config(PROJECT_ROOT)
    write_yaml(target / "project.yaml", config)
    return config


def test_project_contract_is_valid() -> None:
    config = validate_project_config(PROJECT_ROOT)
    assert config["project"]["mode"] == "template"
    assert config["runtime"]["notebook"] == "notebooks/main_analysis.ipynb"


def test_project_contract_rejects_path_outside_project(tmp_path: Path) -> None:
    config = _copy_notebook_contract(tmp_path)
    config["runtime"]["notebook"] = "../outside.ipynb"
    write_yaml(tmp_path / "project.yaml", config)

    with pytest.raises(ConfigError):
        validate_project_config(tmp_path)


def test_notebook_sections_follow_module_configuration(tmp_path: Path) -> None:
    config = _copy_notebook_contract(tmp_path)
    config["modules"]["statistics"] = True
    config["modules"]["modeling"] = True
    write_yaml(tmp_path / "project.yaml", config)

    notebook_path = generate_notebook(tmp_path)
    notebook = nbformat.read(notebook_path, as_version=4)
    sections = notebook.metadata["harness"]["sections"]

    assert "statistical_analysis" in sections
    assert "modeling" in sections
    assert "database" not in sections


def test_initialize_project_applies_presets(tmp_path: Path) -> None:
    output = tmp_path / "generated_project"
    initialize_project(
        output,
        name="retention_analysis",
        display_name="用户留存分析",
        analysis_type="statistical_analysis",
        data_source="database",
        source_root=PROJECT_ROOT,
    )

    config = validate_project_config(output)
    notebook = nbformat.read(output / config["runtime"]["notebook"], as_version=4)
    sections = notebook.metadata["harness"]["sections"]

    assert config["project"]["mode"] == "project"
    assert config["modules"]["database"] is True
    assert config["modules"]["statistics"] is True
    assert config["modules"]["modeling"] is False
    assert "database" in sections
    assert "statistical_analysis" in sections
    assert "modeling" not in sections
    assert (output / "docs/analysis_framework.md").exists()
    assert (output / "reports/final/final_report_structure.md").exists()
    assert not (output / ".harness/status.yaml").exists()
    assert not (output / "logs/runs").exists()

    preflight = validate_project(output)
    assert not preflight.passed
    assert any(
        item.code == "project_placeholders" and item.status == "fail"
        for item in preflight.checks
    )


def test_quality_summary_and_exports(tmp_path: Path) -> None:
    dataframe = pd.DataFrame({"id": [1, 1, 3], "value": [10, None, 30]})
    summary = build_quality_summary(dataframe, primary_key="id")

    statuses = dict(zip(summary["check"], summary["status"]))
    assert statuses["primary_key_duplicates"] == "fail"
    assert statuses["missing_cells"] == "warn"

    table_path = export_dataframe(summary, tmp_path / "reports/tables/quality.csv")
    inputs_path = write_report_inputs(
        {"project": {"name": "demo"}},
        tmp_path / "reports/final/report_inputs.yaml",
    )
    assert table_path.exists()
    assert inputs_path.exists()


def test_template_scaffold_passes_validation_and_audit() -> None:
    validation = validate_project(PROJECT_ROOT)
    audit = audit_project(PROJECT_ROOT)

    assert validation.passed
    assert audit.passed
    assert any(check.status == "warn" for check in audit.checks)
