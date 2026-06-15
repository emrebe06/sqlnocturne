"""Migration runner."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
from types import ModuleType

from sqlnocturne.core.errors import MigrationError
from sqlnocturne.core.result import Result


TRACKING_SQL = """
CREATE TABLE IF NOT EXISTS sqlnocturne_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL
)
"""


@dataclass(slots=True)
class MigrationFile:
    version: str
    name: str
    path: Path

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "name": self.name,
            "path": str(self.path),
        }


def applied_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class MigrationRunner:
    def __init__(self, db, root: str | Path = "nocturne_migrations"):
        self.db = db
        self.root = Path(root)
        self.versions = self.root / "versions"

    def ensure_tracking_table(self) -> Result:
        return self.db.sql(TRACKING_SQL).run()

    def discover(self) -> list[MigrationFile]:
        if not self.versions.exists():
            return []
        files: list[MigrationFile] = []
        for path in sorted(self.versions.glob("*.py")):
            stem = path.stem
            if "_" in stem:
                version, name = stem.split("_", 1)
            else:
                version, name = stem, stem
            files.append(MigrationFile(version=stem, name=name, path=path))
        return files

    def applied(self) -> list[str]:
        self.ensure_tracking_table()
        result = self.db.sql("SELECT version FROM sqlnocturne_migrations ORDER BY version").result(fetch="all")
        if not result.ok:
            return []
        return [row["version"] for row in result.data]

    def status(self) -> Result:
        files = self.discover()
        applied = set(self.applied())
        rows = []
        for migration in files:
            rows.append(
                {
                    **migration.to_dict(),
                    "applied": migration.version in applied,
                }
            )
        return Result.success(
            rows,
            message="Migration status",
            meta={
                "rows": len(rows),
                "pending": len([row for row in rows if not row["applied"]]),
            },
        )

    def migrate(self) -> Result:
        self.ensure_tracking_table()
        applied = set(self.applied())
        applied_rows = []
        for migration in self.discover():
            if migration.version in applied:
                continue
            module = self._load_module(migration)
            up = getattr(module, "up", None)
            if not callable(up):
                return Result.error_result(
                    code="BAD_MIGRATION",
                    message=f"Migration {migration.path.name} has no callable up(db)",
                    error_type="migration_error",
                )
            try:
                up(self.db)
                record = self.db.sql(
                    "INSERT INTO sqlnocturne_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                    [migration.version, migration.name, applied_now()],
                ).run()
                if not record.ok:
                    return record
                applied_rows.append(migration.to_dict())
            except Exception as exc:
                return Result.error_result(
                    code="MIGRATION_FAILED",
                    message=f"Migration failed: {migration.version}",
                    detail=str(exc),
                    error_type="migration_error",
                    meta={"migration": migration.to_dict()},
                )
        return Result.success(
            applied_rows,
            message="Migrations applied",
            meta={"rows": len(applied_rows), "pending": 0},
        )

    def rollback_last(self) -> Result:
        self.ensure_tracking_table()
        row = self.db.sql("SELECT version, name FROM sqlnocturne_migrations ORDER BY id DESC LIMIT 1").one()
        if not row:
            return Result.success(None, message="No migration to rollback", meta={"rows": 0})
        migration = next((item for item in self.discover() if item.version == row["version"]), None)
        if migration is None:
            return Result.error_result(
                code="MIGRATION_FILE_MISSING",
                message=f"Migration file missing for {row['version']}",
                error_type="migration_error",
            )
        module = self._load_module(migration)
        down = getattr(module, "down", None)
        if not callable(down):
            return Result.error_result(
                code="BAD_MIGRATION",
                message=f"Migration {migration.path.name} has no callable down(db)",
                error_type="migration_error",
            )
        try:
            down(self.db)
            self.db.sql("DELETE FROM sqlnocturne_migrations WHERE version = ?", [migration.version]).run()
            return Result.success(migration.to_dict(), message="Migration rolled back", meta={"rows": 1})
        except Exception as exc:
            return Result.error_result(
                code="ROLLBACK_FAILED",
                message=f"Rollback failed: {migration.version}",
                detail=str(exc),
                error_type="migration_error",
            )

    def _load_module(self, migration: MigrationFile) -> ModuleType:
        spec = importlib.util.spec_from_file_location(f"sqlnocturne_migration_{migration.version}", migration.path)
        if spec is None or spec.loader is None:
            raise MigrationError("Could not load migration", detail=str(migration.path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
