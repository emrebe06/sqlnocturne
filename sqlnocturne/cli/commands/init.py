"""Init command."""

from sqlnocturne.migrations.manager import MigrationManager


def handle_init(args) -> int:
    result = MigrationManager(root=args.path).init()
    print(result.to_json(indent=2))
    return 0 if result.ok else 1
