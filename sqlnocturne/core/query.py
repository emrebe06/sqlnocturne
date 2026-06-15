"""Fluent query builder."""

from __future__ import annotations

from copy import deepcopy
from time import perf_counter
from typing import Any

from sqlnocturne.core.compiler import CompiledQuery, compile_query
from sqlnocturne.core.condition import Condition
from sqlnocturne.core.errors import QueryError
from sqlnocturne.core.result import Result


class Query:
    """A small immutable-ish query builder.

    Methods mutate and return ``self`` for simple fluent use. The object is not
    meant to be shared across threads.
    """

    def __init__(
        self,
        database,
        table_name: str | None = None,
        query_type: str = "SELECT",
        *,
        raw_sql: str | None = None,
        raw_params: list[Any] | tuple[Any, ...] | None = None,
    ):
        self.database = database
        self.table_name = table_name
        self.query_type = query_type.upper()
        self.raw_sql = raw_sql or ""
        self.raw_params = list(raw_params or [])
        self.columns: list[Any] = ["*"]
        self.conditions: list[Condition] = []
        self.limit_value: int | None = None
        self.offset_value: int | None = None
        self.order_by: list[tuple[str, str]] = []
        self.values_data: dict[str, Any] = {}
        self.set_data: dict[str, Any] = {}

    def clone(self) -> "Query":
        other = Query(
            self.database,
            self.table_name,
            self.query_type,
            raw_sql=self.raw_sql,
            raw_params=self.raw_params,
        )
        other.columns = deepcopy(self.columns)
        other.conditions = deepcopy(self.conditions)
        other.limit_value = self.limit_value
        other.offset_value = self.offset_value
        other.order_by = deepcopy(self.order_by)
        other.values_data = deepcopy(self.values_data)
        other.set_data = deepcopy(self.set_data)
        return other

    def select(self, *columns: str) -> "Query":
        self.query_type = "SELECT"
        self.columns = list(columns) if columns else ["*"]
        return self

    def where(self, column: str, operator: str, value: Any) -> "Query":
        self.conditions.append(Condition(column, operator, value, "AND"))
        return self

    def or_where(self, column: str, operator: str, value: Any) -> "Query":
        self.conditions.append(Condition(column, operator, value, "OR"))
        return self

    def limit(self, value: int) -> "Query":
        self.limit_value = int(value)
        return self

    def offset(self, value: int) -> "Query":
        self.offset_value = int(value)
        return self

    def order(self, column: str, direction: str = "ASC") -> "Query":
        self.order_by.append((column, direction))
        return self

    def values(self, values: dict[str, Any] | None = None, **kwargs: Any) -> "Query":
        self.query_type = "INSERT"
        merged = dict(values or {})
        merged.update(kwargs)
        self.values_data.update(merged)
        return self

    def set(self, values: dict[str, Any] | None = None, **kwargs: Any) -> "Query":
        self.query_type = "UPDATE"
        merged = dict(values or {})
        merged.update(kwargs)
        self.set_data.update(merged)
        return self

    def delete(self) -> "Query":
        self.query_type = "DELETE"
        return self

    def compile(self) -> CompiledQuery:
        return compile_query(self)

    def explain(self) -> Result:
        try:
            compiled = self.compile()
            inspection = self.database.guard.inspect(compiled.sql, compiled.query_type)
            return Result.success(
                {
                    "compiled": compiled.to_dict(),
                    "safety": inspection,
                },
                message="Query explained",
                meta={"safe_mode": self.database.config.safe_mode},
            )
        except Exception as exc:
            return Result.error_result(
                code="EXPLAIN_ERROR",
                message="Query explain failed",
                detail=str(exc),
                error_type="query_error",
            )

    def all(self) -> list[dict]:
        result = self.result(fetch="all")
        if not result.ok:
            return []
        return result.data or []

    def one(self) -> dict | None:
        result = self.result(fetch="one")
        if not result.ok:
            return None
        return result.data

    def run(self) -> Result:
        return self.result(fetch="none")

    def result(self, *, fetch: str | None = None) -> Result:
        start = perf_counter()
        try:
            compiled = self.compile()
            inspection = self.database.guard.inspect(compiled.sql, compiled.query_type)
            if not inspection.get("allowed", True):
                return Result.from_safety(inspection)
            fetch_mode = fetch or self._default_fetch(compiled.query_type)
            data, rows = self.database._execute_compiled(compiled, fetch_mode)
            elapsed = (perf_counter() - start) * 1000
            return Result.success(
                data,
                message=self._success_message(compiled.query_type),
                meta={
                    "rows": rows,
                    "time_ms": round(elapsed, 3),
                    "query_type": compiled.query_type,
                    "table": compiled.table,
                    "risk_score": inspection.get("risk_score", 0.0),
                    "risk_level": inspection.get("level", "safe"),
                    "warnings": inspection.get("warnings", []),
                    "safe_mode": self.database.config.safe_mode,
                    "adapter": self.database.adapter.name,
                },
            )
        except QueryError as exc:
            return Result.error_result(
                code=exc.code,
                message=exc.message,
                detail=exc.detail,
                error_type=exc.error_type,
                meta={"adapter": self.database.adapter.name},
            )
        except Exception as exc:
            return Result.error_result(
                code="QUERY_FAILED",
                message="Query execution failed",
                detail=str(exc),
                error_type="query_error",
                meta={"adapter": self.database.adapter.name},
            )

    def scalar(self, default: Any = None) -> Any:
        row = self.one()
        if not row:
            return default
        if isinstance(row, dict):
            return next(iter(row.values()), default)
        return row

    def count(self) -> int:
        clone = self.clone()
        clone.columns = ["*"]
        compiled = clone.compile()
        count_query = Query(self.database, self.table_name, "RAW", raw_sql=f"SELECT COUNT(*) AS count FROM ({compiled.sql}) AS _q", raw_params=compiled.params)
        row = count_query.one()
        return int(row["count"]) if row and "count" in row else 0

    def _default_fetch(self, query_type: str) -> str:
        if query_type in {"SELECT", "WITH", "PRAGMA"}:
            return "all"
        return "none"

    def _success_message(self, query_type: str) -> str:
        return {
            "SELECT": "Rows selected",
            "INSERT": "Row inserted",
            "UPDATE": "Rows updated",
            "DELETE": "Rows deleted",
            "CREATE": "Statement executed",
            "DROP": "Statement executed",
            "ALTER": "Statement executed",
            "RAW": "Statement executed",
        }.get(query_type, "Query executed")
