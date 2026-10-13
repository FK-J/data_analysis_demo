"""Execute project-declared table checks without encoding business defaults."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd

from src.io import load_table
from src.project_harness.config import resolve_project_path
from src.project_harness.validation import CheckResult, check


def run_table_checks(project_root: str | Path, rules: list[dict[str, Any]], *, category: str | None = None) -> list[CheckResult]:
    root = Path(project_root).resolve()
    selected = [rule for rule in rules if category is None or rule["category"] == category]
    if not selected:
        return [check("analysis_checks", "unverified", f"No {category or 'table'} checks are declared.", category="analysis")]
    cache: dict[str, pd.DataFrame] = {}

    def table(path: str) -> pd.DataFrame:
        if path not in cache:
            cache[path] = load_table(resolve_project_path(root, path))
        return cache[path]

    results = []
    for rule in selected:
        try:
            frame = table(rule["table"])
            kind = rule["kind"]
            tolerance = rule.get("tolerance", 0)
            if kind == "unique":
                keys = rule["keys"]
                passed = not frame[keys].isna().any().any() and not frame.duplicated(keys).any()
            elif kind == "non_null":
                passed = not frame[rule["column"]].isna().any()
            elif kind in {"range", "row_count"}:
                values = pd.Series([len(frame)]) if kind == "row_count" else pd.to_numeric(frame[rule["column"]], errors="raise")
                passed = bool(len(values)) and bool(values.notna().all()) and bool(values.map(math.isfinite).all())
                if "expected" in rule:
                    passed = passed and bool((values - rule["expected"]).abs().le(tolerance).all())
                if "min" in rule:
                    passed = passed and bool(values.ge(rule["min"] - tolerance).all())
                if "max" in rule:
                    passed = passed and bool(values.le(rule["max"] + tolerance).all())
            elif kind == "sum_equals":
                left = pd.to_numeric(frame[rule["column"]], errors="raise")
                right = pd.to_numeric(table(rule["other_table"])[rule["other_column"]], errors="raise")
                passed = bool(len(left)) and bool(len(right)) and bool(left.notna().all()) and bool(right.notna().all())
                passed = passed and bool(left.map(math.isfinite).all()) and bool(right.map(math.isfinite).all())
                passed = passed and abs(left.sum() - right.sum()) <= tolerance
            elif kind == "column_relation":
                left = pd.to_numeric(frame[rule["column"]], errors="raise")
                right = pd.to_numeric(frame[rule["other_column"]], errors="raise")
                comparison = {"le": lambda: left.le(right + tolerance), "eq": lambda: (left - right).abs().le(tolerance), "ge": lambda: left.ge(right - tolerance)}
                passed = bool(len(frame)) and bool(left.notna().all()) and bool(right.notna().all())
                passed = passed and bool(left.map(math.isfinite).all()) and bool(right.map(math.isfinite).all())
                passed = passed and bool(comparison[rule["operator"]]().all())
            else:
                raise ValueError(f"Unknown check kind: {kind}")
            message = f"{rule['id']}: {rule['description']} ({'passed' if passed else 'failed'})."
        except (OSError, ValueError, KeyError, TypeError, ImportError) as exc:
            passed = False
            message = f"{rule['id']}: {exc}"
        results.append(check("table_check", "pass" if passed else "fail", message, rule["table"], category="analysis"))
    return results
