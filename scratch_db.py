"""Read-only Flowise SQLite schema inspector; never prints row values."""

import os
import sqlite3
import sys
from pathlib import Path


def main() -> int:
    db_path = Path(
        os.environ.get("FLOWISE_DATABASE_PATH", r"D:\ai-agency-tools\flowise\data\database.sqlite")
    )
    if not db_path.is_file():
        print(f"Database not found: {db_path}")
        return 2

    uri = db_path.resolve().as_uri() + "?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as connection:
            tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            print(f"Database: {db_path}")
            for (table_name,) in tables:
                safe_name = table_name.replace('"', '""')
                columns = connection.execute(f'PRAGMA table_info("{safe_name}")').fetchall()
                names = [column[1] for column in columns]
                print(f"{table_name}: {', '.join(names)}")
        return 0
    except sqlite3.Error as error:
        print(f"SQLite inspection failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
