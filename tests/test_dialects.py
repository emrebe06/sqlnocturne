from sqlnocturne import Database, get_dialect


def test_sqlite_dialect_shape():
    dialect = get_dialect("sqlite")

    assert dialect.name == "sqlite"
    assert dialect.placeholder == "?"
    assert dialect.quote_identifier("users") == '"users"'
    assert dialect.supports("transactions") is True


def test_future_dialects_registered():
    assert get_dialect("postgresql").name == "postgresql"
    assert get_dialect("mysql").name == "mysql"


def test_database_uses_dialect_for_compile():
    db = Database("sqlite:///:memory:")
    compiled = db.table("users").select("id").where("id", "=", 1).limit(1).compile()

    assert compiled.sql == 'SELECT "id" FROM "users" WHERE "id" = ? LIMIT ?'
    assert compiled.params == [1, 1]
    db.close()
