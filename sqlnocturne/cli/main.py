"""SQLNocturne CLI."""

from __future__ import annotations

import argparse
import os
import sys

from sqlnocturne.cli.commands.bench import handle_bench
from sqlnocturne.cli.commands.init import handle_init
from sqlnocturne.cli.commands.inspect import handle_check, handle_describe, handle_risk, handle_tables
from sqlnocturne.cli.commands.migrate import (
    handle_migrate,
    handle_revision,
    handle_rollback,
    handle_snapshot,
    handle_status,
)
from sqlnocturne.cli.commands.shell import handle_shell


def default_db() -> str:
    return os.environ.get("SQLNOCTURNE_DATABASE_URL") or os.environ.get("SQLNOCTURNE_DATABASE") or "sqlite:///app.db"


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--database", default=default_db(), help="Database URI, default env SQLNOCTURNE_DATABASE_URL/SQLNOCTURNE_DATABASE or sqlite:///app.db")
    parser.add_argument("--safe-mode", default="strict", choices=["off", "normal", "strict", "paranoid"])
    parser.add_argument("--path", default="nocturne_migrations", help="Migration directory")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sqlnocturne", description="Safety-first, JSON-first SQL runtime.")
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    sub = parser.add_subparsers(dest="command")

    init = sub.add_parser("init", help="Create migration folder")
    init.add_argument("--path", default="nocturne_migrations")
    init.set_defaults(handler=handle_init)

    revision = sub.add_parser("revision", help="Create migration revision")
    revision.add_argument("name")
    revision.add_argument("--path", default="nocturne_migrations")
    revision.set_defaults(handler=handle_revision)

    migrate = sub.add_parser("migrate", help="Apply pending migrations")
    add_common(migrate)
    migrate.set_defaults(handler=handle_migrate)

    status = sub.add_parser("status", help="Show migration status")
    add_common(status)
    status.set_defaults(handler=handle_status)

    rollback = sub.add_parser("rollback", help="Rollback latest migration")
    add_common(rollback)
    rollback.set_defaults(handler=handle_rollback)

    snapshot = sub.add_parser("snapshot", help="Write schema snapshot")
    add_common(snapshot)
    snapshot.set_defaults(handler=handle_snapshot)

    check = sub.add_parser("check", help="Show environment check")
    add_common(check)
    check.set_defaults(handler=handle_check)

    risk = sub.add_parser("risk", help="Inspect SQL risk")
    risk.add_argument("sql")
    risk.add_argument("--safe-mode", default="strict", choices=["off", "normal", "strict", "paranoid"])
    risk.set_defaults(handler=handle_risk)

    tables = sub.add_parser("tables", help="List database tables")
    add_common(tables)
    tables.set_defaults(handler=handle_tables)

    describe = sub.add_parser("describe", help="Describe a table")
    add_common(describe)
    describe.add_argument("table")
    describe.set_defaults(handler=handle_describe)

    shell = sub.add_parser("shell", help="Open interactive shell")
    add_common(shell)
    shell.set_defaults(handler=handle_shell)

    bench = sub.add_parser("bench", help="Run tiny SQLite benchmark")
    bench.add_argument("--count", type=int, default=1000)
    bench.set_defaults(handler=handle_bench)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        from sqlnocturne import __version__

        print(__version__)
        return 0
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 2
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
