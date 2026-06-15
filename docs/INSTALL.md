# SQLNocturne Install

## Requirements

- Python 3.10+
- Git

## Clone And Install

```bash
git clone https://github.com/emrebe06/sqlnocturne.git
cd sqlnocturne
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\activate
pip install -e .
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -e .
```

Optional drivers:

```bash
pip install -e ".[postgresql]"
pip install -e ".[mysql]"
```

## Smoke Test

```python
from sqlnocturne import Database

db = Database("sqlite:///shop")
db.sql("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)").run()
db.insert("users", {"name": "Emre"}).run()
print(db.table("users").select("id", "name").limit(10).result().to_json(indent=2))
db.close()
```

`sqlite:///shop` creates or uses:

```text
shop.db
```

## CLI Check

```bash
sqlnocturne check --database sqlite:///:memory:
sqlnocturne risk "DELETE FROM users"
```
