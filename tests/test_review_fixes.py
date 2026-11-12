"""Regression tests for the review fixes (template-mode framework self-checks)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.project_harness.audit import _report_links
from src.project_harness.config import (
    ConfigError,
    load_project_config,
    resolve_report_formats,
    write_yaml,
)
from src.project_harness.contracts import check_detail_sections
from src.project_harness.execution import execute_notebook
from src.project_harness.scaffold import initialize_project
from src.project_harness.validation import validate_project
from src.quality import run_table_checks
from src.reporting.report import _slug, render_detail_html, render_summary_markdown

ROOT = Path(__file__).resolve().parents[1]

if load_project_config(ROOT)["project"]["mode"] != "template":
    pytest.skip(
        "Framework self-check tests only run in the framework template repository.",
        allow_module_level=True,
    )


@pytest.fixture
def project(tmp_path):
    return initialize_project(tmp_path / "analysis", name="review", display_name="审阅修复", source_root=ROOT)


def _prepare_documents(root: Path) -> None:
    config = load_project_config(root)
    (root / config["paths"]["analysis_framework"]).write_text("# 框架\n范围。", encoding="utf-8")
    (root / config["paths"]["report_structure"]).write_text("# 结构\nQ1。", encoding="utf-8")


def test_required_paths_cover_delivery_script_and_governance_documents(project):
    _prepare_documents(project)
    for relative in (
        "scripts/generate_final_report.py",
        "docs/09_change_management_standard.md",
        "docs/framework_issue_log.md",
        "docs/script_catalog.md",
    ):
        (project / relative).unlink()
    report = validate_project(project)
    failed = {item.path for item in report.checks if item.code == "required_path" and item.status == "fail"}
    assert {
        "scripts/generate_final_report.py",
        "docs/09_change_management_standard.md",
        "docs/framework_issue_log.md",
        "docs/script_catalog.md",
    } <= failed


def test_required_paths_reject_a_directory_shadow(project):
    _prepare_documents(project)
    target = project / "scripts/generate_final_report.py"
    target.unlink()
    target.mkdir()
    report = validate_project(project)
    assert any(item.code == "required_path" and item.path == "scripts/generate_final_report.py" and item.status == "fail" for item in report.checks)


def test_malformed_analysis_config_is_reported_instead_of_crashing(project):
    _prepare_documents(project)
    (project / "configs/analysis_config.yaml").write_text("project: [unclosed\n", encoding="utf-8")
    report = validate_project(project)
    assert not report.passed
    assert any(item.code == "project_config" and item.status == "fail" for item in report.checks)


def test_directory_in_place_of_document_is_reported_instead_of_crashing(project):
    _prepare_documents(project)
    path = project / load_project_config(project)["paths"]["analysis_framework"]
    path.unlink()
    path.mkdir()
    report = validate_project(project)
    assert any(item.code == "project_placeholders" and item.status == "fail" for item in report.checks)


def test_non_ascii_report_assets_resolve_after_url_decoding(tmp_path):
    figure = tmp_path / "reports/figures/留存 趋势.png"
    figure.parent.mkdir(parents=True)
    figure.write_bytes(b"png")
    detail = tmp_path / "reports/final/analysis_detail.html"
    detail.parent.mkdir(parents=True)
    detail.write_text("<html></html>", encoding="utf-8")
    data = {
        "project": {"name": "demo", "report_title": "标题", "run_id": "run-1"},
        "summary": {
            "conclusions": ["结论"],
            "key_results": ["结果"],
            "metrics": [],
            "figures": [{"title": "留存趋势", "path": "reports/figures/留存 趋势.png"}],
            "tables": [],
        },
        "business_questions": [],
        "detail": {"sections": []},
        "appendix": {},
    }
    summary = tmp_path / "reports/final/final_analysis_report.md"
    summary.write_text(
        render_summary_markdown(
            data,
            project_root=tmp_path,
            output_path=summary,
            detail_path="reports/final/analysis_detail.html",
        ),
        encoding="utf-8",
    )
    assert _report_links(tmp_path, summary) == []


def test_resolve_report_formats_respects_detail_switch():
    enabled = {"deliverables": {"detail_report": True}}
    disabled = {"deliverables": {"detail_report": False}}
    assert resolve_report_formats("both", enabled) == "both"
    assert resolve_report_formats("both", disabled) == "md"
    with pytest.raises(ConfigError):
        resolve_report_formats("html", disabled)


def test_detail_report_requires_at_least_one_section():
    config = {"deliverables": {"final_report": True, "detail_report": True}, "paths": {}}
    assert check_detail_sections(Path("."), config, {"detail": {"sections": []}})[0].status == "fail"
    assert check_detail_sections(Path("."), config, {"detail": {"sections": [{"id": "D1"}]}})[0].status == "pass"
    assert check_detail_sections(Path("."), {**config, "deliverables": {"final_report": True, "detail_report": False}}, {})[0].status == "pass"


def test_empty_table_fails_unique_and_non_null_checks(tmp_path):
    pd.DataFrame({"id": pd.Series([], dtype="int64")}).to_csv(tmp_path / "empty.csv", index=False)
    rules = [
        {"id": "u", "category": "data", "kind": "unique", "table": "empty.csv", "keys": ["id"], "description": "unique"},
        {"id": "n", "category": "data", "kind": "non_null", "table": "empty.csv", "column": "id", "description": "non-null"},
    ]
    results = run_table_checks(tmp_path, rules)
    assert all(item.status == "fail" for item in results)


def test_executed_notebook_cannot_overwrite_source(project):
    _prepare_documents(project)
    config = load_project_config(project)
    with pytest.raises(ValueError, match="source Notebook"):
        execute_notebook(project, output_path=config["runtime"]["notebook"])


def test_generated_readme_uses_the_project_readme_template(project):
    text = (project / "README.md").read_text(encoding="utf-8")
    assert text.startswith("# 审阅修复")
    assert "## 5. 数据来源" in text
    assert "docs/analysis_framework.md" in text


def test_non_ascii_section_ids_get_unique_anchors():
    assert _slug("D1") == "d1"
    assert _slug("数据质量") != _slug("分析结论")
    assert _slug("数据质量").startswith("section-")


def test_summary_tables_are_rendered_in_detail_overview(tmp_path):
    detail = render_detail_html(
        {
            "project": {"name": "demo", "run_id": "run-1"},
            "summary": {
                "conclusions": ["结论"],
                "key_results": ["结果"],
                "metrics": [],
                "figures": [],
                "tables": [{"title": "年度结果", "path": "reports/tables/retention.csv"}],
            },
            "business_questions": [],
            "detail": {"sections": []},
            "appendix": {},
        },
        project_root=tmp_path,
        output_path=tmp_path / "reports/final/analysis_detail.html",
        summary_path=tmp_path / "reports/final/final_analysis_report.md",
    )
    assert "关键结果表" in detail
    assert "年度结果" in detail


def test_analysis_config_schema_rejects_bad_seed(project):
    _prepare_documents(project)
    config = load_project_config(project)
    path = project / config["runtime"]["analysis_config"]
    data = {
        "project": {"name": "review", "timezone": "Asia/Shanghai", "random_seed": "not-an-int"},
        "analysis": {"readonly_sql": True},
        "paths": {"data_raw": "data/raw"},
    }
    write_yaml(path, data)
    report = validate_project(project)
    assert any(item.code == "project_config" and item.status == "fail" for item in report.checks)
