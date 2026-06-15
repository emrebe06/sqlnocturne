"""SQLite adapter backed by Python's standard library."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any

from sqlnocturne.adapters.base import BaseAdapter
from sqlnocturne.adapters.contract import sqlite_manifest
from sqlnocturne.core.column import validate_identifier
from sqlnocturne.core.errors import AdapterError, ConnectionError


class SQLiteAdapter(BaseAdapter):
    name = "sqlite"
    dialect_name = "sqlite"

    def __init__(self, path: str, *, timeout: float = 30.0):
        self.path = path
        self.timeout = timeout
        self.connection: sqlite3.Connection | None = None
        self._manual_transaction = False

    def connect(self) -> "SQLiteAdapter":
        try:
            if self.path != ":memory:":
                parent = Path(self.path).expanduser().resolve().parent
                parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(self.path, timeout=self.timeout)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON")
            return self
        except sqlite3.Error as exc:
            raise ConnectionError("SQLite connection failed", detail=str(exc)) from exc

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def execute(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None):
        connection = self._require_connection()
        try:
            cursor = connection.execute(sql, list(params or []))
            if not self._manual_transaction:
                connection.commit()
            return cursor
        except sqlite3.Error as exc:
            raise AdapterError("SQLite execute failed", detail=str(exc)) from exc

    def executemany(self, sql: str, rows: list[list[Any]] | list[tuple[Any, ...]]):
        connection = self._require_connection()
        try:
            cursor = connection.executemany(sql, rows)
            if not self._manual_transaction:
                connection.commit()
            return cursor
        except sqlite3.Error as exc:
            raise AdapterError("SQLite executemany failed", detail=str(exc)) from exc

    def begin(self) -> None:
        connection = self._require_connection()
        if self._manual_transaction:
            raise AdapterError("SQLite transaction is already active")
        connection.execute("BEGIN")
        self._manual_transaction = True

    def commit(self) -> None:
        connection = self._require_connection()
        connection.commit()
        self._manual_transaction = False

    def rollback(self) -> None:
        connection = self._require_connection()
        connection.rollback()
        self._manual_transaction = False

    def fetch_all(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> list[dict]:
        cursor = self.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def fetch_one(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> dict | None:
        cursor = self.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row is not None else None

    def table_exists(self, table: str) -> bool:
        row = self.fetch_one(
            "SELECT name FROM sqlite_master WHERE type = ? AND name = ?",
            ["table", table],
        )
        return row is not None

    def list_tables(self) -> list[str]:
        rows = self.fetch_all(
            "SELECT name FROM sqlite_master WHERE type = ? AND name NOT LIKE ? ORDER BY name",
            ["table", "sqlite_%"],
        )
        return [row["name"] for row in rows]

    def describe_table(self, table: str) -> list[dict]:
        safe_table = validate_identifier(table, allow_dotted=False)
        return self.fetch_all(f'PRAGMA table_info("{safe_table}")')

    def capabilities(self) -> dict:
        base = super().capabilities()
        base.update(
            {
                "memory_database": self.path == ":memory:",
                "foreign_keys": True,
                "row_factory": "sqlite3.Row",
                "manifest": sqlite_manifest(memory=self.path == ":memory:").to_dict(),
            }
        )
        return base

    def _require_connection(self) -> sqlite3.Connection:
        if self.connection is None:
            raise ConnectionError("SQLite connection is not open")
        return self.connection

    def __enter__(self) -> "SQLiteAdapter":
        if self.connection is None:
            self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
