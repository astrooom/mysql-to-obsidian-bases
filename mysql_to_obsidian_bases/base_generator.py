from __future__ import annotations

from typing import Dict, List

import yaml


DEFAULT_WIDTHS = {
    "text": 400,
    "number": 216,
    "checkbox": 120,
    "date": 216,
    "datetime": 260,
}


def write_base_file(
    base_file_path: str,
    notes_folder_relative: str,
    property_keys: List[str],
    view_name: str,
    table_name: str,
    property_types_by_key: Dict[str, str] | None = None,
) -> None:
    # Build ordered list of columns and width map using note.<prop> form
    order = [f"note.{k}" for k in property_keys]
    column_sizes = {}
    if property_types_by_key:
        for k in property_keys:
            t = property_types_by_key.get(k, "text")
            column_sizes[f"note.{k}"] = DEFAULT_WIDTHS.get(t, DEFAULT_WIDTHS["text"])

    data: Dict[str, object] = {
        "filters": {
            "and": [
                f'file.inFolder("{notes_folder_relative}")',
            ]
        },
        "properties": {k: {"displayName": k} for k in property_keys},
        "views": [
            {
                "type": "table",
                "name": view_name,
                "order": order,
            }
        ],
    }

    if column_sizes:
        # Attach sizes to the first view
        assert isinstance(data["views"], list)
        view0 = data["views"][0]  # type: ignore[index]
        view0["columnSize"] = column_sizes  # type: ignore[index]

    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    with open(base_file_path, "w", encoding="utf-8") as f:
        f.write(text)
