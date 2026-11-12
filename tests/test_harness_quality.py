"""Regression tests for the framework quality gates fixed during review."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.io import load_table
from src.project_harness.config import load_project_config, write_yaml
from src.project_harness.execution import success_stage_updates
from src.project_harness.planning import validate_progress
from src.project_harness.scaffold import initialize_project
from src.project_harness.validation import validate_project
from src.quality import run_table_checks
from src.reporting.report import render_summary_markdown

ROOT = Path(__file__).resolve().parents[1]

if load_project_config(ROOT)["project"]["mode"] != "template":
    pytest.skip(
        "Framework self-check tests only run in the framework template repository.",
        allow_module_level=True,
    )


@pytest.fixture
def scaffold(tmp_path):
    return initialize_project(tmp_path / "analysis", name="quality", display_name="质量门禁", source_root=ROOT)


def test_table_checks_keep_the_declared_category(tmp_path):
    pd.DataFrame({"id": [1, 2]}).to_csv(tmp_path / "table.csv", index=False)
    rules = [{"id": "pk", "category": "data", "kind": "unique", "table": "table.csv", "keys": ["id"], "description": "主键唯一"}]
    results = run_table_checks(tmp_path, rules, category="data")
    assert results[0].status == "pass"
    assert results[0].category == "data"


def test_missing_checks_report_the_requested_category(tmp_path):
    results = run_table_checks(tmp_path, [], category="data")
    assert results[0].status == "unverified"
    assert results[0].category == "data"
    assert results[0].code == "data_checks"


def test_validation_reports_missing_template_instead_of_crashing(scaffold):
    (scaffold / "templates/notebook_sections.yaml").unlink()
    report = validate_project(scaffold)
    assert not report.passed
    assert any(item.code == "notebook_sections" and item.status == "fail" for item in report.checks)


def test_stale_notebook_config_is_detected(scaffold):
    config = load_project_config(scaffold)
    config["project"]["display_name"] = "改名后的项目"
    write_yaml(scaffold / "project.yaml", config)
    report = validate_project(scaffold)
    assert any(
        item.code == "notebook_config_digest" and item.status == "fail" for item in report.checks
    )


def test_stale_notebook_template_is_detected(scaffold):
    template = scaffold / "templates/notebook_sections.yaml"
    template.write_text(template.read_text(encoding="utf-8") + "\n# 模板调整\n", encoding="utf-8")
    report = validate_project(scaffold)
    assert any(
        item.code == "notebook_template_digest" and item.status == "fail" for item in report.checks
    )


def test_progress_survives_a_missing_local_status_file(scaffold):
    config = load_project_config(scaffold)
    (scaffold / ".harness/status.yaml").unlink(missing_ok=True)
    assert validate_progress(scaffold, config)[0].status == "pass"


def test_template_mode_does_not_claim_a_validated_stage():
    assert success_stage_updates({"project": {"mode": "template"}}) == {}
    assert success_stage_updates({"project": {"mode": "project"}}) == {
        "current_stage": "validated",
        "completed_stage": "validated",
    }


def test_load_table_reads_csv(tmp_path):
    path = tmp_path / "table.csv"
    pd.DataFrame({"a": [1, 2]}).to_csv(path, index=False)
    assert list(load_table(path).columns) == ["a"]


def test_summary_links_relative_detail_path_from_project_root(tmp_path):
    data = {
        "project": {"name": "demo", "report_title": "标题"},
        "summary": {"conclusions": ["结论"], "metrics": [], "figures": []},
        "business_questions": [],
        "detail": {"sections": []},
        "appendix": {},
    }
    report = render_summary_markdown(
        data,
        project_root=tmp_path,
        output_path=tmp_path / "reports/final/final_analysis_report.md",
        detail_path="reports/final/analysis_detail.html",
    )
    assert "](analysis_detail.html)" in report
