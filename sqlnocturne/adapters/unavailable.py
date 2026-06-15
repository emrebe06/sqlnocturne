"""Unavailable adapter placeholder for production-friendly errors."""

from __future__ import annotations

from typing import Any

from sqlnocturne.adapters.base import BaseAdapter
from sqlnocturne.adapters.contract import AdapterManifest, manifest_for
from sqlnocturne.core.errors import AdapterError


class UnavailableAdapter(BaseAdapter):
    """Adapter used when a dialect is known but its driver is not installed.

    This lets PostgreSQL/MySQL URIs be understood by configuration, health, and
    docs without pretending the real network driver exists yet.
    """

    def __init__(self, uri: str, *, timeout: float = 30.0, manifest: AdapterManifest | None = None):
        self.uri = uri
        self.timeout = timeout
        self.manifest = manifest or manifest_for("unknown")
        self.name = self.manifest.name
        self.dialect_name = self.manifest.dialect
        self.connected = False

    def connect(self):
        raise AdapterError(
            "Database adapter is not installed",
            detail=(
                f"SQLNocturne recognizes '{self.name}', but no production driver is bundled. "
                "Register a concrete adapter before opening this connection."
            ),
            code="ADAPTER_UNAVAILABLE",
        )

    def close(self) -> None:
        self.connected = False

    def execute(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None):
        raise AdapterError("Adapter is unavailable", detail=self.name, code="ADAPTER_UNAVAILABLE")

    def fetch_all(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> list[dict]:
        raise AdapterError("Adapter is unavailable", detail=self.name, code="ADAPTER_UNAVAILABLE")

    def fetch_one(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> dict | None:
        raise AdapterError("Adapter is unavailable", detail=self.name, code="ADAPTER_UNAVAILABLE")

    def table_exists(self, table: str) -> bool:
        raise AdapterError("Adapter is unavailable", detail=self.name, code="ADAPTER_UNAVAILABLE")

    def list_tables(self) -> list[str]:
        raise AdapterError("Adapter is unavailable", detail=self.name, code="ADAPTER_UNAVAILABLE")

    def describe_table(self, table: str) -> list[dict]:
        raise AdapterError("Adapter is unavailable", detail=self.name, code="ADAPTER_UNAVAILABLE")

    def capabilities(self) -> dict:
        data = super().capabilities()
        data.update(
            {
                "available": False,
                "uri": self.uri,
                "timeout": self.timeout,
                "manifest": self.manifest.to_dict(),
            }
        )
        return data
