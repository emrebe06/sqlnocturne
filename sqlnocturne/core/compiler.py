"""SQL compiler for SQLNocturne query objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlnocturne.core.column import normalize_columns
from sqlnocturne.core.condition import Condition
from sqlnocturne.core.errors import QueryError


WRITE_TYPES = {"INSERT", "UPDATE", "DELETE"}


@dataclass(slots=True)
class CompiledQuery:
    sql: str
    params: list[Any] = field(default_factory=list)
    query_type: str = "RAW"
    table: str | None = None

    def to_dict(self) -> dict:
        return {
            "sql": self.sql,
            "params": list(self.params),
            "query_type": self.query_type,
            "table": self.table,
        }


def _quote(query, identifier: str, *, allow_star: bool = False) -> str:
    return query.database.dialect.quote_identifier(identifier, allow_star=allow_star)


def _compile_conditions(query, conditions: list[Condition]) -> tuple[str, list[Any]]:
    if not conditions:
        return "", []
    pieces: list[str] = []
    params: list[Any] = []
    for index, condition in enumerate(conditions):
        prefix = condition.boolean if index else ""
        column_sql = _quote(query, condition.column)
        if condition.is_null_check:
            part = f"{column_sql} {condition.operator} NULL"
        elif condition.is_sequence_operator:
            if not isinstance(condition.value, (list, tuple, set)):
                raise QueryError("IN and NOT IN conditions require a sequence value")
            values = list(condition.value)
            if not values:
                part = "1 = 0" if condition.operator == "IN" else "1 = 1"
            else:
                placeholders = ", ".join(query.database.dialect.placeholders(len(values)))
                part = f"{column_sql} {condition.operator} ({placeholders})"
                params.extend(values)
        else:
            part = f"{column_sql} {condition.operator} {query.database.dialect.placeholder}"
            params.append(condition.value)
        pieces.append(f"{prefix} {part}".strip())
    return " WHERE " + " ".join(pieces), params


def _compile_order(query, order_by: list[tuple[str, str]]) -> str:
    if not order_by:
        return ""
    pieces: list[str] = []
    for column, direction in order_by:
        direction = direction.upper().strip()
        if direction not in {"ASC", "DESC"}:
            raise QueryError("order direction must be ASC or DESC")
        pieces.append(f"{_quote(query, column)} {direction}")
    return " ORDER BY " + ", ".join(pieces)


def compile_select(query) -> CompiledQuery:
    columns = ", ".join(query.database.dialect.quote_identifier(column.name, allow_star=True) if not column.alias else f"{query.database.dialect.quote_identifier(column.name, allow_star=True)} AS {query.database.dialect.quote_identifier(column.alias)}" for column in normalize_columns(tuple(query.columns)))
    sql = f"SELECT {columns} FROM {_quote(query, query.table_name)}"
    params: list[Any] = []
    where_sql, where_params = _compile_conditions(query, query.conditions)
    sql += where_sql
    params.extend(where_params)
    sql += _compile_order(query, query.order_by)
    if query.limit_value is not None and query.limit_value < 0:
        raise QueryError("LIMIT cannot be negative")
    if query.offset_value is not None and query.offset_value < 0:
        raise QueryError("OFFSET cannot be negative")
    limit_sql, limit_params = query.database.dialect.limit_offset(query.limit_value, query.offset_value)
    sql += limit_sql
    params.extend(limit_params)
    return CompiledQuery(sql, params, "SELECT", query.table_name)


def compile_insert(query) -> CompiledQuery:
    if not query.values_data:
        raise QueryError("INSERT requires values")
    columns = list(query.values_data.keys())
    quoted = ", ".join(_quote(query, column) for column in columns)
    placeholders = ", ".join(query.database.dialect.placeholders(len(columns)))
    sql = f"INSERT INTO {_quote(query, query.table_name)} ({quoted}) VALUES ({placeholders})"
    params = [query.values_data[column] for column in columns]
    return CompiledQuery(sql, params, "INSERT", query.table_name)


def compile_update(query) -> CompiledQuery:
    if not query.set_data:
        raise QueryError("UPDATE requires set values")
    pieces: list[str] = []
    params: list[Any] = []
    for column, value in query.set_data.items():
        pieces.append(f"{_quote(query, column)} = {query.database.dialect.placeholder}")
        params.append(value)
    sql = f"UPDATE {_quote(query, query.table_name)} SET " + ", ".join(pieces)
    where_sql, where_params = _compile_conditions(query, query.conditions)
    sql += where_sql
    params.extend(where_params)
    return CompiledQuery(sql, params, "UPDATE", query.table_name)


def compile_delete(query) -> CompiledQuery:
    sql = f"DELETE FROM {_quote(query, query.table_name)}"
    where_sql, where_params = _compile_conditions(query, query.conditions)
    sql += where_sql
    return CompiledQuery(sql, where_params, "DELETE", query.table_name)


def compile_raw(sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> CompiledQuery:
    text = (sql or "").strip()
    if not text:
        raise QueryError("Raw SQL cannot be empty")
    query_type = text.split(None, 1)[0].upper() if text.split(None, 1) else "RAW"
    if query_type not in {"SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "PRAGMA", "WITH"}:
        query_type = "RAW"
    return CompiledQuery(text, list(params or []), query_type)


def compile_query(query) -> CompiledQuery:
    if query.query_type == "SELECT":
        return compile_select(query)
    if query.query_type == "INSERT":
        return compile_insert(query)
    if query.query_type == "UPDATE":
        return compile_update(query)
    if query.query_type == "DELETE":
        return compile_delete(query)
    if query.query_type == "RAW":
        return compile_raw(query.raw_sql, query.raw_params)
    raise QueryError(f"Unsupported query type: {query.query_type}")
