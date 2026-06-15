from sqlnocturne import Database


def test_select_compile():
    db = Database("sqlite:///:memory:")
    compiled = (
        db.table("users")
        .select("id", "name")
        .where("active", "=", True)
        .limit(20)
        .compile()
    )

    assert compiled.sql == 'SELECT "id", "name" FROM "users" WHERE "active" = ? LIMIT ?'
    assert compiled.params == [True, 20]
    db.close()


def test_insert_compile():
    db = Database("sqlite:///:memory:")
    compiled = db.insert("users", {"name": "Emre", "email": "e@example.com"}).compile()

    assert compiled.sql == 'INSERT INTO "users" ("name", "email") VALUES (?, ?)'
    assert compiled.params == ["Emre", "e@example.com"]
    db.close()


def test_update_compile():
    db = Database("sqlite:///:memory:")
    compiled = db.update("users").set({"name": "Emre"}).where("id", "=", 1).compile()

    assert compiled.sql == 'UPDATE "users" SET "name" = ? WHERE "id" = ?'
    assert compiled.params == ["Emre", 1]
    db.close()


def test_delete_compile():
    db = Database("sqlite:///:memory:")
    compiled = db.delete("users").where("id", "=", 1).compile()

    assert compiled.sql == 'DELETE FROM "users" WHERE "id" = ?'
    assert compiled.params == [1]
    db.close()
