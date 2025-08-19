from __future__ import annotations

from datetime import datetime, date
from typing import Any, Dict, List

# Maps MySQL data_type to a simplified semantic type for Obsidian properties.
# We'll later use this to format frontmatter values.
MYSQL_TO_OBSIDIAN_TYPE = {
    # Integral
    "tinyint": "checkbox",  # special-case tinyint(1) to checkbox
    "smallint": "number",
    "mediumint": "number",
    "int": "number",
    "integer": "number",
    "bigint": "number",
    # Fixed/float
    "decimal": "number",
    "numeric": "number",
    "float": "number",
    "double": "number",
    "real": "number",
    # Date/time
    "date": "date",
    "datetime": "datetime",
    "timestamp": "datetime",
    "time": "text",  # no dedicated time type in Bases; store as text
    "year": "number",
    # String
    "char": "text",
    "varchar": "text",
    "tinytext": "text",
    "text": "text",
    "mediumtext": "text",
    "longtext": "text",
    # Binary (store as text or number length) – normally not exported
    "binary": "text",
    "varbinary": "text",
    "tinyblob": "text",
    "blob": "text",
    "mediumblob": "text",
    "longblob": "text",
    # JSON/list
    "json": "text",
    # Enum/set → text
    "enum": "text",
    "set": "text",
    # Geometry
    "geometry": "text",
}


def infer_property_types(columns: List[Dict[str, str]]) -> Dict[str, str]:
    inferred: Dict[str, str] = {}
    for meta in columns:
        name = meta["name"]
        data_type = meta["data_type"].lower()
        column_type = meta.get("column_type", "").lower()
        if data_type == "tinyint" and ("tinyint(1)" in column_type or column_type == "tinyint(1)"):
            inferred[name] = "checkbox"
        else:
            inferred[name] = MYSQL_TO_OBSIDIAN_TYPE.get(data_type, "text")
    return inferred


def normalize_frontmatter_key(key: str) -> str:
    return key.strip().replace(" ", "-").replace("_", "-").lower()


def format_value_for_frontmatter(value: Any, prop_type: str) -> Any:
    if value is None:
        return None
    if prop_type == "checkbox":
        if isinstance(value, bool):
            return value
        try:
            return bool(int(value))
        except Exception:
            return str(value).lower() in {"true", "yes", "y", "1"}
    if prop_type == "number":
        if isinstance(value, (int, float)):
            return value
        try:
            # If numeric string, cast to float, and to int if integral
            num = float(str(value))
            if num.is_integer():
                return int(num)
            return num
        except Exception:
            return None
    if prop_type == "date":
        # Expect date only
        if isinstance(value, date) and not isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        # string or datetime
        try:
            # Try parse common formats
            s = str(value)
            for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                try:
                    dt = datetime.strptime(s, fmt)
                    return dt.date().strftime("%Y-%m-%d")
                except Exception:
                    pass
        except Exception:
            pass
        return None
    if prop_type == "datetime":
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        # If date, promote to datetime with 00:00:00
        if isinstance(value, date):
            return datetime(value.year, value.month, value.day, 0, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
        # Try parse string
        s = str(value)
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                dt = datetime.strptime(s, fmt)
                # If date-only input, normalize to midnight
                if fmt == "%Y-%m-%d":
                    dt = datetime(dt.year, dt.month, dt.day, 0, 0, 0)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
        return None
    # text (default)
    return str(value)
