"""Generate the analyst-facing main Notebook from composable sections."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

try:
    import nbformat
except ImportError as exc:  # pragma: no cover
    raise ImportError("Missing dependency nbformat. Install it with: pip install nbformat") from exc

from .config import get_dotted_value, load_project_config, load_yaml, resolve_project_path, validate_project_config


DEFAULT_TEMPLATE = Path("templates/notebook_sections.yaml")


def write_notebook(notebook: Any, destination: Path) -> None:
    """Write a Notebook with LF endings on every supported platform."""
    with destination.open("w", encoding="utf-8", newline="\n") as file:
        nbformat.write(notebook, file)


def _section_enabled(section: dict[str, Any], config: dict[str, Any]) -> bool:
    requirements = section.get("requires") or []
    return all(bool(get_dotted_value(config, requirement)) for requirement in requirements)


def enabled_section_ids(config: dict[str, Any], template: dict[str, Any]) -> list[str]:
    """Return section IDs enabled by project.yaml in presentation order."""
    sections = template.get("sections") or []
    return [str(section["id"]) for section in sections if _section_enabled(section, config)]


def generate_notebook(
    project_root: str | Path,
    *,
    output_path: str | Path | None = None,
    template_path: str | Path | None = None,
) -> Path:
    """Build main_analysis.ipynb from project.yaml and section templates."""
    root = Path(project_root).resolve()
    config = validate_project_config(root, load_project_config(root))
    source_path = resolve_project_path(root, template_path or DEFAULT_TEMPLATE)
    template = load_yaml(source_path)
    sections = [section for section in template.get("sections") or [] if _section_enabled(section, config)]

    notebook = nbformat.v4.new_notebook()
    notebook.cells = []
    section_ids: list[str] = []
    display_name = config["project"]["display_name"]

    section_number = 0
    for section in sections:
        section_id = str(section["id"])
        section_ids.append(section_id)
        if bool(section.get("numbered", True)):
            section_number += 1
        for cell_spec in section.get("cells") or []:
            source = str(cell_spec.get("source", ""))
            source = source.replace("{section_number}", str(section_number))
            source = source.replace("{project_name}", display_name)
            metadata = dict(cell_spec.get("metadata") or {})
            tags = list(metadata.get("tags") or [])
            section_tag = f"harness-section-{section_id}"
            if section_tag not in tags:
                tags.append(section_tag)
            metadata["tags"] = tags
            if cell_spec.get("type") == "code":
                notebook.cells.append(nbformat.v4.new_code_cell(source=source, metadata=metadata))
            else:
                notebook.cells.append(nbformat.v4.new_markdown_cell(source=source, metadata=metadata))

    config_digest = hashlib.sha256(
        json.dumps(config, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    notebook.metadata.update(
        {
            "kernelspec": {
                "display_name": config["runtime"]["notebook_kernel"],
                "language": "python",
                "name": config["runtime"]["notebook_kernel"],
            },
            "language_info": {"name": "python"},
            "harness": {
                "generated": True,
                "schema_version": 1,
                "project_config_digest": config_digest,
                "sections": section_ids,
                "template": str(DEFAULT_TEMPLATE).replace("\\", "/"),
            },
        }
    )

    destination = resolve_project_path(root, output_path or config["runtime"]["notebook"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    write_notebook(notebook, destination)
    return destination
