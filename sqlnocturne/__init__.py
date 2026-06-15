"""SQLNocturne public package API.

SQLNocturne is intentionally small at the top level. Most users should need
only ``Database`` and the standard ``Result`` shape.
"""

from sqlnocturne.core.database import Database
from sqlnocturne.core.errors import (
    AdapterError,
    ConnectionError,
    MigrationError,
    NocturneError,
    QueryError,
    SafetyError,
)
from sqlnocturne.core.result import Result
from sqlnocturne.core.repository import Repository
from sqlnocturne.core.schema import ColumnSchema, IndexSchema, SchemaBuilder, TableSchema
from sqlnocturne.core.connection import register_adapter
from sqlnocturne.dialects import get_dialect, register_dialect

__version__ = "0.1.0"

__all__ = [
    "AdapterError",
    "ColumnSchema",
    "ConnectionError",
    "Database",
    "IndexSchema",
    "MigrationError",
    "NocturneError",
    "QueryError",
    "Result",
    "Repository",
    "SchemaBuilder",
    "SafetyError",
    "TableSchema",
    "get_dialect",
    "register_adapter",
    "register_dialect",
]
