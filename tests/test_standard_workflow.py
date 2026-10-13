from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import nbformat
import pandas as pd
import pytest

from src.project_harness.audit import audit_project
from src.project_harness.config import ConfigError, load_project_config, load_yaml, write_yaml
from src.project_harness.contracts import load_contracts
from src.project_harness.execution import execute_notebook
from src.project_harness.notebook import generate_notebook
from src.project_harness.provenance import latest_run, verify_run
from src.project_harness.scaffold import initialize_project
from src.project_harness.validation import validate_project
from src.quality import run_table_checks


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def project(tmp_path):
    root = initialize_project(tmp_path / "analysis", name="retention", display_name="客户留存", source_root=ROOT)
    config = load_project_config(root)
    config["deliverables"]["figures"] = False
    write_yaml(root / "project.yaml", config)
    (root / config["paths"]["analysis_framework"]).write_text("# 客户留存\n客户为账号，年度结果用于复盘。", encoding="utf-8")
    (root / config["paths"]["report_structure"]).write_text("# 报告结构\nQ1：展示年度流失人数与比例。", encoding="utf-8")
    pd.DataFrame({"customer": ["a", "b", "c"], "lost": [1, 0, 0]}).to_csv(root / "data/raw/customers.csv", index=False)
    contracts = {
        "schema_version": 1,
        "decisions": [{"id": "D1", "decision": "以客户账号为分析单位", "status": "confirmed", "owner": "分析负责人", "evidence": "已确认的项目范围", "resolve_by_stage": "spec_confirmed", "impact": "客户规模和分母"}],
        "sources": [{"id": "customers", "path": "data/raw/customers.csv", "grain": "客户账号", "primary_key": ["customer"], "missing_semantics": "结果标签完整", "time_semantics": "年度结果", "uses": ["Q1"], "status": "usable", "reason": "", "evidence": "抽样和完整性复核"}],
        "metrics": [{"id": "loss_rate", "name": "流失率", "grain": "客户账号", "population": "本轮全部客户", "numerator": "流失账号", "denominator": "全部账号", "time_window": "本年度", "version": "1"}],
        "checks": [
            {"id": "unique", "category": "data", "kind": "unique", "table": "data/raw/customers.csv", "keys": ["customer"], "description": "原始账号唯一"},
            {"id": "reconcile", "category": "analysis", "kind": "sum_equals", "table": "reports/tables/retention.csv", "column": "lost", "other_table": "data/raw/customers.csv", "other_column": "lost", "description": "流失总量对账"},
            {"id": "bound", "category": "analysis", "kind": "column_relation", "table": "reports/tables/retention.csv", "column": "lost", "other_column": "total", "operator": "le", "description": "分子不大于分母"},
        ],
        "report_requirements": [{"id": "Q1", "title": "年度客户留存", "required": True}],
    }
    write_yaml(root / config["paths"]["contracts"], contracts)
    from src.project_harness.planning import register_change, write_progress
    with (root / "docs/change_execution_log.md").open("a", encoding="utf-8") as stream:
        stream.write("\n### CHANGE-20261013-01：客户留存分析\n\n- 需求：年度留存分析\n")
    register_change(root, config, "CHANGE-20261013-01", "客户留存分析", ["T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08"])
    write_progress(root, config)
    generate_notebook(root)
    return root


def install_analysis(root, *, fail=False):
    config = load_project_config(root)
    notebook_path = root / config["runtime"]["notebook"]
    notebook = nbformat.read(notebook_path, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.source = "pass"
    inputs = {
        "project": {"name": "retention", "report_title": "客户留存分析", "analysis_framework_path": config["paths"]["analysis_framework"], "report_structure_path": config["paths"]["report_structure"], "notebook_path": config["runtime"]["notebook"]},
        "summary": {"section_goal": "展示客户留存", "key_results": ["年度流失结果"], "metrics": [{"id": "loss_rate", "name": "流失率", "value": 1 / 3, "format": "percent", "source": {"path": "reports/tables/retention.csv", "column": "rate", "tolerance": 1e-12}, "note": "账号粒度"}], "figures": [], "tables": [{"title": "年度结果", "path": "reports/tables/retention.csv"}]},
        "business_questions": [{"id": "Q1", "title": "年度留存", "section_goal": "展示年度结果", "analysis_logic": "汇总完整客户名单", "key_results": ["年度结果见表"], "figures": [], "tables": [], "notes": ["客户账号粒度"]}],
        "appendix": {"data_scope": ["本轮客户"], "metric_definitions": ["流失账号除以全部账号"], "output_files": ["reports/tables/retention.csv"]},
        "coverage": [{"id": "Q1", "status": "covered", "evidence": ["reports/tables/retention.csv"]}],
    }
    first = next(cell for cell in notebook.cells if cell.cell_type == "code")
    first.source = (
        "from pathlib import Path\nimport pandas as pd\n"
        "from src.reporting import export_dataframe, write_report_inputs\n"
        "raw = pd.read_csv('data/raw/customers.csv')\n"
        "result = pd.DataFrame({'lost': [raw.lost.sum()], 'total': [len(raw)], 'rate': [raw.lost.mean()]})\n"
        "export_dataframe(result, 'reports/tables/retention.csv')\n"
        f"write_report_inputs({inputs!r}, 'reports/final/report_inputs.yaml')\n"
        + ("raise RuntimeError('deliberate failure')\n" if fail else "")
    )
    nbformat.write(notebook, notebook_path)


def test_initialization_does_not_ship_business_files_or_private_state(tmp_path):
    source = tmp_path / "framework"
    shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__", "logs", ".pytest_cache"))
    (source / "logs").mkdir()
    (source / "logs/.gitkeep").touch()
    for relative in (".env", "configs/database.yaml", "src/analysis/school_only.py", "scripts/school_only.py", "docs/business_history.md", "data/raw/private.csv"):
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("private business content", encoding="utf-8")
    root = initialize_project(tmp_path / "new", name="new_analysis", display_name="新分析", source_root=source)
    assert not (root / ".env").exists()
    assert not (root / "configs/database.yaml").exists()
    assert not (root / "src/analysis/school_only.py").exists()
    assert not (root / "scripts/school_only.py").exists()
    assert not (root / "docs/business_history.md").exists()
    assert not (root / "data/raw/private.csv").exists()
    assert "CHANGE-20261013" not in (root / "docs/change_execution_log.md").read_text()
    assert not (root / "logs/runs").exists()


def test_project_template_is_used_by_both_generator_and_validator(project):
    config = load_project_config(project)
    template = load_yaml(project / "templates/notebook_sections.yaml")
    template["sections"].append({"id": "project_extension", "cells": [{"type": "markdown", "source": "业务扩展"}]})
    write_yaml(project / "templates/project_notebook.yaml", template)
    config["runtime"]["notebook_template"] = "templates/project_notebook.yaml"
    write_yaml(project / "project.yaml", config)
    generate_notebook(project)
    report = validate_project(project)
    assert report.passed
    notebook = nbformat.read(project / config["runtime"]["notebook"], as_version=4)
    assert notebook.metadata.harness.template == "templates/project_notebook.yaml"
    assert notebook.metadata.harness.sections[-1] == "project_extension"


def test_preflight_does_not_require_future_outputs(project):
    report = validate_project(project, stage="spec_confirmed")
    assert report.passed
    assert not (project / "reports/tables/retention.csv").exists()
    assert not validate_project(project, stage="analyzed").passed


@pytest.mark.parametrize("mutation", ["pending_decision", "empty_confirmation", "pending_source", "missing_snapshot", "no_checks", "duplicate_id", "placeholder_metric"])
def test_stage_exits_reject_incomplete_business_evidence(project, mutation):
    path = project / "configs/project_contracts.yaml"
    data = load_yaml(path)
    if mutation == "pending_decision":
        data["decisions"][0]["status"] = "pending"
    elif mutation == "empty_confirmation":
        data["decisions"][0]["evidence"] = ""
    elif mutation == "pending_source":
        data["sources"][0]["status"] = "pending"
    elif mutation == "missing_snapshot":
        data["sources"][0]["path"] = "data/raw/missing.csv"
    elif mutation == "no_checks":
        data["checks"] = []
    elif mutation == "duplicate_id":
        data["metrics"].append(data["metrics"][0].copy())
    else:
        data["metrics"][0]["denominator"] = "待填写"
    write_yaml(path, data)
    assert not validate_project(project, stage="analyzed").passed


def test_later_decision_does_not_block_early_work(project):
    path = project / "configs/project_contracts.yaml"
    data = load_yaml(path)
    data["decisions"].append({**data["decisions"][0], "id": "D2", "status": "pending", "evidence": "", "resolve_by_stage": "analyzed"})
    write_yaml(path, data)
    assert validate_project(project, stage="spec_confirmed").passed
    assert not validate_project(project, stage="analyzed").passed


@pytest.mark.parametrize("values", [[1, None], [1, float("inf")], [1, -1]])
def test_numeric_rules_do_not_hide_missing_or_invalid_values(tmp_path, values):
    pd.DataFrame({"value": values}).to_csv(tmp_path / "table.csv", index=False)
    rules = [{"id": "r", "category": "analysis", "kind": "range", "table": "table.csv", "column": "value", "min": 0, "max": 1, "description": "概率范围"}]
    assert run_table_checks(tmp_path, rules)[0].status == "fail"


def test_cross_table_conservation_detects_join_inflation(tmp_path):
    pd.DataFrame({"amount": [10, 20]}).to_csv(tmp_path / "before.csv", index=False)
    pd.DataFrame({"amount": [10, 10, 20]}).to_csv(tmp_path / "after.csv", index=False)
    rules = [{"id": "r", "category": "analysis", "kind": "sum_equals", "table": "before.csv", "column": "amount", "other_table": "after.csv", "other_column": "amount", "description": "关联前后金额守恒"}]
    assert run_table_checks(tmp_path, rules)[0].status == "fail"


def test_rule_rejects_path_escape(project):
    path = project / "configs/project_contracts.yaml"
    data = load_yaml(path)
    data["checks"][0]["table"] = "../outside.csv"
    write_yaml(path, data)
    with pytest.raises(ConfigError):
        load_contracts(project, load_project_config(project))


def test_complete_run_report_and_audit_without_changing_framework(project):
    core = project / "src/project_harness/audit.py"
    before = core.read_bytes()
    install_analysis(project)
    result = execute_notebook(project)
    assert result["manifest"]["status"] == "passed", result["manifest"]["error"]
    inputs = load_yaml(project / "reports/final/report_inputs.yaml")
    assert inputs["project"]["run_id"] == result["manifest"]["run_id"]
    completed = subprocess.run([sys.executable, str(project / "scripts/generate_final_report.py")], cwd=project, text=True, capture_output=True)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = audit_project(project)
    assert report.passed, report.as_dict()
    assert {"engineering", "analysis", "report"}.issubset(report.as_dict()["categories"])
    assert core.read_bytes() == before
    assert validate_project(project, stage="audited").passed
    final_report = project / "reports/final/final_analysis_report.md"
    original_report = final_report.read_text(encoding="utf-8")
    final_report.write_text(original_report + "\n人工修改数字\n", encoding="utf-8")
    assert not audit_project(project).passed
    final_report.write_text(original_report, encoding="utf-8")
    pd.DataFrame({"lost": [99], "total": [3]}).to_csv(project / "reports/tables/retention.csv", index=False)
    assert not audit_project(project).passed


def test_failed_execution_retains_manifest_and_blocks_old_success(project):
    install_analysis(project, fail=True)
    result = execute_notebook(project)
    assert result["manifest"]["status"] == "failed"
    assert "deliberate failure" in result["manifest"]["error"]
    assert result["executed_notebook"].is_file()
    assert latest_run(project)[1]["run_id"] == result["manifest"]["run_id"]
    assert any(item.status == "fail" for item in verify_run(project, load_project_config(project)))


def test_report_coverage_requires_evidence_or_explained_inapplicability(project):
    from src.project_harness.contracts import check_report_coverage
    install_analysis(project)
    (project / "reports/final/report_inputs.yaml").write_text("coverage: []\n", encoding="utf-8")
    config = load_project_config(project)
    contracts = load_contracts(project, config)
    assert check_report_coverage(project, config, contracts)[0].status == "fail"
    write_yaml(project / config["paths"]["report_inputs"], {"coverage": [{"id": "Q1", "status": "not_applicable", "reason": "缺少可回溯数据，本轮排除"}]})
    assert check_report_coverage(project, config, contracts)[0].status == "pass"


def test_report_numeric_value_must_match_result_cell(project):
    from src.project_harness.contracts import check_report_metrics
    pd.DataFrame({"rate": [0.25]}).to_csv(project / "reports/tables/retention.csv", index=False)
    config = load_project_config(project)
    metric = {"id": "loss_rate", "name": "流失率", "value": 0.5, "source": {"path": "reports/tables/retention.csv", "column": "rate"}}
    write_yaml(project / config["paths"]["report_inputs"], {"summary": {"metrics": [metric]}})
    assert check_report_metrics(project, config, load_contracts(project, config))[0].status == "fail"
    metric["value"] = 0.25
    write_yaml(project / config["paths"]["report_inputs"], {"summary": {"metrics": [metric]}})
    assert check_report_metrics(project, config, load_contracts(project, config))[0].status == "pass"


@pytest.mark.parametrize("relative", ["data/raw/customers.csv", "configs/project_contracts.yaml", "src/analysis/__init__.py", "notebooks/main_analysis.ipynb"])
def test_changed_inputs_or_code_invalidate_run(project, relative):
    install_analysis(project)
    result = execute_notebook(project)
    assert result["manifest"]["status"] == "passed", result["manifest"]["error"]
    path = project / relative
    path.write_bytes(path.read_bytes() + b"\n")
    assert any(item.status == "fail" for item in verify_run(project, load_project_config(project)))


def test_no_report_project_can_run_and_audit_without_report_structure(project):
    config = load_project_config(project)
    config["deliverables"]["final_report"] = False
    write_yaml(project / "project.yaml", config)
    (project / config["paths"]["report_structure"]).unlink()
    generate_notebook(project)
    install_analysis(project)
    assert validate_project(project, stage="spec_confirmed").passed
    result = execute_notebook(project)
    assert result["manifest"]["status"] == "passed", result["manifest"]["error"]
    assert audit_project(project).passed


def test_new_run_invalidates_previous_delivery_status(project):
    from src.project_harness.status import load_status, update_status
    update_status(project, last_run_id="old", last_run_status="passed", current_stage="audited", completed_stage="audited")
    update_status(project, last_run_id="new", last_run_status="running")
    status = load_status(project)
    assert status["completed_stages"] == []
    assert status["current_stage"] == "discovery"


def test_business_project_cannot_become_an_implicit_template(project, tmp_path):
    with pytest.raises(ValueError, match="template mode"):
        initialize_project(tmp_path / "new", name="new_analysis", display_name="新分析", source_root=project)


def test_whitespace_is_not_confirmation_evidence(project):
    path = project / "configs/project_contracts.yaml"
    data = load_yaml(path)
    data["decisions"][0]["evidence"] = "   "
    write_yaml(path, data)
    assert not validate_project(project, stage="spec_confirmed").passed
