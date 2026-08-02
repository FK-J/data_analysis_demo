"""Reusable baseline data quality checks for analyst-facing projects."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


def build_quality_summary(
    dataframe: pd.DataFrame,
    *,
    primary_key: str | Sequence[str] | None = None,
) -> pd.DataFrame:
    """Return a compact quality summary suitable for Notebook display and export."""
    duplicate_rows = int(dataframe.duplicated().sum())
    missing_cells = int(dataframe.isna().sum().sum())
    rows: list[dict[str, object]] = [
        {"check": "row_count", "value": int(len(dataframe)), "status": "info", "details": ""},
        {
            "check": "column_count",
            "value": int(dataframe.shape[1]),
            "status": "info",
            "details": "",
        },
        {
            "check": "duplicate_rows",
            "value": duplicate_rows,
            "status": "pass" if duplicate_rows == 0 else "warn",
            "details": "Exact duplicate rows",
        },
        {
            "check": "missing_cells",
            "value": missing_cells,
            "status": "pass" if missing_cells == 0 else "warn",
            "details": "Missing values across all columns",
        },
    ]

    if primary_key is not None:
        keys = [primary_key] if isinstance(primary_key, str) else list(primary_key)
        missing_keys = [key for key in keys if key not in dataframe.columns]
        if missing_keys:
            rows.append(
                {
                    "check": "primary_key",
                    "value": None,
                    "status": "fail",
                    "details": f"Missing columns: {', '.join(missing_keys)}",
                }
            )
        else:
            duplicate_keys = int(dataframe.duplicated(subset=keys).sum())
            null_keys = int(dataframe[keys].isna().any(axis=1).sum())
            rows.extend(
                [
                    {
                        "check": "primary_key_duplicates",
                        "value": duplicate_keys,
                        "status": "pass" if duplicate_keys == 0 else "fail",
                        "details": ", ".join(keys),
                    },
                    {
                        "check": "primary_key_null_rows",
                        "value": null_keys,
                        "status": "pass" if null_keys == 0 else "fail",
                        "details": ", ".join(keys),
                    },
                ]
            )
    return pd.DataFrame(rows)
