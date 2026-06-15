"""Optional MySQL/MariaDB adapter."""

from __future__ import annotations

import importlib
from urllib.parse import parse_qsl, unquote, urlparse

from sqlnocturne.adapters.contract import future_mysql_manifest
from sqlnocturne.adapters.dbapi import DBAPIAdapter
from sqlnocturne.core.column import validate_identifier


class MySQLAdapter(DBAPIAdapter):
    name = "mysql"
    dialect_name = "mysql"
    driver_name = "pymysql"

    def load_driver(self):
        try:
            return importlib.import_module("pymysql")
        except ImportError:
            self.driver_name = "MySQLdb"
            return importlib.import_module("MySQLdb")

    def connect_args(self) -> dict:
        parsed = urlparse(self.uri)
        options = dict(parse_qsl(parsed.query, keep_blank_values=True))
        args = {
            "database": unquote(parsed.path.lstrip("/")),
            "user": unquote(parsed.username or ""),
            "password": unquote(parsed.password or ""),
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 3306,
            "connect_timeout": int(self.timeout),
        }
        args.update(options)
        return {key: value for key, value in args.items() if value not in {"", None}}

    def list_tables(self) -> list[str]:
        rows = self.fetch_all("SHOW TABLES")
        return [next(iter(row.values())) for row in rows]

    def table_exists(self, table: str) -> bool:
        table = validate_identifier(table, allow_dotted=False)
        return table in set(self.list_tables())

    def describe_table(self, table: str) -> list[dict]:
        table = validate_identifier(table, allow_dotted=False)
        return self.fetch_all(f"DESCRIBE `{table}`")

    def capabilities(self) -> dict:
        base = super().capabilities()
        base.update({"manifest": future_mysql_manifest().to_dict(), "available": self.connection is not None})
        return base
