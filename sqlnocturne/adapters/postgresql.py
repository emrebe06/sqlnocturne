"""Optional PostgreSQL adapter."""

from __future__ import annotations

import importlib
from urllib.parse import parse_qsl, unquote, urlparse

from sqlnocturne.adapters.contract import future_postgresql_manifest
from sqlnocturne.adapters.dbapi import DBAPIAdapter
from sqlnocturne.core.column import validate_identifier


class PostgreSQLAdapter(DBAPIAdapter):
    name = "postgresql"
    dialect_name = "postgresql"
    driver_name = "psycopg"

    def load_driver(self):
        try:
            return importlib.import_module("psycopg")
        except ImportError:
            self.driver_name = "psycopg2"
            return importlib.import_module("psycopg2")

    def connect_args(self) -> dict:
        parsed = urlparse(self.uri)
        options = dict(parse_qsl(parsed.query, keep_blank_values=True))
        args = {
            "dbname": unquote(parsed.path.lstrip("/")),
            "user": unquote(parsed.username or ""),
            "password": unquote(parsed.password or ""),
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "connect_timeout": int(self.timeout),
        }
        args.update(options)
        return {key: value for key, value in args.items() if value not in {"", None}}

    def list_tables(self) -> list[str]:
        rows = self.fetch_all(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
            """
        )
        return [row["table_name"] for row in rows]

    def table_exists(self, table: str) -> bool:
        table = validate_identifier(table, allow_dotted=False)
        row = self.fetch_one(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s
            """,
            [table],
        )
        return row is not None

    def describe_table(self, table: str) -> list[dict]:
        table = validate_identifier(table, allow_dotted=False)
        return self.fetch_all(
            """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            [table],
        )

    def capabilities(self) -> dict:
        base = super().capabilities()
        base.update({"manifest": future_postgresql_manifest().to_dict(), "available": self.connection is not None})
        return base
