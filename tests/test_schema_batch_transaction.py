from sqlnocturne import Database


def test_schema_builder_create_all():
    with Database("sqlite:///:memory:") as db:
        schema = db.schema()
        schema.table("products").id().text("name", nullable=False).real("price", nullable=False, default=0)

        result = schema.create_all(db)
        tables = db.tables()

        assert result.ok is True
        assert "products" in tables.data


def test_batch_insert():
    with Database("sqlite:///:memory:") as db:
        db.sql("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)").run()
        result = (
            db.batch(transactional=True)
            .insert("users", {"name": "Emre"})
            .insert("users", {"name": "Ada"})
            .run()
        )
        rows = db.table("users").select("id", "name").limit(10).all()

        assert result.ok is True
        assert len(rows) == 2


def test_transaction_callback():
    with Database("sqlite:///:memory:") as db:
        db.sql("CREATE TABLE logs (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT)").run()

        def work(inner):
            inner.insert("logs", {"message": "hello"}).run()
            return {"done": True}

        result = db.transaction("logs").run(work)

        assert result.ok is True
        assert db.table("logs").count() == 1
