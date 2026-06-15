"""Main database facade."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlnocturne.core.compiler import CompiledQuery, compile_raw
from sqlnocturne.core.config import DatabaseConfig
from sqlnocturne.core.connection import create_adapter
from sqlnocturne.core.query import Query
from sqlnocturne.core.result import Result
from sqlnocturne.core.batch import Batch
from sqlnocturne.core.repository import Repository
from sqlnocturne.core.schema import SchemaBuilder, inspect_database
from sqlnocturne.core.table import Table
from sqlnocturne.core.transaction import Transaction
from sqlnocturne.dialects import get_dialect
from sqlnocturne.safety.guard import SafetyGuard


class Database:
    """SQLNocturne user-facing database object."""

    def __init__(
        self,
        uri: str,
        safe_mode: str = "strict",
        *,
        timeout: float = 30.0,
        migrations_path: str = "nocturne_migrations",
        echo: bool = False,
        connect: bool = True,
    ):
        self.config = DatabaseConfig(
            uri=uri,
            safe_mode=safe_mode,
            timeout=timeout,
            migrations_path=migrations_path,
            echo=echo,
        )
        self.guard = SafetyGuard(mode=safe_mode)
        self.dialect = get_dialect(self.config.scheme)
        self.adapter = create_adapter(self.config)
        if connect:
            self.adapter.connect()

    def connect(self) -> "Database":
        self.adapter.connect()
        return self

    def close(self) -> None:
        self.adapter.close()

    def table(self, name: str) -> Table:
        return Table(self, name)

    def get(self, table: str, where: dict[str, Any] | None = None) -> Result:
        query = self.table(table).select("*").limit(1)
        for column, value in (where or {}).items():
            query.where(column, "=", value)
        return query.result(fetch="one")

    def insert(self, table: str, values: dict[str, Any] | None = None, **kwargs: Any) -> Query:
        return Query(self, table, "INSERT").values(values, **kwargs)

    def update(self, table: str) -> Query:
        return Query(self, table, "UPDATE")

    def delete(self, table: str) -> Query:
        return Query(self, table, "DELETE")

    def sql(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> Query:
        return Query(self, None, "RAW", raw_sql=sql, raw_params=params)

    def execute(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> Result:
        return self.sql(sql, params).run()

    def fetch_all(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> Result:
        return self.sql(sql, params).result(fetch="all")

    def fetch_one(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> Result:
        return self.sql(sql, params).result(fetch="one")

    def inspect_sql(self, sql: str, query_type: str | None = None) -> dict:
        return self.guard.inspect(sql, query_type)

    def tables(self) -> Result:
        try:
            tables = self.adapter.list_tables()
            return Result.success(tables, message="Tables listed", meta={"rows": len(tables), "adapter": self.adapter.name})
        except Exception as exc:
            return Result.error_result(
                code="INSPECT_FAILED",
                message="Could not list tables",
                detail=str(exc),
                error_type="adapter_error",
            )

    def transaction(self, name: str | None = None) -> Transaction:
        return Transaction(self, name=name)

    def batch(self, *, transactional: bool = True) -> Batch:
        return Batch(self, transactional=transactional)

    def schema(self) -> SchemaBuilder:
        return SchemaBuilder()

    def repository(self, table: str, *, primary_key: str = "id", default_limit: int = 50) -> Repository:
        return Repository(self, table, primary_key=primary_key, default_limit=default_limit)

    def inspect_schema(self) -> Result:
        return inspect_database(self)

    def health(self) -> Result:
        from sqlnocturne.health import check_database

        return check_database(self)

    def export_json(self, result_or_rows, path=None) -> Result:
        from sqlnocturne.io import export_json

        return export_json(result_or_rows, path)

    def import_json(self, table: str, source, *, transactional: bool = True) -> Result:
        from sqlnocturne.io import import_json_rows

        return import_json_rows(self, table, source, transactional=transactional)

    def describe(self, table: str) -> Result:
        try:
            rows = self.adapter.describe_table(table)
            return Result.success(rows, message="Table described", meta={"rows": len(rows), "table": table})
        except Exception as exc:
            return Result.error_result(
                code="INSPECT_FAILED",
                message="Could not describe table",
                detail=str(exc),
                error_type="adapter_error",
            )

    def migration_path(self) -> Path:
        return Path(self.config.migrations_path)

    def _execute_compiled(self, compiled: CompiledQuery, fetch: str) -> tuple[Any, int]:
        if self.config.echo:
            print(f"[sqlnocturne] {compiled.sql} params={compiled.params}")
        if fetch == "all":
            rows = self.adapter.fetch_all(compiled.sql, compiled.params)
            return rows, len(rows)
        if fetch == "one":
            row = self.adapter.fetch_one(compiled.sql, compiled.params)
            return row, 1 if row is not None else 0
        cursor = self.adapter.execute(compiled.sql, compiled.params)
        rows = cursor.rowcount if cursor.rowcount is not None and cursor.rowcount >= 0 else 0
        return {"rowcount": rows, "lastrowid": getattr(cursor, "lastrowid", None)}, rows

    def run_compiled(self, compiled: CompiledQuery, *, fetch: str = "none") -> Result:
        inspection = self.guard.inspect(compiled.sql, compiled.query_type)
        if not inspection.get("allowed", True):
            return Result.from_safety(inspection)
        try:
            data, rows = self._execute_compiled(compiled, fetch)
            return Result.success(
                data,
                message="Compiled query executed",
                meta={
                    "rows": rows,
                    "query_type": compiled.query_type,
                    "risk_score": inspection.get("risk_score", 0.0),
                    "warnings": inspection.get("warnings", []),
                },
            )
        except Exception as exc:
            return Result.error_result(
                code="QUERY_FAILED",
                message="Compiled query failed",
                detail=str(exc),
                error_type="query_error",
            )

    def raw_compiled(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> CompiledQuery:
        return compile_raw(sql, params)

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
