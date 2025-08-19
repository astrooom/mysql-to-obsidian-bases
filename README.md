# MySQL → Obsidian Bases (CLI)

Convert rows from a MySQL table into Obsidian notes with YAML frontmatter and generate a corresponding `.base` file for the Bases core plugin.

## Features
- Connects to MySQL using CLI flags
- Exports each row to a Markdown file with properly-typed frontmatter
- Infers property types from MySQL schema (numbers, dates, datetimes, booleans, text)
- Generates a `.base` file that filters to the exported folder and provides a default Table view
- Idempotent by default (overwrites files with the same name)

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Usage

Preferred (console script):

```bash
mysql-to-bases \
  --host 127.0.0.1 \
  --user root \
  --password secret \
  --database mydb \
  --table books \
  --output /absolute/path/to/output \
  --id-column id \
  --title-column title
```

Export all tables:

```bash
mysql-to-bases \
  --host 127.0.0.1 \
  --user root \
  --password secret \
  --database mydb \
  --all-tables
```

Or via module:

```bash
python -m mysql_to_obsidian_bases --help
```

- You must specify either `--table <name>` or `--all-tables`.
- **--host/--user/--password/--database/--port**: MySQL connection
- **--table**: Table name to export
- **--all-tables**: Export every base table found in the database
- **--output**: Output directory for the base folder (default: `./output/<table>-base`)
- **--id-column**: Column used for filenames (default: `id` or first column)
- **--title-column**: Column used as the H1 title inside the note (optional)

After running, you'll have:
- `output/<table>-base/notes/` with one `.md` file per row
- `output/<table>-base/<table>.base` with a default Table view filtered to the above folder

### Example

```bash
mysql-to-bases \
  --host 127.0.0.1 --user root --password secret --database library \
  --table books --id-column id --title-column title
```

This creates something like:

```
output/books-base/
  books.base
  notes/
    1.md
    the-hitchhikers-guide-to-the-galaxy.md
    ...
```

Tip: Move the generated folder into your Obsidian vault. The `.base` file includes a filter that limits results to the `notes/` subfolder.

## Notes on Types and Formatting
- Dates (`DATE`) are formatted as `YYYY-MM-DD`
- Datetimes (`DATETIME`, `TIMESTAMP`) are formatted as `YYYY-MM-DD HH:mm:ss`
- Booleans (`TINYINT(1)`) become `true`/`false`
- Numbers remain numbers
- Strings are emitted as YAML strings when necessary

The `.base` file sets a global filter `file.inFolder("<table>-base/notes")` to scope the view to the generated notes.

## Stretch Goals (not yet implemented)
- `--query` to use a custom SQL query (type inference is trickier when not tied to a single table)
- Incremental updates (append-only or merge strategies)
- Per-column type overrides via a config file

## Development

Project structure:

```
mysql_to_obsidian_bases/
  __init__.py
  __main__.py
  cli.py
  mysql_utils.py
  type_inference.py
  markdown_generator.py
  base_generator.py
```

Run locally:

```bash
mysql-to-bases --help
```

## License
MIT
