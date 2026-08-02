"""Stable artifact export functions called by the main Notebook."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml


def export_dataframe(
    dataframe: pd.DataFrame,
    path: str | Path,
    *,
    index: bool = False,
) -> Path:
    """Export a DataFrame to CSV, Excel, or Parquet and return its path."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    suffix = destination.suffix.lower()
    if suffix == ".csv":
        dataframe.to_csv(destination, index=index)
    elif suffix in {".xlsx", ".xls"}:
        dataframe.to_excel(destination, index=index)
    elif suffix == ".parquet":
        dataframe.to_parquet(destination, index=index)
    else:
        raise ValueError(f"Unsupported export format: {suffix or '<no extension>'}")
    return destination


def write_report_inputs(data: dict[str, Any], path: str | Path) -> Path:
    """Write structured report inputs prepared by the Notebook."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return destination
