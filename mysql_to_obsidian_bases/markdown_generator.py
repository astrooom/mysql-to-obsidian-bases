from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Set

import yaml

from .type_inference import normalize_frontmatter_key, format_value_for_frontmatter


_slugify_pattern = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    s = value.strip().lower()
    s = _slugify_pattern.sub("-", s).strip("-")
    return s or "untitled"


def choose_filename(row: Dict[str, Any], id_column: str, table_name: str) -> str:
    if id_column in row and row[id_column] is not None:
        raw = str(row[id_column])
    else:
        # fallback: join first non-null values
        raw = "-".join(
            str(v) for v in row.values() if v is not None
        ) or table_name
    return slugify(raw) + ".md"


def ensure_unique_name_within_run(filename: str, used_names: Set[str]) -> str:
    if filename not in used_names:
        used_names.add(filename)
        return filename
    base, ext = os.path.splitext(filename)
    i = 2
    while True:
        candidate = f"{base}-{i}{ext}"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        i += 1


def build_frontmatter(row: Dict[str, Any], column_types: Dict[str, str]) -> Dict[str, Any]:
    fm: Dict[str, Any] = {}
    for key, val in row.items():
        prop_type = column_types.get(key, "text")
        yaml_key = normalize_frontmatter_key(key)
        yaml_val = format_value_for_frontmatter(val, prop_type)
        if yaml_val is None:
            continue
        fm[yaml_key] = yaml_val
    return fm


def write_markdown_files(
    rows: List[Dict[str, Any]],
    column_types: Dict[str, str],
    output_notes_dir: str,
    id_column: str,
    title_column: str | None,
    table_name: str,
) -> int:
    used_names: Set[str] = set()
    count = 0
    for row in rows:
        filename = choose_filename(row, id_column=id_column, table_name=table_name)
        filename = ensure_unique_name_within_run(filename, used_names)
        path = os.path.join(output_notes_dir, filename)

        fm = build_frontmatter(row, column_types)

        title_text = None
        if title_column and title_column in row and row[title_column] is not None:
            title_text = str(row[title_column])

        # Use safe_dump with yaml to ensure valid YAML, keep scalars native
        yaml_frontmatter = yaml.safe_dump(
            fm, sort_keys=False, allow_unicode=True, default_flow_style=False
        ).strip()

        content_lines: List[str] = ["---", yaml_frontmatter, "---", ""]
        if title_text:
            content_lines.append(f"# {title_text}")
            content_lines.append("")
        else:
            # Minimal content
            content_lines.append(f"# {os.path.splitext(os.path.basename(path))[0]}")
            content_lines.append("")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(content_lines))
        count += 1
    return count
