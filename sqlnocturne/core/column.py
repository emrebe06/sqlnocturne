"""Column and identifier helpers."""

from __future__ import annotations

from dataclasses import dataclass
import re


IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
STAR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\.\*$")


def validate_identifier(identifier: str, *, allow_star: bool = False, allow_dotted: bool = True) -> str:
    if not isinstance(identifier, str):
        raise TypeError("SQL identifier must be a string")
    value = identifier.strip()
    if not value:
        raise ValueError("SQL identifier cannot be empty")
    if allow_star and value == "*":
        return value
    if allow_star and STAR_RE.match(value):
        return value
    parts = value.split(".") if allow_dotted else [value]
    for part in parts:
        if not IDENTIFIER_RE.match(part):
            raise ValueError(f"Unsafe SQL identifier: {identifier!r}")
    return value


def quote_identifier(identifier: str, *, allow_star: bool = False) -> str:
    value = validate_identifier(identifier, allow_star=allow_star)
    if value == "*" or value.endswith(".*"):
        return value
    return ".".join(f'"{part}"' for part in value.split("."))


@dataclass(frozen=True, slots=True)
class Column:
    name: str
    alias: str | None = None

    def sql(self) -> str:
        base = quote_identifier(self.name, allow_star=True)
        if self.alias:
            return f"{base} AS {quote_identifier(self.alias, allow_star=False)}"
        return base

    def as_(self, alias: str) -> "Column":
        return Column(self.name, alias)


def normalize_columns(columns: tuple[str | Column, ...]) -> list[Column]:
    if not columns:
        return [Column("*")]
    normalized: list[Column] = []
    for column in columns:
        if isinstance(column, Column):
            normalized.append(column)
        elif isinstance(column, str):
            normalized.append(Column(column))
        else:
            raise TypeError("Columns must be strings or Column objects")
    return normalized
