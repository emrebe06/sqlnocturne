"""Small DB-API adapter base for network databases."""

from __future__ import annotations

from typing import Any

from sqlnocturne.adapters.base import BaseAdapter
from sqlnocturne.core.errors import AdapterError, ConnectionError


class DBAPIAdapter(BaseAdapter):
    driver_name = "dbapi"

    def __init__(self, uri: str, *, timeout: float = 30.0):
        self.uri = uri
        self.timeout = timeout
        self.connection = None
        self.driver = None
        self._manual_transaction = False

    def load_driver(self):
        raise NotImplementedError

    def connect_args(self) -> dict:
        raise NotImplementedError

    def connect(self):
        try:
            self.driver = self.load_driver()
            self.connection = self.driver.connect(**self.connect_args())
            return self
        except ImportError as exc:
            raise AdapterError(
                "Database driver is not installed",
                detail=f"Install an optional driver for {self.name}: {exc}",
                code="DRIVER_NOT_INSTALLED",
            ) from exc
        except Exception as exc:
            raise ConnectionError(f"{self.name} connection failed", detail=str(exc)) from exc

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def execute(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None):
        connection = self._require_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(sql, list(params or []))
            if not self._manual_transaction:
                connection.commit()
            return cursor
        except Exception as exc:
            raise AdapterError(f"{self.name} execute failed", detail=str(exc)) from exc

    def fetch_all(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> list[dict]:
        cursor = self.execute(sql, params)
        columns = [column[0] for column in (cursor.description or [])]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def fetch_one(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> dict | None:
        cursor = self.execute(sql, params)
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [column[0] for column in (cursor.description or [])]
        return dict(zip(columns, row))

    def begin(self) -> None:
        self._manual_transaction = True

    def commit(self) -> None:
        self._require_connection().commit()
        self._manual_transaction = False

    def rollback(self) -> None:
        self._require_connection().rollback()
        self._manual_transaction = False

    def _require_connection(self):
        if self.connection is None:
            raise ConnectionError(f"{self.name} connection is not open")
        return self.connection

    def capabilities(self) -> dict:
        base = super().capabilities()
        base.update({"driver": self.driver_name, "uri": self.uri, "network": True})
        return base
