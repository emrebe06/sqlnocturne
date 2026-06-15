from sqlnocturne import Database


def main():
    with Database("sqlite:///:memory:") as db:
        db.sql(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            )
            """
        ).run()

        db.insert("users", {"name": "Emre", "email": "emre@example.com"}).run()
        db.insert("users", {"name": "Ada", "email": "ada@example.com"}).run()

        result = (
            db.table("users")
            .select("id", "name", "email")
            .where("active", "=", 1)
            .order("id", "ASC")
            .limit(20)
            .result()
        )

        print(result.to_json(indent=2))


if __name__ == "__main__":
    main()
