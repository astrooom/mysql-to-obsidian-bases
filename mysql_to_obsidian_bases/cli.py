from __future__ import annotations

import argparse
import os
import sys
from typing import Dict


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export a MySQL table to Obsidian notes and a .base file"
    )
    parser.add_argument("--host", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--table", help="Table name to export")
    parser.add_argument(
        "--all-tables",
        action="store_true",
        help="Export all base tables in the database (exported one by one)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory. Defaults to ./output/<table>-base",
    )
    parser.add_argument(
        "--id-column",
        default=None,
        help="Column to use for filenames. Defaults to 'id' or first column",
    )
    parser.add_argument(
        "--title-column",
        default=None,
        help="Column to use as the note title (H1). Optional",
    )
    return parser


def export_single_table(
    host: str,
    user: str,
    password: str,
    database: str,
    port: int,
    table_name: str,
    output_root_override: str | None,
    id_column: str | None,
    title_column: str | None,
) -> None:
    from .mysql_utils import MySQLClient
    from .type_inference import infer_property_types, normalize_frontmatter_key
    from .markdown_generator import write_markdown_files
    from .base_generator import write_base_file

    base_folder_name = f"{table_name}-base"
    output_root = (
        output_root_override
        if output_root_override
        else os.path.join(os.getcwd(), "output", base_folder_name)
    )
    notes_subdir_name = "notes"
    notes_dir = os.path.join(output_root, notes_subdir_name)

    os.makedirs(notes_dir, exist_ok=True)

    print("Connecting to MySQL...")
    client = MySQLClient(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
    )

    try:
        client.connect()
    except Exception as exc:
        print(f"Failed to connect to MySQL: {exc}", file=sys.stderr)
        sys.exit(2)

    print(f"Fetching rows from '{table_name}'...")
    try:
        rows, columns = client.fetch_all_rows(table_name)
    except Exception as exc:
        print(f"Failed to fetch rows: {exc}", file=sys.stderr)
        sys.exit(3)
    finally:
        client.close()

    print(f"Fetched {len(rows)} rows and {len(columns)} columns")

    resolved_id_column: str
    if id_column:
        resolved_id_column = id_column
    else:
        resolved_id_column = "id" if any(c["name"] == "id" for c in columns) else columns[0]["name"]

    # Infer property types from MySQL schema
    column_types: Dict[str, str] = infer_property_types(columns)

    # Generate Markdown files
    print("Generating Markdown files...")
    generated = write_markdown_files(
        rows=rows,
        column_types=column_types,
        output_notes_dir=notes_dir,
        id_column=resolved_id_column,
        title_column=title_column,
        table_name=table_name,
    )
    print(f"Generated {generated} Markdown files in '{notes_dir}'")

    # Generate .base file
    print("Generating .base file...")
    normalized_property_keys = [normalize_frontmatter_key(k) for k in column_types.keys()]
    # Map normalized key back to type for column widths
    normalized_types = {normalize_frontmatter_key(k): v for k, v in column_types.items()}
    base_path = os.path.join(output_root, f"{table_name}.base")
    write_base_file(
        base_file_path=base_path,
        notes_folder_relative=f"{base_folder_name}/{notes_subdir_name}",
        property_keys=normalized_property_keys,
        view_name="Table",
        table_name=table_name,
        property_types_by_key=normalized_types,
    )
    print(f"Wrote base file: {base_path}")

    print("Done.")


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    if not args.all_tables and not args.table:
        print("Error: specify --table <name> or --all-tables", file=sys.stderr)
        sys.exit(1)

    if args.all_tables:
        from .mysql_utils import MySQLClient

        print("Connecting to MySQL to list tables...")
        client = MySQLClient(
            host=args.host,
            user=args.user,
            password=args.password,
            database=args.database,
            port=args.port,
        )
        try:
            client.connect()
            tables = client.list_tables()
        except Exception as exc:
            print(f"Failed to list tables: {exc}", file=sys.stderr)
            sys.exit(2)
        finally:
            client.close()

        if not tables:
            print("No base tables found.")
            return

        for t in tables:
            print(f"\n=== Exporting table: {t} ===")
            export_single_table(
                host=args.host,
                user=args.user,
                password=args.password,
                database=args.database,
                port=args.port,
                table_name=t,
                output_root_override=args.output,
                id_column=args.id_column,
                title_column=args.title_column,
            )
        return

    # Single-table export
    export_single_table(
        host=args.host,
        user=args.user,
        password=args.password,
        database=args.database,
        port=args.port,
        table_name=args.table,
        output_root_override=args.output,
        id_column=args.id_column,
        title_column=args.title_column,
    )
