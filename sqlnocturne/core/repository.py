"""Small repository helper.

The repository is optional. It is deliberately thin and table-oriented, not a
full ORM model system.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlnocturne.core.column import validate_identifier
from sqlnocturne.core.pagination import cursor_page, paginate_query
from sqlnocturne.core.result import Result


@dataclass(slots=True)
class RepositoryConfig:
    table: str
    primary_key: str = "id"
    default_limit: int = 50

    def __post_init__(self) -> None:
        validate_identifier(self.table)
        validate_identifier(self.primary_key)
        if self.default_limit < 1:
            raise ValueError("default_limit must be greater than zero")


class Repository:
    """Convenience wrapper around a table.

    This gives small apps a practical data-access pattern without turning
    SQLNocturne into a heavy ORM.
    """

    def __init__(self, db, table: str, *, primary_key: str = "id", default_limit: int = 50):
        self.db = db
        self.config = RepositoryConfig(table, primary_key, default_limit)

    @property
    def table_name(self) -> str:
        return self.config.table

    @property
    def primary_key(self) -> str:
        return self.config.primary_key

    def query(self):
        return self.db.table(self.table_name).select("*")

    def all(self, *, limit: int | None = None) -> Result:
        return self.query().limit(limit or self.config.default_limit).result()

    def page(self, *, page: int = 1, per_page: int | None = None) -> Result:
        return paginate_query(self.query(), page=page, per_page=per_page or self.config.default_limit)

    def cursor(self, *, after: Any = None, limit: int | None = None) -> Result:
        return cursor_page(self.query(), after=after, key=self.primary_key, limit=limit or self.config.default_limit)

    def get(self, value: Any) -> Result:
        return self.query().where(self.primary_key, "=", value).limit(1).result(fetch="one")

    def find_by(self, **where: Any) -> Result:
        query = self.query()
        for column, value in where.items():
            query.where(column, "=", value)
        return query.limit(1).result(fetch="one")

    def filter(self, **where: Any) -> Result:
        query = self.query()
        for column, value in where.items():
            query.where(column, "=", value)
        return query.limit(self.config.default_limit).result()

    def create(self, values: dict[str, Any] | None = None, **kwargs: Any) -> Result:
        merged = dict(values or {})
        merged.update(kwargs)
        return self.db.insert(self.table_name, merged).run()

    def update(self, key: Any, values: dict[str, Any] | None = None, **kwargs: Any) -> Result:
        merged = dict(values or {})
        merged.update(kwargs)
        return self.db.update(self.table_name).set(merged).where(self.primary_key, "=", key).run()

    def delete(self, key: Any) -> Result:
        return self.db.delete(self.table_name).where(self.primary_key, "=", key).run()

    def exists(self, key: Any) -> bool:
        result = self.get(key)
        return result.ok and result.data is not None

    def count(self) -> int:
        return self.query().count()

    def upsert_like(self, key: Any, values: dict[str, Any]) -> Result:
        """Portable update-then-insert helper.

        This avoids dialect-specific UPSERT syntax for now. Future dialects can
        add optimized native upsert methods.
        """

        existing = self.get(key)
        if existing.ok and existing.data:
            return self.update(key, values)
        payload = dict(values)
        payload.setdefault(self.primary_key, key)
        return self.create(payload)

    def to_dict(self) -> dict:
        return {
            "table": self.table_name,
            "primary_key": self.primary_key,
            "default_limit": self.config.default_limit,
        }
