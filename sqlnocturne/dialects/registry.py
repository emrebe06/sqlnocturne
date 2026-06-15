"""Dialect registry."""

from __future__ import annotations

from sqlnocturne.dialects.base import Dialect
from sqlnocturne.dialects.generic import MySQLDialect, PostgreSQLDialect
from sqlnocturne.dialects.sqlite import SQLiteDialect


_DIALECTS: dict[str, Dialect] = {}


def register_dialect(dialect: Dialect) -> None:
    _DIALECTS[dialect.name] = dialect


def get_dialect(name: str) -> Dialect:
    key = (name or "sqlite").lower()
    if not _DIALECTS:
        register_dialect(SQLiteDialect())
        register_dialect(PostgreSQLDialect())
        register_dialect(MySQLDialect())
    if key not in _DIALECTS:
        raise KeyError(f"Unknown SQL dialect: {name}")
    return _DIALECTS[key]


def available_dialects() -> list[str]:
    if not _DIALECTS:
        get_dialect("sqlite")
    return sorted(_DIALECTS)
