from pathlib import Path

from sqlnocturne import Database
from sqlnocturne.migrations import MigrationManager


def test_migration_folder_creation(tmp_path):
    root = tmp_path / "migrations"

    result = MigrationManager(root=root).init()

    assert result.ok is True
    assert (root / "versions").exists()
    assert (root / "snapshot.json").exists()


def test_apply_simple_migration(tmp_path):
    root = tmp_path / "migrations"
    manager = MigrationManager(root=root)
    manager.init()
    path = Path(manager.revision("create users").data["path"])
    path.write_text(
        """
def up(db):
    db.sql("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)").run()

def down(db):
    db.sql("DROP TABLE IF EXISTS users").run()
""",
        encoding="utf-8",
    )

    with Database("sqlite:///:memory:") as db:
        result = MigrationManager(db, root=root).migrate()
        tables = db.tables()

        assert result.ok is True
        assert "users" in tables.data
