"""Migration snapshot file helpers."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path


DEFAULT_SNAPSHOT = {
    "engine": "sqlnocturne",
    "version": 1,
    "created_at": None,
    "tables": {},
    "notes": [],
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def snapshot_path(root: str | Path) -> Path:
    return Path(root) / "snapshot.json"


def load_snapshot(root: str | Path) -> dict:
    path = snapshot_path(root)
    if not path.exists():
        data = dict(DEFAULT_SNAPSHOT)
        data["created_at"] = now_iso()
        return data
    return json.loads(path.read_text(encoding="utf-8"))


def save_snapshot(root: str | Path, data: dict) -> Path:
    path = snapshot_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(data)
    payload.setdefault("engine", "sqlnocturne")
    payload.setdefault("version", 1)
    payload.setdefault("created_at", now_iso())
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def capture_sqlite_schema(db) -> dict:
    tables = {}
    table_result = db.tables()
    if not table_result.ok:
        return tables
    for table in table_result.data:
        if table == "sqlnocturne_migrations":
            continue
        desc = db.describe(table)
        tables[table] = desc.data if desc.ok else []
    return tables
