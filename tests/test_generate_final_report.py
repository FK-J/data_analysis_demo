from __future__ import annotations

from pathlib import Path

from src.reporting.report import render_detail_html, render_summary_markdown


def _report_data() -> dict:
    return {
        "project": {
            "name": "demo",
            "report_title": "测试报告",
            "run_id": "20261104T000000Z-test",
            "generated_at": "2026-11-04 10:00:00",
            "analysis_framework_path": "docs/analysis_framework.md",
            "report_structure_path": "reports/final/final_report_structure.md",
            "notebook_path": "notebooks/main_analysis.ipynb",
        },
        "summary": {
            "section_goal": "汇总结果",
            "conclusions": ["核心结论一", "核心结论二 <script>alert(1)</script>"],
            "key_results": ["旧的汇总结果"],
            "metrics": [{"name": "样本数", "value": 10, "note": "测试"}],
            "figures": [{"title": "趋势图", "path": "reports/figures/trend.png", "note": "月度"}],
            "tables": [{"title": "结果表", "path": "reports/tables/result.csv"}],
        },
        "business_questions": [
            {
                "id": "Q1",
                "title": "核心问题",
                "section_goal": "回答问题",
                "conclusions": ["Q1 本节结论"],
                "analysis_logic": "比较结果",
                "process_steps": [
                    {
                        "title": "核对数据",
                        "method": "按账号去重",
                        "evidence": ["reports/tables/result.csv"],
                        "finding": "核对一致",
                    }
                ],
                "key_results": ["旧的 Q1 结果"],
                "figures": [{"title": "Q1 图", "path": "reports/figures/q1.png"}],
                "tables": [{"title": "Q1 表", "path": "reports/tables/q1.csv"}],
                "notes": ["测试口径"],
            }
        ],
        "detail": {
            "sections": [
                {
                    "id": "D1",
                    "title": "数据质量",
                    "conclusions": ["质量结论"],
                    "content": ["检查范围"],
                    "notes": ["质量限制"],
                }
            ]
        },
        "appendix": {
            "data_scope": ["测试数据"],
            "metric_definitions": ["样本数"],
            "output_files": [
                "reports/final/final_analysis_report.md",
                "reports/final/analysis_detail.html",
            ],
        },
        "coverage": [{"id": "Q1", "status": "covered", "evidence": ["reports/tables/result.csv"]}],
        "insights": {"enabled": True, "items": ["可选洞察"]},
    }


def test_summary_contains_only_conclusions_metrics_figures_and_index(tmp_path: Path) -> None:
    report = render_summary_markdown(
        _report_data(),
        project_root=tmp_path,
        output_path=tmp_path / "reports/final/final_analysis_report.md",
        detail_path=tmp_path / "reports/final/analysis_detail.html",
    )
    assert "核心结论一" in report
    assert "样本数" in report
    assert "趋势图" in report
    assert "analysis_detail.html#q-q1" in report
    assert "analysis_detail.html#detail-d1" in report
    assert "分析逻辑" not in report
    assert "测试口径" not in report
    assert "可选洞察" not in report


def test_summary_escapes_inline_html(tmp_path: Path) -> None:
    report = render_summary_markdown(
        _report_data(),
        project_root=tmp_path,
        output_path=tmp_path / "reports/final/final_analysis_report.md",
        detail_path=tmp_path / "reports/final/analysis_detail.html",
    )
    assert "<script>" not in report
    assert "&lt;script&gt;" in report


def test_detail_contains_per_section_conclusions_and_process(tmp_path: Path) -> None:
    detail = render_detail_html(
        _report_data(),
        project_root=tmp_path,
        output_path=tmp_path / "reports/final/analysis_detail.html",
        summary_path=tmp_path / "reports/final/final_analysis_report.md",
    )
    assert "Q1 本节结论" in detail
    assert "Q1 表" in detail
    assert "核对数据" in detail
    assert "核对一致" in detail
    assert "质量结论" in detail
    assert "<h3>本节结论</h3>" in detail
    assert 'name="dsh-run-id" content="20261104T000000Z-test"' in detail
    assert 'src="../figures/trend.png"' in detail
    assert "final_analysis_report.md" in detail


def test_detail_escapes_user_content(tmp_path: Path) -> None:
    detail = render_detail_html(
        _report_data(),
        project_root=tmp_path,
        output_path=tmp_path / "reports/final/analysis_detail.html",
        summary_path=tmp_path / "reports/final/final_analysis_report.md",
    )
    assert "<script>alert(1)</script>" not in detail
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in detail


def test_insights_only_render_when_enabled(tmp_path: Path) -> None:
    default = render_detail_html(
        _report_data(),
        project_root=tmp_path,
        output_path=tmp_path / "reports/final/analysis_detail.html",
        summary_path=tmp_path / "reports/final/final_analysis_report.md",
    )
    assert "可选洞察" not in default

    enabled = render_detail_html(
        _report_data(),
        project_root=tmp_path,
        output_path=tmp_path / "reports/final/analysis_detail.html",
        summary_path=tmp_path / "reports/final/final_analysis_report.md",
        with_insights=True,
    )
    assert "可选洞察" in enabled
