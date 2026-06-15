"""Revision file creation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re


REVISION_TEMPLATE = '''"""SQLNocturne migration: {name}."""


def up(db):
    # Write forward migration SQL here.
    # Example:
    # db.sql("""
    # CREATE TABLE IF NOT EXISTS users (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     name TEXT NOT NULL
    # )
    # """).run()
    pass


def down(db):
    # Write rollback SQL here.
    pass
'''


def slugify(name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower())
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "migration"


def revision_id(name: str) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{timestamp}_{slugify(name)}"


def versions_dir(root: str | Path) -> Path:
    return Path(root) / "versions"


def create_revision(root: str | Path, name: str) -> Path:
    folder = versions_dir(root)
    folder.mkdir(parents=True, exist_ok=True)
    version = revision_id(name)
    path = folder / f"{version}.py"
    path.write_text(REVISION_TEMPLATE.format(name=name), encoding="utf-8")
    return path
