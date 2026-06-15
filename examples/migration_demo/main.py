from pathlib import Path

from sqlnocturne import Database
from sqlnocturne.migrations import MigrationManager


def main():
    root = Path("demo_migrations")
    manager = MigrationManager(root=root)
    print(manager.init().to_json(indent=2))
    revision = manager.revision("create users")
    print(revision.to_json(indent=2))

    print("Edit the generated migration file, then run:")
    print("  sqlnocturne migrate --database sqlite:///demo.db --path demo_migrations")

    with Database("sqlite:///demo.db") as db:
        print(MigrationManager(db, root=root).status().to_json(indent=2))


if __name__ == "__main__":
    main()
