"""Connection helpers."""

from __future__ import annotations

from sqlnocturne.core.config import DatabaseConfig
from sqlnocturne.core.errors import AdapterError
from sqlnocturne.adapters.mysql import MySQLAdapter
from sqlnocturne.adapters.postgresql import PostgreSQLAdapter
from sqlnocturne.adapters.sqlite import SQLiteAdapter


ADAPTER_SCHEMES = {
    "sqlite": SQLiteAdapter,
    "postgresql": PostgreSQLAdapter,
    "mysql": MySQLAdapter,
}


def register_adapter(scheme: str, adapter_cls) -> None:
    ADAPTER_SCHEMES[scheme.lower()] = adapter_cls


def create_adapter(config: DatabaseConfig):
    scheme = config.scheme
    if scheme not in ADAPTER_SCHEMES:
        raise AdapterError(
            "No adapter registered for database scheme",
            detail=f"Unsupported scheme: {scheme}. Register an adapter before using this URI.",
            code="ADAPTER_NOT_REGISTERED",
        )
    if scheme == "sqlite":
        return ADAPTER_SCHEMES[scheme](config.sqlite_path, timeout=config.timeout)
    return ADAPTER_SCHEMES[scheme](config.uri, timeout=config.timeout)
