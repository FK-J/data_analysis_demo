"""Structured configuration helpers for generated analysis projects."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise ImportError("Missing dependency PyYAML. Install it with: pip install PyYAML") from exc


PROJECT_CONFIG_NAME = "project.yaml"
PROJECT_SCHEMA_PATH = Path("schemas/project.schema.yaml")


class ConfigError(ValueError):
    """Raised when a project configuration does not satisfy its contract."""


def resolve_project_path(project_root: str | Path, path: str | Path) -> Path:
    """Resolve a project-relative path and reject paths outside the project."""
    root = Path(project_root).resolve()
    candidate = Path(path)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ConfigError(f"Path must stay inside the project root: {path}") from exc
    return resolved


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML mapping from disk."""
    yaml_path = Path(path)
    if not yaml_path.exists():
        raise FileNotFoundError(f"YAML file not found: {yaml_path}")
    with yaml_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"YAML root must be a mapping: {yaml_path}")
    return data


def write_yaml(path: str | Path, data: dict[str, Any]) -> None:
    """Write a YAML mapping with stable, readable formatting."""
    yaml_path = Path(path)
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    yaml_path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def validate_against_schema(
    data: dict[str, Any],
    schema_path: str | Path,
    *,
    label: str,
) -> None:
    """Validate a mapping against a YAML-encoded JSON Schema."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:  # pragma: no cover
        raise ImportError("Missing dependency jsonschema. Install it with: pip install jsonschema") from exc

    schema = load_yaml(schema_path)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(data),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    if not errors:
        return

    details: list[str] = []
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        details.append(f"{location}: {error.message}")
    raise ConfigError(f"Invalid {label}: " + "; ".join(details))


def load_project_config(project_root: str | Path) -> dict[str, Any]:
    """Load project.yaml without validating it."""
    root = Path(project_root).resolve()
    return load_yaml(root / PROJECT_CONFIG_NAME)


def validate_project_config(
    project_root: str | Path,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load and validate the canonical project contract."""
    root = Path(project_root).resolve()
    project_config = config if config is not None else load_project_config(root)
    validate_against_schema(
        project_config,
        root / PROJECT_SCHEMA_PATH,
        label=PROJECT_CONFIG_NAME,
    )

    source_type = project_config["data"]["source_type"]
    modules = project_config["modules"]
    if source_type in {"database", "mixed"} and not modules["database"]:
        raise ConfigError("modules.database must be true when data.source_type uses a database.")
    if modules["database"] and not modules["sql"]:
        raise ConfigError("modules.sql must be true when modules.database is true.")
    for relative_path in project_config["runtime"].values():
        if isinstance(relative_path, str) and ("/" in relative_path or "\\" in relative_path):
            resolve_project_path(root, relative_path)
    for relative_path in project_config["paths"].values():
        resolve_project_path(root, relative_path)
    return project_config


def get_dotted_value(data: dict[str, Any], dotted_path: str) -> Any:
    """Read a dotted configuration value such as modules.statistics."""
    value: Any = data
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ConfigError(f"Unknown configuration key in notebook template: {dotted_path}")
        value = value[part]
    return value
