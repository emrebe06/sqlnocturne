"""High-level migration manager."""

from __future__ import annotations

from pathlib import Path

from sqlnocturne.core.result import Result
from sqlnocturne.migrations.revision import create_revision
from sqlnocturne.migrations.runner import MigrationRunner
from sqlnocturne.migrations.snapshot import capture_sqlite_schema, save_snapshot


class MigrationManager:
    def __init__(self, db=None, root: str | Path = "nocturne_migrations"):
        self.db = db
        self.root = Path(root)
        self.versions = self.root / "versions"

    def init(self) -> Result:
        self.versions.mkdir(parents=True, exist_ok=True)
        save_snapshot(self.root, {"tables": {}, "notes": ["Initialized by SQLNocturne"]})
        return Result.success(
            {
                "root": str(self.root),
                "versions": str(self.versions),
                "snapshot": str(self.root / "snapshot.json"),
            },
            message="Migration folder initialized",
        )

    def revision(self, name: str) -> Result:
        path = create_revision(self.root, name)
        return Result.success({"path": str(path)}, message="Migration revision created")

    def runner(self) -> MigrationRunner:
        if self.db is None:
            raise RuntimeError("MigrationManager requires db for runner operations")
        return MigrationRunner(self.db, self.root)

    def migrate(self) -> Result:
        return self.runner().migrate()

    def status(self) -> Result:
        return self.runner().status()

    def rollback_last(self) -> Result:
        return self.runner().rollback_last()

    def snapshot(self) -> Result:
        if self.db is None:
            return Result.error_result(
                code="NO_DATABASE",
                message="Snapshot requires a database",
                error_type="migration_error",
            )
        data = {"tables": capture_sqlite_schema(self.db)}
        path = save_snapshot(self.root, data)
        return Result.success({"path": str(path), "tables": data["tables"]}, message="Snapshot written")
