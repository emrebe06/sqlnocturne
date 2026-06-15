"""Migration commands."""

from sqlnocturne import Database
from sqlnocturne.migrations.manager import MigrationManager


def handle_revision(args) -> int:
    result = MigrationManager(root=args.path).revision(args.name)
    print(result.to_json(indent=2))
    return 0 if result.ok else 1


def handle_migrate(args) -> int:
    with Database(args.database, safe_mode=args.safe_mode, migrations_path=args.path) as db:
        result = MigrationManager(db, root=args.path).migrate()
    print(result.to_json(indent=2))
    return 0 if result.ok else 1


def handle_status(args) -> int:
    with Database(args.database, safe_mode=args.safe_mode, migrations_path=args.path) as db:
        result = MigrationManager(db, root=args.path).status()
    print(result.to_json(indent=2))
    return 0 if result.ok else 1


def handle_rollback(args) -> int:
    with Database(args.database, safe_mode=args.safe_mode, migrations_path=args.path) as db:
        result = MigrationManager(db, root=args.path).rollback_last()
    print(result.to_json(indent=2))
    return 0 if result.ok else 1


def handle_snapshot(args) -> int:
    with Database(args.database, safe_mode=args.safe_mode, migrations_path=args.path) as db:
        result = MigrationManager(db, root=args.path).snapshot()
    print(result.to_json(indent=2))
    return 0 if result.ok else 1
