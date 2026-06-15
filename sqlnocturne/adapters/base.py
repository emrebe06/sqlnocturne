"""Base adapter contract."""

from __future__ import annotations

from typing import Any


class BaseAdapter:
    name = "base"
    dialect_name = "base"

    def connect(self):
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    def execute(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None):
        raise NotImplementedError

    def fetch_all(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> list[dict]:
        raise NotImplementedError

    def fetch_one(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> dict | None:
        raise NotImplementedError

    def table_exists(self, table: str) -> bool:
        raise NotImplementedError

    def list_tables(self) -> list[str]:
        raise NotImplementedError

    def describe_table(self, table: str) -> list[dict]:
        raise NotImplementedError

    def begin(self) -> None:
        self.execute("BEGIN")

    def commit(self) -> None:
        self.execute("COMMIT")

    def rollback(self) -> None:
        self.execute("ROLLBACK")

    def capabilities(self) -> dict:
        return {
            "name": self.name,
            "dialect": self.dialect_name,
            "transactions": True,
            "schema_inspection": True,
        }
