"""Database connection helpers.

The connection code is intentionally stable across projects. Different projects
should switch database targets by changing configs/database.yaml or selecting a
different profile, not by editing this module.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise ImportError("Missing dependency PyYAML. Install it with: pip install PyYAML") from exc

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import Engine, URL
except ImportError as exc:  # pragma: no cover
    raise ImportError("Missing dependency SQLAlchemy. Install it with: pip install SQLAlchemy PyMySQL") from exc


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "database.yaml"
EXAMPLE_CONFIG_PATH = PROJECT_ROOT / "configs" / "database.example.yaml"
ENV_PATTERN = re.compile(r"\$\{([^}:]+)(?::([^}]*))?\}")


def _load_dotenv_if_available(project_root: Path) -> None:
    """Load .env if python-dotenv is installed."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    load_dotenv(project_root / ".env")


def _expand_env_value(value: Any) -> Any:
    """Expand ${VAR} or ${VAR:default} placeholders in config values."""
    if isinstance(value, dict):
        return {key: _expand_env_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand_env_value(item) for item in value]
    if not isinstance(value, str):
        return value

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        default = match.group(2)
        env_value = os.getenv(name)
        if env_value is not None:
            return env_value
        if default is not None:
            return default
        return match.group(0)

    return ENV_PATTERN.sub(replace, value)


def _ensure_no_unresolved_placeholders(config: dict[str, Any]) -> None:
    unresolved: list[str] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                walk(item, f"{path}.{key}" if path else str(key))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{path}[{index}]")
        elif isinstance(value, str) and ENV_PATTERN.search(value):
            unresolved.append(path)

    walk(config, "")
    if unresolved:
        joined = ", ".join(unresolved)
        raise ValueError(f"Unresolved environment placeholders in database config: {joined}")


def load_database_config(
    config_path: str | Path | None = None,
    profile: str | None = None,
) -> dict[str, Any]:
    """Load a database profile from YAML config.

    Parameters
    ----------
    config_path:
        Path to the real database config. Defaults to configs/database.yaml.
    profile:
        Profile name under the top-level profiles key. If omitted, uses
        default_profile from the config.
    """
    _load_dotenv_if_available(PROJECT_ROOT)

    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    if not path.exists():
        raise FileNotFoundError(
            f"Database config not found: {path}. "
            f"Copy {EXAMPLE_CONFIG_PATH} to {DEFAULT_CONFIG_PATH} and fill in the real values."
        )

    with path.open("r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file) or {}

    raw_config = _expand_env_value(raw_config)
    _ensure_no_unresolved_placeholders(raw_config)

    profiles = raw_config.get("profiles", {})
    selected_profile = profile or raw_config.get("default_profile")
    if not selected_profile:
        raise ValueError("No database profile specified and default_profile is missing.")
    if selected_profile not in profiles:
        available = ", ".join(sorted(profiles)) or "none"
        raise ValueError(f"Database profile '{selected_profile}' not found. Available profiles: {available}")

    config = dict(profiles[selected_profile])
    config["profile"] = selected_profile
    return config


def _validate_mysql_config(config: dict[str, Any]) -> None:
    required_keys = ["host", "port", "username", "database"]
    missing = [key for key in required_keys if config.get(key) in (None, "")]
    if missing:
        raise ValueError(f"Missing required MySQL config keys: {', '.join(missing)}")

    dialect = config.get("dialect", "mysql")
    if dialect != "mysql":
        raise ValueError(f"This project connection helper only supports MySQL, got dialect={dialect!r}.")


def _validate_sqlite_config(config: dict[str, Any]) -> None:
    database = config.get("database")
    if database in (None, ""):
        raise ValueError("Missing required SQLite config key: database")


def _build_mysql_url(config: dict[str, Any]) -> URL:
    driver = config.get("driver", "pymysql")
    charset = config.get("charset", "utf8mb4")
    return URL.create(
        drivername=f"mysql+{driver}",
        username=str(config["username"]),
        password=str(config.get("password", "")),
        host=str(config["host"]),
        port=int(config["port"]),
        database=str(config["database"]),
        query={"charset": charset},
    )


def _build_sqlite_url(config: dict[str, Any]) -> URL:
    database = str(config["database"])
    if database != ":memory:":
        database_path = Path(database)
        if not database_path.is_absolute():
            database_path = PROJECT_ROOT / database_path
        database_path.parent.mkdir(parents=True, exist_ok=True)
        database = str(database_path)

    return URL.create(drivername="sqlite", database=database)


def create_engine_from_profile(
    config_path: str | Path | None = None,
    profile: str | None = None,
    **overrides: Any,
) -> Engine:
    """Create a SQLAlchemy engine from a configured database profile.

    Supported dialects:
    - mysql
    - sqlite
    """
    config = load_database_config(config_path=config_path, profile=profile)
    config.update({key: value for key, value in overrides.items() if value is not None})

    dialect = str(config.get("dialect", "mysql")).lower()
    echo = bool(config.get("echo", False))

    if dialect == "mysql":
        _validate_mysql_config(config)
        connect_args = {
            "connect_timeout": int(config.get("connect_timeout", 10)),
            "read_timeout": int(config.get("read_timeout", 60)),
            "write_timeout": int(config.get("write_timeout", 60)),
        }
        return create_engine(
            _build_mysql_url(config),
            echo=echo,
            pool_pre_ping=bool(config.get("pool_pre_ping", True)),
            pool_recycle=int(config.get("pool_recycle", 3600)),
            connect_args=connect_args,
            future=True,
        )

    if dialect == "sqlite":
        _validate_sqlite_config(config)
        connect_args = {"check_same_thread": bool(config.get("check_same_thread", False))}
        return create_engine(
            _build_sqlite_url(config),
            echo=echo,
            connect_args=connect_args,
            future=True,
        )

    raise ValueError(
        f"Unsupported database dialect={dialect!r}. "
        "Supported dialects: mysql, sqlite."
    )


def create_mysql_engine(
    config_path: str | Path | None = None,
    profile: str | None = None,
    **overrides: Any,
) -> Engine:
    """Create a SQLAlchemy engine for a MySQL database profile."""
    config = load_database_config(config_path=config_path, profile=profile)
    config.update({key: value for key, value in overrides.items() if value is not None})
    _validate_mysql_config(config)
    return create_engine_from_profile(config_path=config_path, profile=profile, **overrides)


def test_connection(engine: Engine) -> dict[str, Any]:
    """Run a minimal test query and return the first row as a dict."""
    with engine.connect() as connection:
        row = connection.execute(text("select 1 as connection_ok")).mappings().one()
    return dict(row)
