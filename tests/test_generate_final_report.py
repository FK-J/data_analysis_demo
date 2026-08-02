from __future__ import annotations

from scripts.generate_final_report import render_report


def _report_data() -> dict:
    return {
        "project": {"name": "demo", "report_title": "测试报告"},
        "summary": {
            "section_goal": "汇总结果",
            "key_results": ["结果一"],
            "metrics": [{"name": "样本数", "value": 10, "note": "测试"}],
            "figures": [],
            "tables": [],
        },
        "business_questions": [
            {
                "id": "Q1",
                "title": "核心问题",
                "section_goal": "回答问题",
                "analysis_logic": "比较结果",
                "key_results": ["问题结果"],
                "figures": [],
                "tables": [],
                "notes": ["测试口径"],
            }
        ],
        "appendix": {
            "data_scope": ["测试数据"],
            "metric_definitions": ["样本数"],
            "output_files": ["reports/final/final_analysis_report.md"],
        },
        "insights": {"enabled": True, "items": ["可选洞察"]},
    }


def test_report_does_not_render_insights_by_default() -> None:
    report = render_report(_report_data(), with_insights=False)
    assert "结果一" in report
    assert "可选洞察" not in report


def test_report_renders_prepared_insights_only_when_enabled() -> None:
    report = render_report(_report_data(), with_insights=True)
    assert "可选洞察" in report
