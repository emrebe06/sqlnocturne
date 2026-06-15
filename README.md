# SQLNocturne

**No heavy ORM. No blind SQL. No hidden magic.**

SQLNocturne is a safety-first, JSON-first SQL runtime for Python. It gives
developers clear database access, guarded query execution, standard result
objects, SQLite/PostgreSQL/MySQL adapter boundaries, and an optional native
C/C++/Rust/ASM worker layer for SQL safety and runtime acceleration.

SQLNocturne is an independent product. It can integrate with API frameworks
later, but it does not depend on QuickAPI, FastAPI, Flask, Django, SQLAlchemy,
Alembic, Pydantic, Click, Typer, or Rich.

V0.1 is SQLite-first, not SQLite-only. SQLite is the first working adapter
because it ships with Python, but the core already has adapter and dialect
boundaries for future PostgreSQL, MySQL, DuckDB, or other database backends.

## Ecosystem

SQLNocturne is the data runtime in a small native-first Python ecosystem:

- [QuickAPI](https://github.com/emrebe06/QuickAPI): JSON-first Python API runtime.
- [Katmer](https://github.com/emrebe06/katmer): native C ABI layered execution core.

SQLNocturne can run alone. In the ecosystem, it provides guarded database access, JSON result objects, migrations, CLI workflows, and optional native SQL safety checks.

## Keywords

Python SQL runtime, safe SQL query builder, SQLite Python runtime, PostgreSQL adapter Python, MySQL adapter Python, SQL injection guard, JSON-first database library, lightweight ORM alternative, SQLAlchemy alternative, native SQL guard, C ABI database runtime, Docker database tooling, Kubernetes database runtime.

## What It Is

- A small Python SQL runtime.
- A guarded SQLite V0.1 database layer.
- A dialect/adapter architecture that can grow beyond SQLite.
- A JSON-first result model.
- A query builder that compiles parameterized SQL.
- A safe raw SQL runner with strict-mode checks.
- A simple migration system.
- A CLI built with standard library `argparse`.
- Optional native safety/runtime layer with C, C++, Rust, and ASM-ready pieces.

## What It Is Not

- SQLNocturne is not a SQLAlchemy clone.
- SQLNocturne is not a full ORM.
- SQLNocturne is not a database engine.
- SQLNocturne is not trying to hide SQL completely.

## Installation

For local development:

```bash
pip install -e .
```

Optional network database drivers:

```bash
pip install -e ".[postgresql]"
pip install -e ".[mysql]"
```

The package import name is:

```python
import sqlnocturne
```

## Quick Start

```python
from sqlnocturne import Database

db = Database("sqlite:///app.db", safe_mode="strict")

db.sql("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
)
""").run()

db.insert("users", {
    "name": "Emre",
    "email": "emre@example.com",
}).run()

result = (
    db.table("users")
    .select("id", "name", "email")
    .where("active", "=", 1)
    .limit(20)
    .result()
)

print(result.to_json(indent=2))
```

SQLite convenience: `sqlite:///shop` creates/uses `shop.db`. Existing suffixes
such as `.db`, `.sqlite`, and `.sqlite3` are preserved.

Network database URIs are recognized too:

```python
Database("postgresql://user:pass@localhost:5432/app")
Database("mysql://user:pass@localhost:3306/app")
```

PostgreSQL requires an optional `psycopg`/`psycopg2` driver. MySQL requires
`pymysql` or `mysqlclient`. If a driver is missing, SQLNocturne returns a
controlled adapter error instead of failing unclearly.

## Result Shape

Every public operation returns a stable `Result` object when using `.result()`
or `.run()`.

```json
{
  "ok": true,
  "code": "OK",
  "message": "Rows selected",
  "data": [],
  "meta": {
    "engine": "sqlnocturne",
    "adapter": "sqlite",
    "rows": 0,
    "time_ms": 1.23,
    "risk_score": 0.02
  },
  "error": null
}
```

## Query Builder

```python
users = db.table("users")

rows = (
    users
    .select("id", "name", "email")
    .where("active", "=", True)
    .order("id", "DESC")
    .limit(20)
    .all()
)
```

Compiled SQL is parameterized:

```sql
SELECT "id", "name", "email" FROM "users" WHERE "active" = ? ORDER BY "id" DESC LIMIT ?
```

Parameters:

```python
[True, 20]
```

## Insert

```python
result = db.insert("users", {
    "name": "Ada",
    "email": "ada@example.com",
}).run()
```

## Update

```python
result = (
    db.update("users")
    .set({"name": "Ada Lovelace"})
    .where("id", "=", 1)
    .run()
)
```

Strict mode blocks update without `WHERE`.

## Delete

```python
result = db.delete("users").where("id", "=", 1).run()
```

Strict mode blocks delete without `WHERE`.

## Transactions

```python
def create_user(db):
    db.insert("users", {"name": "Emre", "email": "emre@example.com"}).run()
    db.insert("audit_logs", {"event": "user_created"}).run()
    return {"created": True}

result = db.transaction("create_user").run(create_user)
```

You can also use an explicit context manager:

```python
with db.transaction("manual") as tx:
    db.insert("users", {"name": "Ada"}).run()
```

## Batch Execution

```python
result = (
    db.batch(transactional=True)
    .insert("users", {"name": "Ada", "email": "ada@example.com"})
    .insert("users", {"name": "Linus", "email": "linus@example.com"})
    .run()
)
```

The batch is inspected by the same safety guard before execution.

## Schema Builder

```python
schema = db.schema()

schema.table("products") \
    .id() \
    .text("name", nullable=False) \
    .real("price", nullable=False, default=0) \
    .integer("stock", nullable=False, default=0) \
    .index("idx_products_name", ["name"])

result = schema.create_all(db)
```

Schema builder is intentionally small. It is a convenience layer, not a full
migration diff engine.

## Repository Helper

Repositories are optional table wrappers. They are not ORM models.

```python
products = db.repository("products", primary_key="id", default_limit=25)

products.create({"name": "Keyboard", "price": 99.90})
products.update(1, {"price": 89.90})
page = products.page(page=1, per_page=20)
item = products.get(1)
```

This is useful for small applications that want clean data access without model
magic.

## Pagination

```python
result = db.repository("products").page(page=2, per_page=20)

print(result.data["items"])
print(result.data["pagination"])
```

Cursor style pagination is also available through repository helpers.

## Import And Export

```python
rows = db.table("products").select("id", "name").limit(100).result()

db.export_json(rows, "products.json")
db.import_json("products_archive", "products.json")
```

The helpers use JSON and JSON Lines style primitives and keep returning
SQLNocturne `Result` objects.

## Health Checks

```python
result = db.health()
print(result.to_json(indent=2))
```

Health output includes adapter capabilities, active dialect details, a simple
`SELECT 1`, and table inspection.

## Safe Raw SQL

```python
result = db.sql("SELECT * FROM users WHERE id = ?", [1]).result(fetch="one")
```

Raw SQL goes through the same safety guard.

```python
blocked = db.sql("DELETE FROM users").run()
print(blocked.ok)      # False
print(blocked.code)    # DELETE_WITHOUT_WHERE
```

## Safety Guard

```python
from sqlnocturne.safety import SafetyGuard

guard = SafetyGuard("strict")
print(guard.inspect("DELETE FROM users"))
```

V0.1 checks:

- `DELETE` without `WHERE`
- `UPDATE` without `WHERE`
- multiple SQL statements
- dangerous schema operations in strict mode
- `SELECT *` without `LIMIT` warning
- obvious injection signals such as `OR 1=1`, comments, and `UNION SELECT`
- ML-style local feature guard for suspicious SQL shape scoring
- optional native C guard when `sqlnocturne_native` is available

This is a guardrail, not a perfect SQL parser.

## Native Layer

Python remains the public API. Native code is optional and used as a worker
layer when present.

```bash
cmake -S sqlnocturne/native -B native-build
cmake --build native-build --config Release
```

Native pieces:

- C ABI: `nocturne_validate_query_json`, `nocturne_runtime_json`
- C allocator: platform-aware aligned allocation/free
- ASM: CPU cycle backend for x86/x64 and ARM64 where available
- C++: plan preparation and future cache/JSON writer work
- Rust: tokenizer/risk-policy direction

If the native library is missing, SQLNocturne keeps working with the Python
guard and ML-style local guard.

## Docker And Kubernetes

```bash
docker build -t sqlnocturne:local .
docker compose up --build
```

Kubernetes manifests live in `deploy/kubernetes`:

```bash
kubectl apply -f deploy/kubernetes/configmap.yaml
kubectl apply -f deploy/kubernetes/pvc.yaml
kubectl apply -f deploy/kubernetes/deployment.yaml
```

Set `SQLNOCTURNE_DATABASE_URL` or `SQLNOCTURNE_DATABASE` for containerized
deployments.

## Migrations

Initialize:

```bash
sqlnocturne init
```

Create revision:

```bash
sqlnocturne revision "create users"
```

Apply migrations:

```bash
sqlnocturne migrate --database sqlite:///app.db
```

Status:

```bash
sqlnocturne status --database sqlite:///app.db
```

Migration files look like:

```python
def up(db):
    db.sql("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """).run()

def down(db):
    db.sql("DROP TABLE IF EXISTS users").run()
```

## CLI

```bash
sqlnocturne check
sqlnocturne init
sqlnocturne revision "create products"
sqlnocturne migrate --database sqlite:///shop.db
sqlnocturne status --database sqlite:///shop.db
sqlnocturne risk "DELETE FROM users"
sqlnocturne tables --database sqlite:///shop.db
sqlnocturne describe products --database sqlite:///shop.db
sqlnocturne shell --database sqlite:///shop.db
sqlnocturne bench --count 1000
```

## Optional API Integration Later

SQLNocturne stays separate. A web app can still consume its plain result shape:

```python
from sqlnocturne import Database

db = Database("sqlite:///shop.db")

def products_handler():
    result = db.table("products").select("id", "name").limit(20).result()
    return result.to_dict()
```

There is also a tiny helper in `sqlnocturne.integrations.quickapi`, but it does
not import QuickAPI and does not make QuickAPI a dependency.

## Architecture

```text
sqlnocturne/
  core/          Database, Query, Result, compiler
  adapters/      SQLite adapter
  dialects/      SQL dialect contracts and future backend shapes
  safety/        guard, tokenizer, rules, risk, injection checks
  migrations/    init, revision, runner, snapshot
  cli/           argparse command line interface
  integrations/  optional helpers with no framework dependency
  native/        optional C/C++/Rust/ASM safety/runtime worker layer
```

Python is the product layer for V0.1. Native code is a future acceleration
direction, not a requirement.

## Adapter And Dialect Direction

SQLite is the first supported runtime adapter:

```python
db = Database("sqlite:///app.db")
```

Future adapters can register themselves:

```python
from sqlnocturne import register_adapter, register_dialect

register_adapter("postgresql", PostgreSQLAdapter)
register_dialect(PostgreSQLDialect())
```

The compiler asks the active dialect how to quote identifiers, how placeholders
look, and what features are available. That keeps SQLNocturne from becoming a
SQLite-only wrapper.

## Roadmap

- Better SQL tokenizer and dialect awareness
- Stronger native risk scanner
- C++ plan cache integration
- Native JSON result writer integration
- PostgreSQL adapter after SQLite stabilizes
- Policy engine for tenant/role checks
- Schema inspection and migration diffing

## License

Apache-2.0. Copyright (c) 2026 Emre B.
