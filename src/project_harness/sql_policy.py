"""SQL text normalization shared by the read-only policy checks and the SQL runner.

The helpers stay dependency-free so project validation works even when the
database stack (SQLAlchemy/PyMySQL) is not installed.
"""

from __future__ import annotations

import re

WRITE_SQL_PATTERN = re.compile(
    r"\b(insert|update|delete|drop|truncate|create|alter|replace|merge|grant|revoke)\b",
    re.IGNORECASE,
)
READ_SQL_PATTERN = re.compile(r"^(select|with)\b", re.IGNORECASE)
BLOCK_COMMENT_PATTERN = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_PATTERN = re.compile(r"(--|#).*?$", re.MULTILINE)
SINGLE_QUOTED_STRING_PATTERN = re.compile(r"'(?:''|[^'])*'")
DOUBLE_QUOTED_STRING_PATTERN = re.compile(r'"(?:""|[^"])*"')


def strip_sql_comments(sql_text: str) -> str:
    """Remove SQL comments before safety checks."""
    without_block_comments = BLOCK_COMMENT_PATTERN.sub(" ", sql_text)
    return LINE_COMMENT_PATTERN.sub(" ", without_block_comments)


def strip_sql_strings(sql_text: str) -> str:
    """Remove quoted strings before keyword-based safety checks."""
    without_single_quotes = SINGLE_QUOTED_STRING_PATTERN.sub("''", sql_text)
    return DOUBLE_QUOTED_STRING_PATTERN.sub('""', without_single_quotes)


def normalize_sql_for_safety(sql_text: str) -> str:
    """Prepare SQL text for conservative keyword checks."""
    return strip_sql_comments(strip_sql_strings(sql_text)).strip()


def contains_write_statement(sql_text: str) -> bool:
    """Return True when SQL appears to contain write or DDL statements."""
    return bool(WRITE_SQL_PATTERN.search(normalize_sql_for_safety(sql_text)))


def is_read_query(sql_text: str) -> bool:
    """Return True when SQL starts with SELECT or WITH after comments are removed."""
    normalized = normalize_sql_for_safety(sql_text)
    return bool(READ_SQL_PATTERN.search(normalized))


def contains_multiple_statements(sql_text: str) -> bool:
    """Return True when SQL contains more than one statement."""
    normalized = normalize_sql_for_safety(sql_text).rstrip()
    while normalized.endswith(";"):
        normalized = normalized[:-1].rstrip()
    return ";" in normalized
