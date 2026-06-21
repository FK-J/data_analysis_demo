"""Generate a result-only final analysis report from structured inputs.

Default behavior is intentionally conservative:
- render provided results, figures, tables, and notes;
- do not generate business insights automatically;
- do not call any large language model.

Use --with-insights only when the user explicitly asks to include pre-written
insight text from the input YAML.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise ImportError("Missing dependency PyYAML. Install it with: pip install PyYAML") from exc


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "reports" / "final" / "report_inputs.yaml"
DEFAULT_OUTPUT = PROJECT_ROOT / "reports" / "final" / "final_analysis_report.md"


def resolve_path(path: str | Path) -> Path:
    """Resolve a path relative to the project root."""
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    return resolved


def load_report_inputs(input_path: Path) -> dict[str, Any]:
    """Load report inputs from YAML."""
    if not input_path.exists():
        raise FileNotFoundError(
            f"Report input file not found: {input_path}. "
            "Copy docs/report_inputs_template.yaml to reports/final/report_inputs.yaml "
            "and fill in the exported results first."
        )

    with input_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError("Report input YAML must contain a top-level mapping.")

    return data


def as_list(value: Any) -> list[Any]:
    """Normalize a value to a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def render_bullets(items: Any, *, empty_text: str = "待填写") -> list[str]:
    """Render a list of bullet lines."""
    values = [str(item) for item in as_list(items) if str(item).strip()]
    if not values:
        return [f"- {empty_text}"]
    return [f"- {item}" for item in values]


def render_metrics(metrics: Any) -> list[str]:
    """Render metric dictionaries as a Markdown table."""
    rows = [item for item in as_list(metrics) if isinstance(item, dict)]
    if not rows:
        return ["| 指标 | 结果 | 说明 |", "| --- | --- | --- |", "| 待填写 | 待填写 | 待填写 |"]

    lines = ["| 指标 | 结果 | 说明 |", "| --- | --- | --- |"]
    for item in rows:
        name = item.get("name", "")
        value = item.get("value", "")
        note = item.get("note", "")
        lines.append(f"| {name} | {value} | {note} |")
    return lines


def render_assets(items: Any, *, label: str) -> list[str]:
    """Render figure or table references."""
    rows = [item for item in as_list(items) if isinstance(item, dict)]
    if not rows:
        return [f"- 暂无{label}"]

    lines: list[str] = []
    for item in rows:
        title = item.get("title", "未命名")
        path = item.get("path", "")
        note = item.get("note", "")
        suffix = f"：{note}" if note else ""
        if path:
            lines.append(f"- {title}：`{path}`{suffix}")
        else:
            lines.append(f"- {title}{suffix}")
    return lines


def append_section(lines: list[str], title: str, content: list[str]) -> None:
    """Append a Markdown section with a blank line."""
    lines.append(title)
    lines.append("")
    lines.extend(content)
    lines.append("")


def render_report(data: dict[str, Any], *, with_insights: bool) -> str:
    """Render final report Markdown."""
    project = data.get("project", {}) if isinstance(data.get("project"), dict) else {}
    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    appendix = data.get("appendix", {}) if isinstance(data.get("appendix"), dict) else {}
    questions = [item for item in as_list(data.get("business_questions")) if isinstance(item, dict)]

    title = project.get("report_title") or project.get("name") or "数据分析报告"
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines: list[str] = [
        f"# {title}",
        "",
        f"- 生成时间：{generated_at}",
        f"- 分析框架：`{project.get('analysis_framework_path', 'docs/analysis_framework.md')}`",
        f"- 报告结构：`{project.get('report_structure_path', 'reports/final/final_report_structure.md')}`",
        f"- 主 Notebook：`{project.get('notebook_path', 'notebooks/main_analysis.ipynb')}`",
        "",
        "本报告由 `scripts/generate_final_report.py` 根据结构化输入生成。默认只呈现结果，不自动生成洞察或业务解读。",
        "",
    ]

    lines.extend(["## 1. 汇总结果", ""])
    append_section(lines, "### 本节目标", [str(summary.get("section_goal", "汇总本次分析最重要的结果。"))])
    append_section(lines, "### 关键结果", render_bullets(summary.get("key_results")))
    append_section(lines, "### 核心指标", render_metrics(summary.get("metrics")))
    append_section(lines, "### 图表", render_assets(summary.get("figures"), label="图表"))
    append_section(lines, "### 结果表", render_assets(summary.get("tables"), label="结果表"))

    for index, question in enumerate(questions, start=2):
        question_id = question.get("id", f"Q{index - 1}")
        question_title = question.get("title", "待填写业务问题")
        lines.extend([f"## {index}. {question_id}：{question_title}", ""])
        append_section(lines, "### 本节目标", [str(question.get("section_goal", "待填写"))])
        append_section(lines, "### 具体分析逻辑", [str(question.get("analysis_logic", "待填写"))])
        append_section(lines, "### 关键结果", render_bullets(question.get("key_results")))
        append_section(lines, "### 图表", render_assets(question.get("figures"), label="图表"))
        append_section(lines, "### 结果表", render_assets(question.get("tables"), label="结果表"))
        append_section(lines, "### 口径与限制", render_bullets(question.get("notes")))

    if with_insights:
        insights = data.get("insights", {}) if isinstance(data.get("insights"), dict) else {}
        lines.extend(["## 可选洞察", ""])
        lines.append("以下内容仅在用户明确要求并传入 `--with-insights` 时渲染；本脚本不会自动调用大模型生成洞察。")
        lines.append("")
        lines.extend(render_bullets(insights.get("items"), empty_text="未提供洞察内容"))
        lines.append("")

    lines.extend(["## 附录", ""])
    append_section(lines, "### 数据范围", render_bullets(appendix.get("data_scope")))
    append_section(lines, "### 指标口径", render_bullets(appendix.get("metric_definitions")))
    append_section(lines, "### 输出文件", render_bullets(appendix.get("output_files")))

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a result-only final analysis report.")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help="Path to report input YAML. Defaults to reports/final/report_inputs.yaml.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Path to output Markdown report. Defaults to reports/final/final_analysis_report.md.",
    )
    parser.add_argument(
        "--with-insights",
        action="store_true",
        help="Render pre-written insights from input YAML. This does not call a large language model.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = resolve_path(args.input)
    output_path = resolve_path(args.output)

    data = load_report_inputs(input_path)
    report = render_report(data, with_insights=bool(args.with_insights))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Generated final report: {output_path}")


if __name__ == "__main__":
    main()
