"""Unit tests for the shared SQL text policy (no database driver required)."""

from __future__ import annotations

from src.project_harness.sql_policy import (
    contains_multiple_statements,
    contains_write_statement,
    is_read_query,
    normalize_sql_for_safety,
)


def test_write_keywords_inside_literals_and_comments_are_ignored():
    sql = "-- delete the staging table later\nselect 'update users set x=1' as note from t # drop\n"
    assert contains_write_statement(sql) is False


def test_write_statements_are_detected():
    assert contains_write_statement("update users set plan = 'pro' where id = 1") is True
    assert contains_write_statement("CREATE TABLE tmp AS SELECT 1") is True


def test_read_query_detection_skips_leading_comments():
    assert is_read_query("/* 说明 */\nwith base as (select 1) select * from base") is True
    assert is_read_query("update t set a = 1") is False


def test_multiple_statement_detection():
    assert contains_multiple_statements("select 1; select 2") is True
    assert contains_multiple_statements("select 1;\n") is False


def test_normalization_removes_comments_and_strings():
    normalized = normalize_sql_for_safety("select '--not a comment' from t /* block */")
    assert "--not a comment" not in normalized
    assert "/*" not in normalized
