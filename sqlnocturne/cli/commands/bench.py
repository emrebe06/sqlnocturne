"""Tiny benchmark command."""

from time import perf_counter

from sqlnocturne import Database


def handle_bench(args) -> int:
    count = args.count
    with Database("sqlite:///:memory:", safe_mode="normal") as db:
        db.sql("CREATE TABLE bench_items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)").run()
        start = perf_counter()
        for index in range(count):
            db.insert("bench_items", {"name": f"item-{index}"}).run()
        insert_ms = (perf_counter() - start) * 1000
        start = perf_counter()
        rows = db.table("bench_items").select("id", "name").limit(count).all()
        select_ms = (perf_counter() - start) * 1000
    print(f"inserts: {count} in {insert_ms:.2f}ms")
    print(f"select: {len(rows)} rows in {select_ms:.2f}ms")
    return 0
