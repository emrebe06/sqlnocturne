"""SQL dialect definitions.

SQLite is the first working adapter, but SQLNocturne's architecture is not
SQLite-only. Dialects describe quoting, placeholder style, and feature flags so
future adapters can plug into the same core.
"""

from sqlnocturne.dialects.base import Dialect, FeatureSet
from sqlnocturne.dialects.registry import get_dialect, register_dialect
from sqlnocturne.dialects.sqlite import SQLiteDialect

__all__ = ["Dialect", "FeatureSet", "SQLiteDialect", "get_dialect", "register_dialect"]
