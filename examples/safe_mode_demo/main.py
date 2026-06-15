from sqlnocturne import Database


def show(label, result):
    print(f"\n--- {label} ---")
    print(result.to_json(indent=2))


def main():
    with Database("sqlite:///:memory:", safe_mode="strict") as db:
        db.sql("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)").run()
        db.insert("users", {"id": 1, "name": "Emre"}).run()

        show("DELETE without WHERE blocked", db.delete("users").run())
        show("UPDATE without WHERE blocked", db.update("users").set({"name": "Nope"}).run())
        show("Safe update", db.update("users").set({"name": "Emre B."}).where("id", "=", 1).run())
        show("Safe delete", db.delete("users").where("id", "=", 1).run())


if __name__ == "__main__":
    main()
