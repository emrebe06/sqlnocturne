"""SQLite dialect."""

from sqlnocturne.dialects.base import Dialect, FeatureSet


class SQLiteDialect(Dialect):
    name = "sqlite"
    placeholder = "?"
    quote_open = '"'
    quote_close = '"'
    features = FeatureSet(
        returning=True,
        schemas=False,
        json_type=False,
        upsert=True,
        transactions=True,
        savepoints=True,
        foreign_keys=True,
    )
