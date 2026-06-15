"""Inspection commands."""

from pathlib import Path
import platform

from sqlnocturne import __version__, Database
from sqlnocturne.safety.guard import SafetyGuard


def handle_check(args) -> int:
    data = {
        "sqlnocturne": __version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cwd": str(Path.cwd()),
        "migrations_exists": Path(args.path).exists(),
        "database": args.database,
    }
    for key, value in data.items():
        print(f"{key}: {value}")
    return 0


def handle_risk(args) -> int:
    guard = SafetyGuard(args.safe_mode)
    result = guard.inspect(args.sql)
    import json

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["allowed"] else 2


def handle_tables(args) -> int:
    with Database(args.database, safe_mode=args.safe_mode) as db:
        result = db.tables()
    print(result.to_json(indent=2))
    return 0 if result.ok else 1


def handle_describe(args) -> int:
    with Database(args.database, safe_mode=args.safe_mode) as db:
        result = db.describe(args.table)
    print(result.to_json(indent=2))
    return 0 if result.ok else 1
