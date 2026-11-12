"""Database configuration and read-only engine tests."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from src.db import create_engine_from_profile, load_database_config
from src.db.connection import test_connection as check_connection
from src.project_harness.config import write_yaml


def _config(tmp_path, *, database: str, readonly: bool = True) -> dict:
    return {
        "default_profile": "local",
        "profiles": {
            "local": {
                "dialect": "sqlite",
                "database": database,
                "readonly": readonly,
            }
        },
    }


def test_environment_placeholder_expansion(tmp_path, monkeypatch):
    target = tmp_path / "env.db"
    monkeypatch.setenv("REVIEW_DB_PATH", str(target))
    path = tmp_path / "database.yaml"
    write_yaml(path, _config(tmp_path, database="${REVIEW_DB_PATH}"))
    config = load_database_config(path, "local")
    assert config["database"] == str(target)


def test_unresolved_environment_placeholder_is_rejected(tmp_path, monkeypatch):
    monkeypatch.delenv("REVIEW_MISSING_DB", raising=False)
    path = tmp_path / "database.yaml"
    write_yaml(path, _config(tmp_path, database="${REVIEW_MISSING_DB}"))
    with pytest.raises(ValueError, match="Unresolved environment placeholders"):
        load_database_config(path, "local")


def test_sqlite_readonly_profile_blocks_writes(tmp_path):
    path = tmp_path / "database.yaml"
    write_yaml(path, _config(tmp_path, database=str(tmp_path / "readonly.db")))
    engine = create_engine_from_profile(path, "local")
    assert check_connection(engine)["connection_ok"] == 1
    with pytest.raises(OperationalError):
        with engine.begin() as connection:
            connection.execute(text("create table should_not_exist (id integer)"))
