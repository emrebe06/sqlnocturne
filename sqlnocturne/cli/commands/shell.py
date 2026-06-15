"""Interactive shell."""

from sqlnocturne import Database
from sqlnocturne.safety.guard import SafetyGuard


HELP = """Commands:
  help                         show this text
  exit                         leave shell
  risk <sql>                   inspect SQL without running it
  sql <sql>                    execute SQL through SQLNocturne
  tables                       list tables
"""


def handle_shell(args) -> int:
    print("SQLNocturne shell. Type 'help' or 'exit'.")
    guard = SafetyGuard(args.safe_mode)
    db = Database(args.database, safe_mode=args.safe_mode)
    try:
        while True:
            try:
                line = input("nocturne> ").strip()
            except EOFError:
                print()
                break
            if not line:
                continue
            if line in {"exit", "quit", "\\q"}:
                break
            if line == "help":
                print(HELP)
                continue
            if line == "tables":
                print(db.tables().to_json(indent=2))
                continue
            if line.startswith("risk "):
                import json

                print(json.dumps(guard.inspect(line[5:].strip()), indent=2, ensure_ascii=False))
                continue
            if line.startswith("sql "):
                result = db.sql(line[4:].strip()).result()
                print(result.to_json(indent=2))
                continue
            print("Unknown command. Type 'help'.")
    finally:
        db.close()
    return 0
