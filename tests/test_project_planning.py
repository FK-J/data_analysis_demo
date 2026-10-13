from __future__ import annotations

from pathlib import Path

import pytest

from src.project_harness.config import ConfigError, load_project_config, load_yaml, write_yaml
from src.project_harness.planning import change_ids, load_plan, register_change, request_fingerprint, validate_progress, write_progress
from src.project_harness.scaffold import initialize_project
from src.project_harness.status import update_status


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def planned_project(tmp_path):
    root = initialize_project(tmp_path / "analysis", name="analysis", display_name="项目计划示例", source_root=ROOT)
    return root, load_project_config(root)


def log_change(root, identifier="CHANGE-20261013-01", summary="年度分析"):
    path = root / "docs/change_execution_log.md"
    with path.open("a", encoding="utf-8") as stream:
        stream.write(f"\n### {identifier}：{summary}\n\n- 需求：{summary}\n- 状态：进行中\n")


def test_initialization_creates_independent_plan_and_fresh_summary(planned_project):
    root, config = planned_project
    plan = load_plan(root, config)
    assert plan["changes"] == []
    assert all(task["status"] == "pending" for task in plan["tasks"])
    assert validate_progress(root, config)[0].status == "pass"
    summary = (root / config["paths"]["progress"]).read_text()
    assert "0 / 8" in summary
    assert "尚未登记需求" in summary
    assert "H01" not in summary


def test_new_requirement_requires_plan_mapping_before_summary(planned_project):
    root, config = planned_project
    log_change(root)
    assert validate_progress(root, config)[0].status == "fail"
    with pytest.raises(ConfigError, match="must match"):
        write_progress(root, config)
    register_change(root, config, "CHANGE-20261013-01", "年度分析", ["T01", "T02"])
    assert validate_progress(root, config)[0].status == "fail"
    write_progress(root, config)
    assert validate_progress(root, config)[0].status == "pass"


def test_plan_or_log_change_makes_summary_stale(planned_project):
    root, config = planned_project
    path = root / config["paths"]["plan"]
    data = load_yaml(path)
    data["tasks"][0]["status"] = "in_progress"
    write_yaml(path, data)
    assert validate_progress(root, config)[0].status == "fail"
    write_progress(root, config)
    assert validate_progress(root, config)[0].status == "pass"
    (root / "docs/change_execution_log.md").write_text("# 项目记录\n\n业务范围更新\n")
    assert validate_progress(root, config)[0].status == "fail"


def test_requirement_revision_reopens_completed_task_and_downstream(planned_project):
    root, config = planned_project
    log_change(root)
    register_change(root, config, "CHANGE-20261013-01", "年度分析", ["T01", "T02"])
    path = root / config["paths"]["plan"]
    plan = load_yaml(path)
    for task in plan["tasks"][:2]:
        task["status"] = "completed"
        task["evidence"] = "项目范围已确认，输出已经审阅"
    write_yaml(path, plan)
    write_progress(root, config)
    log_path = root / "docs/change_execution_log.md"
    log_path.write_text(log_path.read_text().replace("年度分析", "月度分析"))
    register_change(root, config, "CHANGE-20261013-01", "改为月度分析", ["T01"])
    revised = load_plan(root, config)
    assert revised["tasks"][0]["status"] == "revalidate"
    assert revised["tasks"][1]["status"] == "revalidate"
    assert revised["tasks"][2]["status"] == "pending"
    write_progress(root, config)
    summary = (root / config["paths"]["progress"]).read_text()
    assert "待重新验证" in summary
    assert "改为月度分析" in summary
    assert "已验收任务：0 / 8" in summary


@pytest.mark.parametrize("issue", ["unknown_dependency", "cycle", "completion_without_evidence", "blocked_without_reason", "completion_before_dependency", "unknown_task", "unknown_change"])
def test_invalid_plan_cannot_be_presented_as_progress(planned_project, issue):
    root, config = planned_project
    path = root / config["paths"]["plan"]
    data = load_yaml(path)
    if issue == "unknown_dependency":
        data["tasks"][0]["dependencies"] = ["bad"]
    elif issue == "cycle":
        data["tasks"][0]["dependencies"] = ["T02"]
    elif issue == "completion_without_evidence":
        data["tasks"][0]["status"] = "completed"
    elif issue == "blocked_without_reason":
        data["tasks"][0]["status"] = "blocked"
    elif issue == "completion_before_dependency":
        data["tasks"][1]["status"] = "completed"
        data["tasks"][1]["evidence"] = "已审阅"
    elif issue == "unknown_task":
        log_change(root)
        data["changes"] = [{"id": "CHANGE-20261013-01", "summary": "分析", "task_ids": ["bad"]}]
    else:
        data["changes"] = [{"id": "CHANGE-20261013-01", "summary": "分析", "task_ids": ["T01"]}]
    write_yaml(path, data)
    assert validate_progress(root, config)[0].status == "fail"


def test_run_transition_refreshes_summary_without_completing_tasks(planned_project):
    root, config = planned_project
    update_status(root, current_stage="validated", last_run_id="test-run", last_run_status="passed", completed_stage="validated")
    assert validate_progress(root, config)[0].status == "pass"
    assert all(task["status"] == "pending" for task in load_plan(root, config)["tasks"])
    summary = (root / config["paths"]["progress"]).read_text()
    assert "test-run" in summary
    assert "已验收任务：0 / 8" in summary


def test_example_change_records_are_not_actual_requirements(planned_project):
    root, _ = planned_project
    path = root / "docs/change_execution_log.md"
    path.write_text("# 项目记录\n```markdown\n### CHANGE-20261013-01：示例\n```\n~~~markdown\n### CHANGE-20261013-02：示例\n~~~\n")
    assert change_ids(root) == []


def test_registration_rejects_unknown_tasks_without_mutating_plan(planned_project):
    root, config = planned_project
    log_change(root)
    path = root / config["paths"]["plan"]
    before = path.read_bytes()
    with pytest.raises(ConfigError):
        register_change(root, config, "CHANGE-20261013-01", "年度分析", ["bad"])
    assert path.read_bytes() == before


def test_existing_scope_change_cannot_be_hidden_by_regenerating_summary(planned_project):
    root, config = planned_project
    log_change(root)
    register_change(root, config, "CHANGE-20261013-01", "年度分析", ["T01"])
    write_progress(root, config)
    path = root / "docs/change_execution_log.md"
    path.write_text(path.read_text().replace("年度分析", "月度分析"))
    with pytest.raises(ConfigError, match="scope changed"):
        write_progress(root, config)
    register_change(root, config, "CHANGE-20261013-01", "月度分析", ["T01"])
    write_progress(root, config)
    assert validate_progress(root, config)[0].status == "pass"
