"""Schema description and SQL generation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlnocturne.core.column import quote_identifier, validate_identifier
from sqlnocturne.core.result import Result


@dataclass(slots=True)
class ColumnSchema:
    name: str
    type: str = "TEXT"
    nullable: bool = True
    primary_key: bool = False
    unique: bool = False
    default: Any = None

    def __post_init__(self) -> None:
        validate_identifier(self.name)
        self.type = self.type.upper().strip()

    def ddl(self) -> str:
        pieces = [quote_identifier(self.name), self.type]
        if self.primary_key:
            pieces.append("PRIMARY KEY")
        if not self.nullable:
            pieces.append("NOT NULL")
        if self.unique:
            pieces.append("UNIQUE")
        if self.default is not None:
            pieces.append(f"DEFAULT {self._default_sql()}")
        return " ".join(pieces)

    def _default_sql(self) -> str:
        if isinstance(self.default, bool):
            return "1" if self.default else "0"
        if isinstance(self.default, (int, float)):
            return str(self.default)
        if str(self.default).upper() in {"CURRENT_TIMESTAMP", "CURRENT_DATE", "CURRENT_TIME"}:
            return str(self.default).upper()
        escaped = str(self.default).replace("'", "''")
        return f"'{escaped}'"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "nullable": self.nullable,
            "primary_key": self.primary_key,
            "unique": self.unique,
            "default": self.default,
        }


@dataclass(slots=True)
class IndexSchema:
    name: str
    columns: list[str]
    unique: bool = False

    def __post_init__(self) -> None:
        validate_identifier(self.name)
        for column in self.columns:
            validate_identifier(column)

    def ddl(self, table_name: str) -> str:
        unique = "UNIQUE " if self.unique else ""
        columns = ", ".join(quote_identifier(column) for column in self.columns)
        return f"CREATE {unique}INDEX IF NOT EXISTS {quote_identifier(self.name)} ON {quote_identifier(table_name)} ({columns})"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "columns": list(self.columns),
            "unique": self.unique,
        }


@dataclass(slots=True)
class TableSchema:
    name: str
    columns: list[ColumnSchema] = field(default_factory=list)
    indexes: list[IndexSchema] = field(default_factory=list)

    def __post_init__(self) -> None:
        validate_identifier(self.name)

    def column(
        self,
        name: str,
        type: str = "TEXT",
        *,
        nullable: bool = True,
        primary_key: bool = False,
        unique: bool = False,
        default: Any = None,
    ) -> "TableSchema":
        self.columns.append(ColumnSchema(name, type, nullable, primary_key, unique, default))
        return self

    def id(self, name: str = "id") -> "TableSchema":
        return self.column(name, "INTEGER", nullable=False, primary_key=True)

    def text(self, name: str, *, nullable: bool = True, unique: bool = False, default: Any = None) -> "TableSchema":
        return self.column(name, "TEXT", nullable=nullable, unique=unique, default=default)

    def integer(self, name: str, *, nullable: bool = True, default: Any = None) -> "TableSchema":
        return self.column(name, "INTEGER", nullable=nullable, default=default)

    def real(self, name: str, *, nullable: bool = True, default: Any = None) -> "TableSchema":
        return self.column(name, "REAL", nullable=nullable, default=default)

    def index(self, name: str, columns: list[str], *, unique: bool = False) -> "TableSchema":
        self.indexes.append(IndexSchema(name, columns, unique))
        return self

    def create_sql(self, *, if_not_exists: bool = True) -> str:
        if not self.columns:
            raise ValueError("TableSchema requires at least one column")
        exists = "IF NOT EXISTS " if if_not_exists else ""
        column_sql = ", ".join(column.ddl() for column in self.columns)
        return f"CREATE TABLE {exists}{quote_identifier(self.name)} ({column_sql})"

    def index_sql(self) -> list[str]:
        return [index.ddl(self.name) for index in self.indexes]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "columns": [column.to_dict() for column in self.columns],
            "indexes": [index.to_dict() for index in self.indexes],
        }


class SchemaBuilder:
    """Fluent schema builder for simple SQLite tables."""

    def __init__(self):
        self.tables: list[TableSchema] = []

    def table(self, name: str) -> TableSchema:
        table = TableSchema(name)
        self.tables.append(table)
        return table

    def create_all(self, db) -> Result:
        created = []
        for table in self.tables:
            result = db.sql(table.create_sql()).run()
            if not result.ok:
                return result
            created.append({"table": table.name, "sql": table.create_sql()})
            for index_sql in table.index_sql():
                index_result = db.sql(index_sql).run()
                if not index_result.ok:
                    return index_result
        return Result.success(created, message="Schema created", meta={"rows": len(created)})

    def to_dict(self) -> dict:
        return {
            "tables": [table.to_dict() for table in self.tables],
        }


def inspect_database(db) -> Result:
    tables = db.tables()
    if not tables.ok:
        return tables
    payload = {}
    for table in tables.data:
        payload[table] = {
            "columns": db.describe(table).data,
        }
    return Result.success(payload, message="Database schema inspected", meta={"rows": len(payload)})
