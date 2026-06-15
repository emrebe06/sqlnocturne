"""Configuration primitives for SQLNocturne."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qsl, urlparse


SAFE_MODES = {"off", "normal", "strict", "paranoid"}
SQLITE_SUFFIXES = {".db", ".sqlite", ".sqlite3"}
SCHEME_ALIASES = {
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "mysql": "mysql",
    "mariadb": "mysql",
    "sqlite": "sqlite",
}


@dataclass(slots=True)
class DatabaseConfig:
    """Runtime configuration for a database connection."""

    uri: str
    safe_mode: str = "strict"
    timeout: float = 30.0
    migrations_path: str = "nocturne_migrations"
    echo: bool = False
    row_limit_warning: int = 0
    adapter_name: str = "sqlite"
    dialect_name: str = "sqlite"

    def __post_init__(self) -> None:
        if self.safe_mode not in SAFE_MODES:
            allowed = ", ".join(sorted(SAFE_MODES))
            raise ValueError(f"safe_mode must be one of: {allowed}")
        if not self.uri:
            raise ValueError("Database uri cannot be empty")
        if self.timeout <= 0:
            raise ValueError("timeout must be greater than zero")

    @property
    def is_memory(self) -> bool:
        return self.uri == "sqlite:///:memory:"

    @property
    def sqlite_path(self) -> str:
        if self.uri == "sqlite:///:memory:":
            return ":memory:"
        prefix = "sqlite:///"
        if not self.uri.startswith(prefix):
            raise ValueError("sqlite_path is only available for sqlite:/// URIs")
        path = self.uri[len(prefix):]
        if path == ":memory:":
            return ":memory:"
        expanded = Path(path).expanduser()
        if expanded.suffix.lower() not in SQLITE_SUFFIXES:
            expanded = expanded.with_suffix(".db")
        return str(expanded)

    @property
    def scheme(self) -> str:
        if "://" not in self.uri:
            return "sqlite"
        raw = self.uri.split("://", 1)[0].lower()
        return SCHEME_ALIASES.get(raw, raw)

    @property
    def parsed(self):
        return urlparse(self.uri)

    @property
    def options(self) -> dict[str, str]:
        return dict(parse_qsl(self.parsed.query, keep_blank_values=True))

    @property
    def database_name(self) -> str:
        if self.scheme == "sqlite":
            path = self.sqlite_path
            return ":memory:" if path == ":memory:" else Path(path).name
        parsed = self.parsed
        return parsed.path.lstrip("/") or ""

    @property
    def migrations_dir(self) -> Path:
        return Path(self.migrations_path)

    def to_dict(self) -> dict:
        return {
            "uri": self.uri,
            "safe_mode": self.safe_mode,
            "timeout": self.timeout,
            "migrations_path": self.migrations_path,
            "echo": self.echo,
            "row_limit_warning": self.row_limit_warning,
            "adapter_name": self.adapter_name,
            "dialect_name": self.dialect_name,
            "scheme": self.scheme,
            "database_name": self.database_name,
            "options": self.options,
        }
