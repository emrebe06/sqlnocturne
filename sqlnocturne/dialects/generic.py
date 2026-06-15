"""Generic future dialects.

These classes are not connected to working adapters yet. They document the
target shape for future PostgreSQL/MySQL-style support without adding drivers.
"""

from sqlnocturne.dialects.base import Dialect, FeatureSet


class PostgreSQLDialect(Dialect):
    name = "postgresql"
    placeholder = "%s"
    quote_open = '"'
    quote_close = '"'
    features = FeatureSet(
        returning=True,
        schemas=True,
        json_type=True,
        upsert=True,
        transactions=True,
        savepoints=True,
        foreign_keys=True,
    )


class MySQLDialect(Dialect):
    name = "mysql"
    placeholder = "%s"
    quote_open = "`"
    quote_close = "`"
    features = FeatureSet(
        returning=False,
        schemas=True,
        json_type=True,
        upsert=True,
        transactions=True,
        savepoints=True,
        foreign_keys=True,
    )
