"""Utilities for reading and executing SQL files from the project sql/ folder."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover
    raise ImportError("Missing dependency pandas. Install it with: pip install pandas") from exc

try:
    from sqlalchemy import text
    from sqlalchemy.engine import Engine
except ImportError as exc:  # pragma: no cover
    raise ImportError("Missing dependency SQLAlchemy. Install it with: pip install SQLAlchemy") from exc


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WRITE_SQL_PATTERN = re.compile(
    r"\b(insert|update|delete|drop|truncate|create|alter|replace|merge|grant|revoke)\b",
    re.IGNORECASE,
)


def resolve_project_path(path: str | Path) -> Path:
    """Resolve a path relative to the project root."""
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    return resolved


def read_sql_file(sql_file: str | Path, encoding: str = "utf-8") -> str:
    """Read a SQL file as text."""
    path = resolve_project_path(sql_file)
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text(encoding=encoding)


def contains_write_statement(sql_text: str) -> bool:
    """Return True when SQL appears to contain write or DDL statements."""
    return bool(WRITE_SQL_PATTERN.search(sql_text))


def run_query_file(
    engine: Engine,
    sql_file: str | Path,
    params: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Execute a read-only SQL file and return the result as a DataFrame."""
    sql_text = read_sql_file(sql_file)
    if contains_write_statement(sql_text):
        raise ValueError(
            f"SQL file appears to contain write/DDL statements and cannot be run as a read query: {sql_file}"
        )
    return pd.read_sql_query(text(sql_text), con=engine, params=params or {})


def run_query_with_metadata(
    engine: Engine,
    sql_file: str | Path,
    params: dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Execute a query SQL file and return both DataFrame and execution metadata."""
    start = time.perf_counter()
    dataframe = run_query_file(engine=engine, sql_file=sql_file, params=params)
    elapsed_seconds = round(time.perf_counter() - start, 4)

    metadata = {
        "sql_file": str(resolve_project_path(sql_file)),
        "row_count": int(dataframe.shape[0]),
        "column_count": int(dataframe.shape[1]),
        "elapsed_seconds": elapsed_seconds,
    }
    return dataframe, metadata


def execute_statement_file(
    engine: Engine,
    sql_file: str | Path,
    params: dict[str, Any] | None = None,
    *,
    allow_write: bool = False,
) -> int:
    """Execute a SQL statement file and return affected row count.

    Write or DDL statements are blocked unless allow_write=True is explicitly
    passed by the caller.
    """
    sql_text = read_sql_file(sql_file)
    if contains_write_statement(sql_text) and not allow_write:
        raise ValueError(
            "This SQL file appears to contain write/DDL statements. "
            "Pass allow_write=True only after the user has confirmed the risk."
        )

    with engine.begin() as connection:
        result = connection.execute(text(sql_text), params or {})
        return int(result.rowcount if result.rowcount is not None else -1)
