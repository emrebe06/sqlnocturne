# SQLNocturne Architecture

SQLNocturne is designed as a standalone data runtime. It can be used under any
Python application, including API servers, CLI tools, local desktop tools, small
ecommerce backends, automation scripts, or future QuickAPI applications.

The first version is intentionally Python-first. Native code is optional and
works as a lower worker layer when present. The V0.1 runtime must still run
without Rust, C, C++, ASM, or external database drivers.

V0.1 is SQLite-first, not SQLite-only. SQLite is the first adapter because it is
available in Python's standard library. The architecture must still protect the
future path for PostgreSQL, MySQL, DuckDB, and other engines.

## Product Boundary

SQLNocturne owns:

- database connection lifecycle
- query builder
- raw SQL execution
- safety inspection
- JSON-first result objects
- migrations
- schema convenience helpers
- CLI workflow

SQLNocturne does not own:

- HTTP request handling
- web routing
- authentication
- template rendering
- full ORM object identity maps
- model decorators
- hidden database magic

This boundary matters. The package should remain useful even when no API
framework is installed.

## Runtime Flow

```text
User code
  -> Database
  -> Query or Raw SQL
  -> Compiler
  -> Dialect
  -> SafetyGuard
  -> Adapter
  -> Result
```

Every public operation should either return a `Result` or raise a controlled
setup/programmer error. The normal query path should not explode into raw
sqlite exceptions.

## Database

`Database` is the primary facade.

Responsibilities:

- parse configuration
- create adapter
- expose table/query helpers
- expose raw SQL helper
- expose transaction, batch, and schema helpers
- hold the safety guard
- close connections

`Database` should stay readable. If a feature needs many lines, move it to a
dedicated module and expose only a small method on `Database`.

## Query Builder

The query builder is fluent but not magical.

```python
db.table("users").select("id", "name").where("active", "=", True).limit(20)
```

The compiler must produce:

- SQL text
- parameter list
- query type
- optional table name

Values must never be interpolated directly into SQL. They must go into the
parameter list.

## Safety Guard

The safety guard is a heuristic guardrail.

It should catch:

- full-table `DELETE`
- full-table `UPDATE`
- stacked statements
- dangerous schema operations in strict modes
- obvious injection patterns
- broad reads that deserve warnings

It is not a complete parser and should not claim to be one. Its job is to stop
obvious foot-guns and provide metadata.

## Result Object

Result shape is the product language.

```json
{
  "ok": true,
  "code": "OK",
  "message": "Rows selected",
  "data": [],
  "meta": {},
  "error": null
}
```

Keep this stable. Integrations can be built around this shape.

## Adapter Layer

V0.1 ships with a working SQLite adapter only.

The adapter boundary now recognizes SQLite, PostgreSQL, and MySQL. SQLite works
with the standard library. PostgreSQL/MySQL adapters are optional DB-API
adapters: if the driver exists they can connect; if the driver is missing they
raise a controlled adapter error.

Future adapters can follow the same small contract:

- connect
- close
- execute
- fetch_all
- fetch_one
- list_tables
- describe_table

Do not add external drivers until the core behavior is stable.

## Dialect Layer

Adapters move bytes to and from a database. Dialects explain how SQL should be
written for that database.

Dialect responsibilities:

- identifier quoting
- placeholder style
- limit/offset syntax
- feature flags
- create-table prefix

Current dialects:

- `sqlite`: working dialect for the current adapter
- `postgresql`: optional DB-API adapter, `%s` placeholders, standard quoting
- `mysql`: optional DB-API adapter, `%s` placeholders, backtick quoting

This split keeps the compiler from hardcoding SQLite forever.

## Repository Layer

The repository layer is optional. It gives small applications a convenient
table-oriented wrapper, but it must not become a full ORM.

Allowed repository behavior:

- create row
- update by primary key
- delete by primary key
- get by primary key
- page rows
- cursor rows
- simple filters

Avoid repository behavior like:

- object identity maps
- lazy relationship loading
- model decorators
- lifecycle hooks hidden from the user

SQLNocturne should keep SQL visible and understandable.

## Import Export Layer

Import/export is JSON-first. It is meant for small tools, backups, examples,
admin workflows, and local product experiments.

This layer should remain adapter-neutral. It should not use SQLite-specific
features. It should call public `Database`, `Batch`, and `Result` APIs.

## Health Layer

Health checks give applications a quick way to inspect:

- Python runtime
- SQLNocturne version
- adapter capability
- dialect capability
- database connectivity
- table listing

The health layer is intentionally plain JSON so web frameworks, CLIs, or
monitoring scripts can consume it easily.

## Migrations

Migrations are Python files with:

```python
def up(db):
    ...

def down(db):
    ...
```

This keeps the migration system simple and dependency-free.

The tracking table is:

```sql
sqlnocturne_migrations
```

The migration runner should stay conservative. It should apply pending files in
filename order and record applied versions.

## CLI

The CLI uses `argparse`.

Core commands:

- check
- init
- revision
- migrate
- status
- rollback
- snapshot
- risk
- tables
- describe
- shell
- bench

The CLI should print JSON for result-oriented commands so it can be scripted.

## Transactions

Transactions are explicit. The package should not hide transaction boundaries
from users.

```python
db.transaction("name").run(callback)
```

or:

```python
with db.transaction("name"):
    ...
```

## Batch

Batch execution is a convenience layer. It should inspect every item before
running the first item. Transactional mode is the default because partial writes
are surprising.

## Schema Builder

Schema builder is intentionally small. It is not a full migration diff engine.
It exists to make examples and small apps easier.

## Native Roadmap

Native code should remain optional.

Current native direction:

- C owns the stable ABI, allocator, and low-level SQL scan report.
- C++ owns plan preparation, future plan cache, and native JSON helpers.
- Rust owns tokenizer/risk-policy experiments.
- ASM is limited to tiny platform probes such as CPU cycle timing.

Rust can later own:

- tokenization
- risk scoring
- policy matching

C++ can later own:

- query plan cache
- JSON result writer
- parameter binding helpers

C ABI can later provide:

- stable boundary between Python and native modules
- version checks
- small result structs

The rule is simple: Python is the developer-facing desk. Native code is the
worker floor. If native code is unavailable, Python must still return safe,
controlled `Result` objects.

## Development Rules

- No heavy runtime dependencies.
- Keep public API small.
- Prefer explicit methods over decorators.
- Keep SQL visible.
- Never pretend heuristics are perfect security.
- Keep QuickAPI integration optional.
- Keep result shape stable.

## Future Package Family

SQLNocturne can become part of a broader ecosystem, but it should not become a
hidden submodule of another product. The clean path is:

- SQLNocturne for data access
- QuickAPI for API/runtime
- future packages for auth, queues, or admin panels

Each package should be able to stand alone.
