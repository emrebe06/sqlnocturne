"""Base dialect contract."""

from __future__ import annotations

from dataclasses import dataclass

from sqlnocturne.core.column import validate_identifier


@dataclass(frozen=True, slots=True)
class FeatureSet:
    returning: bool = False
    schemas: bool = False
    json_type: bool = False
    upsert: bool = False
    transactions: bool = True
    savepoints: bool = True
    foreign_keys: bool = True

    def to_dict(self) -> dict:
        return {
            "returning": self.returning,
            "schemas": self.schemas,
            "json_type": self.json_type,
            "upsert": self.upsert,
            "transactions": self.transactions,
            "savepoints": self.savepoints,
            "foreign_keys": self.foreign_keys,
        }


class Dialect:
    name = "base"
    placeholder = "?"
    quote_open = '"'
    quote_close = '"'
    features = FeatureSet()

    def quote_identifier(self, identifier: str, *, allow_star: bool = False) -> str:
        value = validate_identifier(identifier, allow_star=allow_star)
        if value == "*" or value.endswith(".*"):
            return value
        return ".".join(f"{self.quote_open}{part}{self.quote_close}" for part in value.split("."))

    def placeholders(self, count: int) -> list[str]:
        return [self.placeholder for _ in range(count)]

    def limit_offset(self, limit: int | None, offset: int | None) -> tuple[str, list[int]]:
        sql = ""
        params: list[int] = []
        if limit is not None:
            sql += f" LIMIT {self.placeholder}"
            params.append(limit)
        if offset is not None:
            sql += f" OFFSET {self.placeholder}"
            params.append(offset)
        return sql, params

    def create_table_prefix(self, if_not_exists: bool = True) -> str:
        return "CREATE TABLE IF NOT EXISTS" if if_not_exists else "CREATE TABLE"

    def supports(self, feature: str) -> bool:
        return bool(getattr(self.features, feature, False))

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "placeholder": self.placeholder,
            "quote_open": self.quote_open,
            "quote_close": self.quote_close,
            "features": self.features.to_dict(),
        }
