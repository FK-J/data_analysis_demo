"""Project-owned task plans and deterministic, change-linked progress summaries."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .config import ConfigError, load_yaml, resolve_project_path, validate_against_schema
from .status import load_status
from .validation import CheckResult, check


PLAN_PATH = "docs/project_plan.yaml"
PROGRESS_PATH = "docs/progress_summary.md"
CHANGE_LOG = "docs/change_execution_log.md"
LABELS = {
    "pending": "待开始", "in_progress": "进行中", "blocked": "阻塞",
    "completed": "已验收", "cancelled": "已取消", "revalidate": "待重新验证",
}


def change_ids(root: Path) -> list[str]:
    """Only actual headings count; ignore example records in fenced blocks."""
    path = root / CHANGE_LOG
    if not path.is_file():
        raise ConfigError("Requirement/change log is missing.")
    in_fence = False
    fence = ""
    identifiers = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if not in_fence:
                in_fence, fence = True, marker
            elif marker == fence:
                in_fence = False
            continue
        if not in_fence:
            match = re.match(r"^###\s+(CHANGE-\d{8}-\d+)\b", line)
            if match:
                identifiers.append(match.group(1))
    if len(set(identifiers)) != len(identifiers):
        raise ConfigError("Duplicate change IDs in requirement/change log.")
    return identifiers


def request_fingerprint(root: Path, identifier: str) -> str:
    """Scope fields must be re-registered; execution status alone does not reopen scope."""
    text = (root / CHANGE_LOG).read_text(encoding="utf-8")
    text = re.sub(r"(?ms)^\s*(```|~~~).*?^\s*\1[^\n]*$", "", text)
    headings = list(re.finditer(r"(?m)^###\s+(CHANGE-\d{8}-\d+)\b[^\n]*", text))
    for index, match in enumerate(headings):
        if match.group(1) != identifier:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[match.end():end]
        scope = [match.group(0)]
        scope.extend(line for line in section.splitlines() if re.match(
            r"^- (需求|变更等级|验收标准|影响范围|最早重跑位置|最早执行位置|必须执行到)[：:]", line))
        return hashlib.sha256("\n".join(scope).encode("utf-8")).hexdigest()
    raise ConfigError(f"Requirement is not registered: {identifier}")


def load_plan(root: Path, config: dict[str, Any], *, candidate: dict[str, Any] | None = None) -> dict[str, Any]:
    relative = config["paths"].get("plan", PLAN_PATH)
    data = candidate if candidate is not None else load_yaml(resolve_project_path(root, relative))
    validate_against_schema(data, root / "schemas/plan.schema.yaml", label="development plan")
    tasks = {task["id"]: task for task in data["tasks"]}
    if len(tasks) != len(data["tasks"]):
        raise ConfigError("Duplicate task IDs in development plan.")
    changes = [entry["id"] for entry in data["changes"]]
    if len(set(changes)) != len(changes):
        raise ConfigError("Duplicate change IDs in development plan.")
    logged = set(change_ids(root))
    if set(changes) != logged:
        raise ConfigError(f"Change log and plan must match: missing={sorted(logged - set(changes))}, unknown={sorted(set(changes) - logged)}.")
    for entry in data["changes"]:
        if not set(entry["task_ids"]).issubset(tasks):
            raise ConfigError(f"{entry['id']} references unknown tasks.")
        if entry["request_fingerprint"] != request_fingerprint(root, entry["id"]):
            raise ConfigError(f"{entry['id']} scope changed; re-register affected tasks with --change-id, --summary and --tasks.")
    for task in tasks.values():
        if not set(task["dependencies"]).issubset(tasks) or task["id"] in task["dependencies"]:
            raise ConfigError(f"{task['id']} has invalid dependencies.")
        for relative in task["outputs"]:
            resolve_project_path(root, relative)
        if task["status"] == "completed":
            if not task["evidence"].strip():
                raise ConfigError(f"{task['id']} requires acceptance evidence before completion.")
            if any(tasks[key]["status"] not in {"completed", "cancelled"} for key in task["dependencies"]):
                raise ConfigError(f"{task['id']} cannot complete before its dependencies.")
            if any(not resolve_project_path(root, relative).is_file() for relative in task["outputs"]):
                raise ConfigError(f"{task['id']} is completed but a declared output is missing.")
        if task["status"] in {"blocked", "cancelled"} and not task["blocker"].strip():
            raise ConfigError(f"{task['id']} requires a blocker/cancellation reason.")
        if task["status"] not in {"completed", "cancelled"} and not task["next_action"].strip():
            raise ConfigError(f"{task['id']} requires a next action.")
    visiting, visited = set(), set()

    def visit(identifier: str) -> None:
        if identifier in visiting:
            raise ConfigError("Development plan contains a dependency cycle.")
        if identifier in visited:
            return
        visiting.add(identifier)
        for dependency in tasks[identifier]["dependencies"]:
            visit(dependency)
        visiting.remove(identifier)
        visited.add(identifier)

    for identifier in tasks:
        visit(identifier)
    return data


def register_change(root: Path, config: dict[str, Any], identifier: str, summary: str, task_ids: list[str]) -> None:
    """Link new/revised scope to tasks, invalidating accepted downstream work."""
    from .config import write_yaml
    path = resolve_project_path(root, config["paths"].get("plan", PLAN_PATH))
    plan = load_yaml(path)
    validate_against_schema(plan, root / "schemas/plan.schema.yaml", label="development plan")
    tasks = {task["id"]: task for task in plan["tasks"]}
    if identifier not in change_ids(root):
        raise ConfigError("Register the requirement in the change log before updating the plan.")
    if not summary.strip() or not task_ids or len(set(task_ids)) != len(task_ids) or not set(task_ids).issubset(tasks):
        raise ConfigError("Change needs a summary and a unique list of existing task IDs.")
    entry = {"id": identifier, "summary": summary, "task_ids": task_ids,
             "request_fingerprint": request_fingerprint(root, identifier)}
    plan["changes"] = [entry if item["id"] == identifier else item for item in plan["changes"]]
    if not any(item["id"] == identifier for item in plan["changes"]):
        plan["changes"].append(entry)
    affected = set(task_ids)
    while True:
        expanded = affected | {task["id"] for task in tasks.values() if affected.intersection(task["dependencies"])}
        if expanded == affected:
            break
        affected = expanded
    for key in affected:
        task = tasks[key]
        if task["status"] in {"completed", "cancelled"}:
            task["status"] = "revalidate"
            task["blocker"] = ""
            task["next_action"] = f"按 {identifier} 重新确认范围并验收；历史依据：{task['evidence'] or '原任务已取消'}"
    load_plan(root, config, candidate=plan)
    write_yaml(path, plan)


def render_progress(root: Path, config: dict[str, Any], plan: dict[str, Any]) -> str:
    """Stable rendering makes every plan/log/status change invalidate the summary."""
    status = load_status(root)
    plan_path = resolve_project_path(root, config["paths"].get("plan", PLAN_PATH))
    digest = hashlib.sha256(plan_path.read_bytes() + b"\0" + (root / CHANGE_LOG).read_bytes()).hexdigest()
    operational = {key: status.get(key) for key in ("current_stage", "last_run_id", "last_run_status", "remaining_risks")}
    tasks = plan["tasks"]
    active = [task for task in tasks if task["status"] != "cancelled"]
    completed = sum(task["status"] == "completed" for task in active)
    lines = ["# 项目开发进度摘要", "", "由框架生成；任务状态来自项目计划，验收依据由开发者维护。", "",
             f"- 已验收任务：{completed} / {len(active)}；已取消：{len(tasks) - len(active)}。",
             f"- 最近运行：{status.get('last_run_status') or '尚未运行'}；运行 ID：{status.get('last_run_id') or '无'}。",
             f"- 最近记录的工程阶段：{status.get('current_stage', 'discovery')}（不等同于任务完成）。",
             f"- 计划及需求记录指纹：`{digest}`。", "",
             "## 需求与变更", ""]
    for entry in plan["changes"]:
        lines.append(f"- {entry['id']}：{entry['summary']}；关联任务：{', '.join(entry['task_ids'])}。")
    if not plan["changes"]:
        lines.append("- 尚未登记需求；首次开始业务分析前登记需求并调整计划。")
    stages = load_yaml(root / ".harness/workflow.yaml")["stages"]
    lines += ["", "## 阶段进度", "", "| 阶段 | 已验收 / 有效任务 | 状态 |", "| --- | --- | --- |"]
    for stage in stages:
        subset = [task for task in active if task["stage"] == stage["id"]]
        done = sum(task["status"] == "completed" for task in subset)
        state = "未安排" if not subset else "已验收" if done == len(subset) else "阻塞" if any(task["status"] == "blocked" for task in subset) else "待重新验证" if any(task["status"] == "revalidate" for task in subset) else "进行中" if any(task["status"] == "in_progress" for task in subset) else "待开始"
        lines.append(f"| {stage['label']} | {done} / {len(subset)} | {state} |")

    def cell(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines += ["", "## 任务明细", "", "| 任务 | 负责人 | 状态 | 依赖 | 产物 | 验收依据 | 下一步 / 阻塞 |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for task in tasks:
        row = [f"{task['id']} {task['title']}", task["owner"], LABELS[task["status"]], ", ".join(task["dependencies"]) or "无", ", ".join(task["outputs"]) or "见验收依据", task["evidence"] or task["acceptance"], task["blocker"] or task["next_action"] or "无"]
        lines.append("| " + " | ".join(cell(value) for value in row) + " |")
    lines += ["", "## 阻塞与下一步", ""]
    lookup = {task["id"]: task for task in tasks}
    open_tasks = [task for task in active if task["status"] != "completed"]
    for task in open_tasks:
        waiting = [key for key in task["dependencies"] if lookup[key]["status"] not in {"completed", "cancelled"}]
        suffix = f"；等待：{', '.join(waiting)}" if waiting else ""
        lines.append(f"- {task['id']}：{task['blocker'] or task['next_action']}{suffix}。")
    if not open_tasks:
        lines.append("- 当前计划任务均已验收；正式交付仍需通过框架审计。")
    lines += [f"- 剩余风险：{risk}" for risk in status.get("remaining_risks", [])]
    lines += ["", f"<!-- operational-status: {json.dumps(operational, ensure_ascii=False, sort_keys=True)} -->", ""]
    return "\n".join(lines)


def write_progress(root: Path, config: dict[str, Any]) -> Path:
    plan = load_plan(root, config)
    path = resolve_project_path(root, config["paths"].get("progress", PROGRESS_PATH))
    if path == resolve_project_path(root, config["paths"].get("plan", PLAN_PATH)) or path == root / CHANGE_LOG:
        raise ConfigError("Progress output must not overwrite the plan or change log.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_progress(root, config, plan), encoding="utf-8")
    return path


def validate_progress(root: Path, config: dict[str, Any]) -> list[CheckResult]:
    try:
        plan = load_plan(root, config)
        path = resolve_project_path(root, config["paths"].get("progress", PROGRESS_PATH))
        fresh = path.is_file() and path.read_text(encoding="utf-8") == render_progress(root, config, plan)
        return [check("development_progress", "pass" if fresh else "fail", "Plan, requirements and progress summary agree." if fresh else "Progress summary is missing or stale; update the plan and run scripts/update_progress.py.", str(path.relative_to(root)))]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [check("development_progress", "fail", str(exc))]
