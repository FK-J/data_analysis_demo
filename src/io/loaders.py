"""Stable local table loading entry points used by the main Notebook."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def load_table(path: str | Path, **kwargs: Any) -> pd.DataFrame:
    """Load a supported tabular file based on its extension."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Data file not found: {source}")

    suffix = source.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(source, **kwargs)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(source, **kwargs)
    if suffix == ".parquet":
        return pd.read_parquet(source, **kwargs)
    if suffix in {".json", ".jsonl"}:
        if suffix == ".jsonl" and "lines" not in kwargs:
            kwargs["lines"] = True
        return pd.read_json(source, **kwargs)
    raise ValueError(f"Unsupported table format: {suffix or '<no extension>'}")
