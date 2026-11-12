"""Render the conclusion summary and the detailed analysis report.

The summary Markdown intentionally contains only report metadata, core
conclusions, key metrics, key figures and an index into the detailed HTML.
All per-question analysis logic, evidence, tables and limitations belong to
the detailed HTML so readers can move from conclusions to process without the
summary repeating the full analysis.
"""

from __future__ import annotations

import html
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

DEFAULT_SUMMARY_NAME = "final_analysis_report.md"
DEFAULT_DETAIL_NAME = "analysis_detail.html"

_COVERAGE_LABELS = {
    "covered": "已覆盖",
    "not_applicable": "不适用",
    "missing": "缺失",
}


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _items(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _escape(value: Any) -> str:
    return html.escape(_text(value), quote=True)


def _md_text(value: Any) -> str:
    """Escape inline HTML so report input cannot inject markup into Markdown."""
    return html.escape(_text(value), quote=False)


def _md_cell(value: Any) -> str:
    return _md_text(value).replace("|", "\\|").replace("\n", " ")


def _generated_at(project: dict[str, Any]) -> str:
    return _text(project.get("generated_at")) or datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _slug(value: Any) -> str:
    slug = re.sub(r"[^0-9A-Za-z_-]+", "-", _text(value)).strip("-").lower()
    return slug or "section"


def _relative_link(
    target: str | Path | None,
    output_path: str | Path | None,
    default: str,
    *,
    project_root: str | Path | None = None,
) -> str:
    """Link a project-relative target from the directory of ``output_path``."""
    if target is None:
        return default
    path = Path(target)
    if not path.is_absolute():
        base = Path(project_root).resolve() if project_root is not None else Path.cwd()
        path = base / path
    try:
        relative = os.path.relpath(path.resolve(), Path(output_path).resolve().parent)
    except (OSError, ValueError, TypeError):
        return default
    return quote(Path(relative).as_posix(), safe="/#")


def _asset_href(path_value: Any, *, project_root: Path, output_dir: Path) -> str:
    raw = _text(path_value).strip()
    if not raw:
        return ""
    source = Path(raw)
    if not source.is_absolute():
        source = (project_root / source).resolve()
    try:
        relative = os.path.relpath(source, output_dir)
    except (OSError, ValueError):
        relative = str(source)
    return quote(Path(relative).as_posix(), safe="/:@!$&'()*+,;=-._~")


def _format_metric(metric: dict[str, Any]) -> str:
    value = metric.get("value", "")
    if value in {"", None}:
        return ""
    if metric.get("format") == "percent":
        try:
            return f"{float(value):.2%}"
        except (TypeError, ValueError):
            return _text(value)
    return _text(value)


# ---------------------------------------------------------------------------
# Markdown summary
# ---------------------------------------------------------------------------


def _markdown_bullets(values: Any, *, empty: str = "暂无内容") -> list[str]:
    text_values = [_text(item).strip() for item in _items(values) if _text(item).strip()]
    if not text_values:
        return [f"- {empty}"]
    return [f"- {_md_text(item)}" for item in text_values]


def _markdown_metrics(metrics: Any) -> list[str]:
    rows = [item for item in _items(metrics) if isinstance(item, dict)]
    if not rows:
        return ["| 指标 | 结果 | 说明 |", "| --- | --- | --- |", "| 暂无关键指标 |  |  |"]
    lines = ["| 指标 | 结果 | 说明 |", "| --- | --- | --- |"]
    for item in rows:
        name = _md_cell(item.get("name"))
        value = _md_cell(_format_metric(item))
        note = _md_cell(item.get("note"))
        lines.append(f"| {name} | {value} | {note} |")
    return lines


def _markdown_figures(
    figures: Any,
    *,
    project_root: Path,
    output_path: Path,
) -> list[str]:
    rows = [item for item in _items(figures) if isinstance(item, dict)]
    if not rows:
        return ["- 暂无关键图表"]
    lines: list[str] = []
    for item in rows:
        title = _text(item.get("title")) or "未命名图表"
        note = _text(item.get("note"))
        path = _text(item.get("path"))
        safe_title = _md_text(title).replace("[", "\\[").replace("]", "\\]")
        if path:
            href = _asset_href(path, project_root=project_root, output_dir=output_path.parent)
            lines.append(f"![{safe_title}]({href})")
            lines.append("")
            lines.append(f"*{_md_text(title)}{('：' + _md_text(note)) if note else ''}*")
            lines.append("")
        else:
            lines.append(f"- {_md_text(title)}{('：' + _md_text(note)) if note else ''}")
    return lines


def render_summary_markdown(
    data: dict[str, Any],
    *,
    project_root: str | Path | None = None,
    output_path: str | Path | None = None,
    detail_path: str | Path | None = None,
) -> str:
    """Render the conclusion-only Markdown report."""
    root = Path(project_root).resolve() if project_root is not None else Path.cwd().resolve()
    destination = (
        Path(output_path).resolve()
        if output_path is not None
        else root / "reports" / "final" / DEFAULT_SUMMARY_NAME
    )
    project = _mapping(data.get("project"))
    summary = _mapping(data.get("summary"))
    questions = [item for item in _items(data.get("business_questions")) if isinstance(item, dict)]
    detail = _mapping(data.get("detail"))
    detail_sections = [item for item in _items(detail.get("sections")) if isinstance(item, dict)]

    title = _text(project.get("report_title")) or _text(project.get("name")) or "数据分析报告"
    detail_href = _relative_link(detail_path, destination, DEFAULT_DETAIL_NAME, project_root=root)

    lines: list[str] = [f"# {_md_text(title)}", "", f"- 生成时间：{_generated_at(project)}"]
    if project.get("run_id"):
        lines.append(f"- 运行 ID：`{_text(project['run_id'])}`")
    lines.extend(
        [
            f"- 分析框架：`{_text(project.get('analysis_framework_path')) or 'docs/analysis_framework.md'}`",
            f"- 报告结构：`{_text(project.get('report_structure_path')) or 'reports/final/final_report_structure.md'}`",
            f"- 主 Notebook：`{_text(project.get('notebook_path')) or 'notebooks/main_analysis.ipynb'}`",
            f"- 完整分析过程：`{detail_href}`",
            "",
            "## 1. 核心结论",
            "",
        ]
    )
    lines.extend(_markdown_bullets(summary.get("conclusions") or summary.get("key_results"), empty="暂无核心结论"))
    lines.extend(["", "## 2. 关键指标", ""])
    lines.extend(_markdown_metrics(summary.get("metrics")))
    lines.extend(["", "## 3. 关键图表", ""])
    lines.extend(_markdown_figures(summary.get("figures"), project_root=root, output_path=destination))
    lines.extend(["", "## 4. 交付物索引", ""])
    lines.append(f"- [完整分析过程（HTML）]({detail_href})")
    for question in questions:
        identifier = _text(question.get("id")) or "Q"
        question_title = _md_text(_text(question.get("title")) or "未命名业务问题").replace("[", "\\[").replace("]", "\\]")
        lines.append(f"- [{identifier}：{question_title}]({detail_href}#q-{_slug(identifier)})")
    for section in detail_sections:
        section_id = _text(section.get("id")) or "D"
        section_title = _md_text(_text(section.get("title")) or "未命名分析章节").replace("[", "\\[").replace("]", "\\]")
        lines.append(f"- [{section_title}]({detail_href}#detail-{_slug(section_id)})")
    lines.append(f"- [附录：口径、限制与复现信息]({detail_href}#appendix)")
    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# HTML detail report
# ---------------------------------------------------------------------------

_CSS = """
:root {
  color-scheme: light dark;
  --bg: #f6f7f9;
  --panel: #ffffff;
  --ink: #1f2933;
  --muted: #64748b;
  --line: #d8dee8;
  --accent: #1f6feb;
  --accent-soft: #e8f0fe;
  --code: #f1f3f7;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font: 16px/1.7 -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
        "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.layout { display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 32px; max-width: 1240px; margin: 0 auto; padding: 32px 24px 64px; }
nav.toc { position: sticky; top: 24px; align-self: start; background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 18px 20px; max-height: calc(100vh - 48px); overflow: auto; }
nav.toc h2 { font-size: 15px; margin: 0 0 12px; color: var(--muted); letter-spacing: .04em; }
nav.toc ol { list-style: none; margin: 0; padding: 0; }
nav.toc li { margin: 4px 0; font-size: 14px; }
nav.toc ol ol { padding-left: 14px; }
main { min-width: 0; }
.hero { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 28px 32px; margin-bottom: 24px; }
.eyebrow { margin: 0 0 8px; color: var(--accent); font-size: 13px; letter-spacing: .12em; text-transform: uppercase; }
.hero h1 { margin: 0 0 8px; font-size: 30px; line-height: 1.3; }
.subtitle { margin: 0 0 20px; color: var(--muted); }
.meta { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 10px 24px; margin: 0 0 20px; }
.meta div { min-width: 0; }
.meta dt { color: var(--muted); font-size: 12px; }
.meta dd { margin: 0; font-size: 14px; overflow-wrap: anywhere; }
.button { display: inline-block; background: var(--accent); color: #fff; padding: 8px 16px; border-radius: 999px; font-size: 14px; }
.button:hover { text-decoration: none; filter: brightness(.95); }
section { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 26px 32px; margin-bottom: 20px; }
section h2 { margin: 0 0 16px; font-size: 23px; border-bottom: 1px solid var(--line); padding-bottom: 10px; }
section h3 { margin: 24px 0 10px; font-size: 18px; }
section h4 { margin: 18px 0 6px; font-size: 16px; }
p { margin: 8px 0; }
ul, ol { margin: 8px 0; padding-left: 22px; }
li { margin: 4px 0; }
table { border-collapse: collapse; width: 100%; margin: 10px 0 18px; font-size: 14px; }
th, td { border: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }
th { background: var(--accent-soft); }
code { background: var(--code); border-radius: 5px; padding: 1px 5px; font-size: 13px; }
figure { margin: 18px 0; }
figure img { max-width: 100%; height: auto; border: 1px solid var(--line); border-radius: 10px; background: #fff; }
figcaption { color: var(--muted); font-size: 13px; margin-top: 6px; }
.step { border-left: 3px solid var(--accent); background: #fafbfe; padding: 4px 16px 10px; margin: 14px 0; border-radius: 0 10px 10px 0; }
.label { color: var(--muted); font-weight: 600; }
.muted { color: var(--muted); }
footer { max-width: 1240px; margin: 0 auto; padding: 0 24px 40px; color: var(--muted); font-size: 13px; }
@media (max-width: 980px) {
  .layout { grid-template-columns: 1fr; }
  nav.toc { position: static; max-height: none; }
}
@media print {
  body { background: #fff; }
  .layout { display: block; max-width: none; padding: 0; }
  nav.toc { display: none; }
  section, .hero { border: none; padding: 0; margin: 0 0 24px; }
  .button { display: none; }
}
"""


def _html_bullets(values: Any, *, empty: str = "本节未提供") -> str:
    text_values = [_text(item).strip() for item in _items(values) if _text(item).strip()]
    if not text_values:
        return f'<p class="muted">{_escape(empty)}</p>'
    return "<ul>" + "".join(f"<li>{_escape(item)}</li>" for item in text_values) + "</ul>"


def _html_metric_table(metrics: Any) -> str:
    rows = [item for item in _items(metrics) if isinstance(item, dict)]
    if not rows:
        return '<p class="muted">本节未提供指标。</p>'
    lines = ["<table>", "<thead><tr><th>指标</th><th>结果</th><th>说明</th></tr></thead><tbody>"]
    for item in rows:
        lines.append(
            "<tr>"
            f"<td>{_escape(item.get('name'))}</td>"
            f"<td>{_escape(_format_metric(item))}</td>"
            f"<td>{_escape(item.get('note'))}</td>"
            "</tr>"
        )
    lines.append("</tbody></table>")
    return "\n".join(lines)


def _html_figures(figures: Any, *, project_root: Path, output_dir: Path) -> str:
    rows = [item for item in _items(figures) if isinstance(item, dict)]
    if not rows:
        return '<p class="muted">本节未提供图表。</p>'
    parts: list[str] = []
    for item in rows:
        title = _text(item.get("title")) or "未命名图表"
        note = _text(item.get("note"))
        href = _asset_href(item.get("path"), project_root=project_root, output_dir=output_dir)
        caption = _escape(title) + (f"：{_escape(note)}" if note else "")
        if href:
            parts.append(
                f'<figure><img src="{href}" alt="{_escape(title)}" loading="lazy">'
                f"<figcaption>{caption}</figcaption></figure>"
            )
        else:
            parts.append(f"<p><strong>{_escape(title)}</strong>{('：' + _escape(note)) if note else ''}</p>")
    return "\n".join(parts)


def _html_tables(tables: Any, *, project_root: Path, output_dir: Path) -> str:
    rows = [item for item in _items(tables) if isinstance(item, dict)]
    if not rows:
        return '<p class="muted">本节未提供结果表。</p>'
    parts = ["<ul>"]
    for item in rows:
        title = _text(item.get("title")) or "未命名结果表"
        note = _text(item.get("note"))
        href = _asset_href(item.get("path"), project_root=project_root, output_dir=output_dir)
        label = _escape(title)
        if href:
            label = f'<a href="{href}">{label}</a>'
        parts.append(f"<li>{label}{('：' + _escape(note)) if note else ''}</li>")
    parts.append("</ul>")
    return "\n".join(parts)


def _html_steps(steps: Any, *, project_root: Path, output_dir: Path) -> str:
    rows = [item for item in _items(steps) if isinstance(item, dict)]
    if not rows:
        return '<p class="muted">本节未提供分步过程。</p>'
    parts: list[str] = []
    for step in rows:
        title = _text(step.get("title")) or "分析步骤"
        parts.append(f'<div class="step"><h4>{_escape(title)}</h4>')
        method = _text(step.get("method"))
        if method:
            parts.append(f'<p><span class="label">方法：</span>{_escape(method)}</p>')
        evidence = [_text(item).strip() for item in _items(step.get("evidence")) if _text(item).strip()]
        if evidence:
            parts.append('<p><span class="label">证据：</span></p>')
            parts.append("<ul>" + "".join(f"<li><code>{_escape(item)}</code></li>" for item in evidence) + "</ul>")
        finding = _text(step.get("finding"))
        if finding:
            parts.append(f'<p><span class="label">结论：</span>{_escape(finding)}</p>')
        if step.get("figures"):
            parts.append(_html_figures(step.get("figures"), project_root=project_root, output_dir=output_dir))
        if step.get("tables"):
            parts.append(_html_tables(step.get("tables"), project_root=project_root, output_dir=output_dir))
        parts.append("</div>")
    return "\n".join(parts)


def _html_conclusions(values: Any, *, fallback: Any = None, empty: str = "本节未提供结论") -> str:
    chosen = values if [_text(item).strip() for item in _items(values) if _text(item).strip()] else fallback
    return _html_bullets(chosen, empty=empty)


def _question_section(
    question: dict[str, Any],
    *,
    number: int,
    project_root: Path,
    output_dir: Path,
) -> tuple[str, str]:
    identifier = _text(question.get("id")) or f"Q{number}"
    title = _text(question.get("title")) or "未命名业务问题"
    anchor = f"q-{_slug(identifier)}"
    parts = [f'<section id="{anchor}">', f"<h2>2.{number} {_escape(identifier)}：{_escape(title)}</h2>"]
    parts.append("<h3>本节目标</h3>")
    parts.append(f"<p>{_escape(question.get('section_goal') or '本节未提供目标。')}</p>")
    parts.append("<h3>本节结论</h3>")
    parts.append(_html_conclusions(question.get("conclusions"), fallback=question.get("key_results")))
    parts.append("<h3>分析逻辑</h3>")
    parts.append(f"<p>{_escape(question.get('analysis_logic') or '本节未提供分析逻辑。')}</p>")
    parts.append("<h3>分析过程</h3>")
    parts.append(_html_steps(question.get("process_steps"), project_root=project_root, output_dir=output_dir))
    if question.get("metrics"):
        parts.append("<h3>核心指标</h3>")
        parts.append(_html_metric_table(question["metrics"]))
    parts.append("<h3>图表</h3>")
    parts.append(_html_figures(question.get("figures"), project_root=project_root, output_dir=output_dir))
    parts.append("<h3>结果表</h3>")
    parts.append(_html_tables(question.get("tables"), project_root=project_root, output_dir=output_dir))
    parts.append("<h3>口径与限制</h3>")
    parts.append(_html_bullets(question.get("notes"), empty="本节未提供口径或限制说明。"))
    parts.append("</section>")
    toc = f'<li><a href="#{anchor}">{_escape(identifier)}：{_escape(title)}</a></li>'
    return "\n".join(parts), toc


def _detail_section(
    section: dict[str, Any],
    *,
    number: int,
    project_root: Path,
    output_dir: Path,
) -> tuple[str, str]:
    identifier = _text(section.get("id")) or f"D{number}"
    title = _text(section.get("title")) or "未命名分析章节"
    anchor = f"detail-{_slug(identifier)}"
    parts = [f'<section id="{anchor}">', f"<h2>3.{number} {_escape(title)}</h2>"]
    parts.append("<h3>本节结论</h3>")
    parts.append(_html_conclusions(section.get("conclusions"), empty="本节未提供结论。"))
    if section.get("content"):
        parts.append("<h3>分析说明</h3>")
        parts.append(_html_bullets(section.get("content")))
    if section.get("steps"):
        parts.append("<h3>分析过程</h3>")
        parts.append(_html_steps(section["steps"], project_root=project_root, output_dir=output_dir))
    if section.get("figures"):
        parts.append("<h3>图表</h3>")
        parts.append(_html_figures(section.get("figures"), project_root=project_root, output_dir=output_dir))
    if section.get("tables"):
        parts.append("<h3>结果表</h3>")
        parts.append(_html_tables(section.get("tables"), project_root=project_root, output_dir=output_dir))
    if section.get("notes"):
        parts.append("<h3>口径与限制</h3>")
        parts.append(_html_bullets(section.get("notes")))
    parts.append("</section>")
    toc = f'<li><a href="#{anchor}">{_escape(title)}</a></li>'
    return "\n".join(parts), toc


def render_detail_html(
    data: dict[str, Any],
    *,
    project_root: str | Path | None = None,
    output_path: str | Path | None = None,
    summary_path: str | Path | None = None,
    with_insights: bool = False,
) -> str:
    """Render the detailed analysis process as a standalone HTML page."""
    root = Path(project_root).resolve() if project_root is not None else Path.cwd().resolve()
    destination = (
        Path(output_path).resolve()
        if output_path is not None
        else root / "reports" / "final" / DEFAULT_DETAIL_NAME
    )
    output_dir = destination.parent
    project = _mapping(data.get("project"))
    summary = _mapping(data.get("summary"))
    questions = [item for item in _items(data.get("business_questions")) if isinstance(item, dict)]
    appendix = _mapping(data.get("appendix"))
    detail = _mapping(data.get("detail"))
    detail_sections = [item for item in _items(detail.get("sections")) if isinstance(item, dict)]
    coverage = [item for item in _items(data.get("coverage")) if isinstance(item, dict)]

    title = _text(project.get("report_title")) or _text(project.get("name")) or "数据分析报告"
    run_id = _text(project.get("run_id"))
    generated_at = _generated_at(project)
    summary_href = _relative_link(summary_path, destination, DEFAULT_SUMMARY_NAME, project_root=root)

    toc = ['<li><a href="#overview">分析概览</a></li>']
    if questions:
        toc.append('<li><a href="#questions">业务问题分析</a><ol>')
        question_toc = []
        question_sections = []
        for index, question in enumerate(questions, start=1):
            section_html, section_toc = _question_section(
                question, number=index, project_root=root, output_dir=output_dir
            )
            question_sections.append(section_html)
            question_toc.append(section_toc)
        toc.extend(question_toc)
        toc.append("</ol></li>")
    else:
        question_sections = []
    if detail_sections:
        toc.append('<li><a href="#detail">详细分析过程</a><ol>')
        detail_toc = []
        detail_html = []
        for index, section in enumerate(detail_sections, start=1):
            section_html, section_toc = _detail_section(
                section, number=index, project_root=root, output_dir=output_dir
            )
            detail_html.append(section_html)
            detail_toc.append(section_toc)
        toc.extend(detail_toc)
        toc.append("</ol></li>")
    else:
        detail_html = []
    toc.append('<li><a href="#appendix">附录与复现信息</a></li>')

    meta_lines = [
        f"<div><dt>生成时间</dt><dd>{_escape(generated_at)}</dd></div>",
    ]
    if run_id:
        meta_lines.append(f"<div><dt>运行 ID</dt><dd><code>{_escape(run_id)}</code></dd></div>")
    meta_lines.extend(
        [
            f"<div><dt>分析框架</dt><dd><code>{_escape(project.get('analysis_framework_path') or 'docs/analysis_framework.md')}</code></dd></div>",
            f"<div><dt>报告结构</dt><dd><code>{_escape(project.get('report_structure_path') or 'reports/final/final_report_structure.md')}</code></dd></div>",
            f"<div><dt>主 Notebook</dt><dd><code>{_escape(project.get('notebook_path') or 'notebooks/main_analysis.ipynb')}</code></dd></div>",
        ]
    )

    overview = [
        '<section id="overview">',
        "<h2>1. 分析概览</h2>",
        "<h3>核心结论</h3>",
        _html_conclusions(summary.get("conclusions"), fallback=summary.get("key_results"), empty="暂无核心结论"),
        "<h3>关键指标</h3>",
        _html_metric_table(summary.get("metrics")),
        "<h3>关键图表</h3>",
        _html_figures(summary.get("figures"), project_root=root, output_dir=output_dir),
        "</section>",
    ]

    appendix_parts = ["<section id=\"appendix\">", "<h2>4. 附录与复现信息</h2>"]
    appendix_parts.extend(
        [
            "<h3>数据范围</h3>",
            _html_bullets(appendix.get("data_scope"), empty="未提供数据范围说明。"),
            "<h3>指标口径</h3>",
            _html_bullets(appendix.get("metric_definitions"), empty="未提供指标口径说明。"),
            "<h3>输出文件</h3>",
            _html_bullets(appendix.get("output_files"), empty="未提供输出文件清单。"),
        ]
    )
    if coverage:
        appendix_parts.append("<h3>报告要求覆盖</h3>")
        appendix_parts.append(
            "<table><thead><tr><th>ID</th><th>状态</th><th>证据 / 原因</th></tr></thead><tbody>"
        )
        for entry in coverage:
            status = _text(entry.get("status"))
            detail_text = "；".join(
                [_text(item) for item in _items(entry.get("evidence"))]
                + ([_text(entry.get("reason"))] if _text(entry.get("reason")) else [])
            )
            appendix_parts.append(
                "<tr>"
                f"<td>{_escape(entry.get('id'))}</td>"
                f"<td>{_escape(_COVERAGE_LABELS.get(status, status))}</td>"
                f"<td>{_escape(detail_text)}</td>"
                "</tr>"
            )
        appendix_parts.append("</tbody></table>")
    appendix_parts.extend(
        [
            "<h3>复现信息</h3>",
            "<ul>",
            f"<li>运行 ID：<code>{_escape(run_id or '未绑定')}</code></li>",
            f"<li>主 Notebook：<code>{_escape(project.get('notebook_path') or 'notebooks/main_analysis.ipynb')}</code></li>",
            f"<li>分析框架：<code>{_escape(project.get('analysis_framework_path') or 'docs/analysis_framework.md')}</code></li>",
            f"<li>报告结构：<code>{_escape(project.get('report_structure_path') or 'reports/final/final_report_structure.md')}</code></li>",
            "</ul>",
            "</section>",
        ]
    )

    insights_html = []
    if with_insights:
        insights = _mapping(data.get("insights"))
        insights_html = [
            '<section id="insights">',
            "<h2>5. 可选洞察</h2>",
            '<p class="muted">本节仅在用户明确要求并启用洞察时渲染。</p>',
            _html_bullets(insights.get("items"), empty="未提供洞察内容。"),
            "</section>",
        ]
        toc.append('<li><a href="#insights">可选洞察</a></li>')

    question_block = "\n".join(question_sections)
    detail_block = "\n".join(detail_html)
    toc_html = "\n".join(toc)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="dsh-run-id" content="{_escape(run_id)}">
<title>{_escape(title)} · 分析过程详情</title>
<style>{_CSS}</style>
</head>
<body>
<div class="layout">
<nav class="toc">
<h2>目录</h2>
<ol>
{toc_html}
</ol>
</nav>
<main>
<header class="hero">
<p class="eyebrow">分析过程详情</p>
<h1>{_escape(title)}</h1>
<p class="subtitle">{_escape(summary.get("section_goal") or "完整记录分析范围、过程、证据与结论。")}</p>
<dl class="meta">
{chr(10).join(meta_lines)}
</dl>
<a class="button" href="{summary_href}">返回结论摘要</a>
</header>
{chr(10).join(overview)}
<section id="questions">
<h2>2. 业务问题分析</h2>
{question_block if question_block else '<p class="muted">未提供业务问题分析。</p>'}
</section>
{('<section id="detail"><h2>3. 详细分析过程</h2>' + detail_block + '</section>') if detail_block else ''}
{chr(10).join(appendix_parts)}
{chr(10).join(insights_html)}
</main>
</div>
<footer>
<p>本页由 <code>scripts/generate_final_report.py</code> 根据 <code>reports/final/report_inputs.yaml</code> 生成。结论摘要见 <a href="{summary_href}">{_escape(Path(summary_href).name)}</a>。</p>
</footer>
</body>
</html>
"""
