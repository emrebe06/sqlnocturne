"""Table facade."""

from __future__ import annotations

from typing import Any

from sqlnocturne.core.column import validate_identifier
from sqlnocturne.core.query import Query


class Table:
    """Convenience facade returned by ``Database.table(name)``."""

    def __init__(self, database, name: str):
        self.database = database
        self.name = validate_identifier(name)

    def select(self, *columns: str) -> Query:
        return Query(self.database, self.name, "SELECT").select(*columns)

    def where(self, column: str, operator: str, value: Any) -> Query:
        return self.select().where(column, operator, value)

    def limit(self, value: int) -> Query:
        return self.select().limit(value)

    def order(self, column: str, direction: str = "ASC") -> Query:
        return self.select().order(column, direction)

    def insert(self, values: dict[str, Any] | None = None, **kwargs: Any) -> Query:
        return Query(self.database, self.name, "INSERT").values(values, **kwargs)

    def update(self) -> Query:
        return Query(self.database, self.name, "UPDATE")

    def delete(self) -> Query:
        return Query(self.database, self.name, "DELETE")

    def all(self) -> list[dict]:
        return self.select().all()

    def one(self) -> dict | None:
        return self.select().limit(1).one()

    def result(self):
        return self.select().result()

    def count(self) -> int:
        return self.select().count()

    def __repr__(self) -> str:
        return f"Table({self.name!r})"
