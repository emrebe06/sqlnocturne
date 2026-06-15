from sqlnocturne import Database


def test_memory_database_insert_select():
    with Database("sqlite:///:memory:") as db:
        db.sql("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)").run()
        insert = db.insert("users", {"name": "Emre"}).run()
        rows = db.table("users").select("id", "name").limit(10).result()

        assert insert.ok is True
        assert rows.ok is True
        assert rows.data == [{"id": 1, "name": "Emre"}]


def test_fetch_one():
    with Database("sqlite:///:memory:") as db:
        db.sql("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)").run()
        db.insert("users", {"id": 1, "name": "Ada"}).run()
        row = db.sql("SELECT id, name FROM users WHERE id = ?", [1]).result(fetch="one")

        assert row.ok is True
        assert row.data == {"id": 1, "name": "Ada"}
