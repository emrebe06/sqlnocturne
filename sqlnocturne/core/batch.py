"""Batch execution helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlnocturne.core.result import Result


@dataclass(slots=True)
class BatchItem:
    sql: str
    params: list[Any] = field(default_factory=list)
    label: str | None = None

    def to_dict(self) -> dict:
        return {
            "sql": self.sql,
            "params": list(self.params),
            "label": self.label,
        }


class Batch:
    """Collect and execute multiple SQLNocturne operations."""

    def __init__(self, db, *, transactional: bool = True):
        self.db = db
        self.transactional = transactional
        self.items: list[BatchItem] = []

    def add(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None, *, label: str | None = None) -> "Batch":
        self.items.append(BatchItem(sql, list(params or []), label))
        return self

    def insert(self, table: str, values: dict[str, Any], *, label: str | None = None) -> "Batch":
        compiled = self.db.insert(table, values).compile()
        return self.add(compiled.sql, compiled.params, label=label or f"insert:{table}")

    def update(self, table: str, values: dict[str, Any], where: dict[str, Any], *, label: str | None = None) -> "Batch":
        query = self.db.update(table).set(values)
        for column, value in where.items():
            query.where(column, "=", value)
        compiled = query.compile()
        return self.add(compiled.sql, compiled.params, label=label or f"update:{table}")

    def delete(self, table: str, where: dict[str, Any], *, label: str | None = None) -> "Batch":
        query = self.db.delete(table)
        for column, value in where.items():
            query.where(column, "=", value)
        compiled = query.compile()
        return self.add(compiled.sql, compiled.params, label=label or f"delete:{table}")

    def inspect(self) -> Result:
        rows = []
        allowed = True
        max_risk = 0.0
        for item in self.items:
            inspection = self.db.guard.inspect(item.sql)
            allowed = allowed and inspection["allowed"]
            max_risk = max(max_risk, inspection["risk_score"])
            rows.append(
                {
                    "item": item.to_dict(),
                    "safety": inspection,
                }
            )
        return Result.success(
            rows,
            message="Batch inspected",
            meta={
                "rows": len(rows),
                "allowed": allowed,
                "risk_score": max_risk,
            },
        )

    def run(self) -> Result:
        if not self.items:
            return Result.success([], message="Batch is empty", meta={"rows": 0})
        inspection = self.inspect()
        if not inspection.meta.get("allowed", True):
            return Result.error_result(
                code="BATCH_BLOCKED",
                message="Batch contains blocked SQL",
                detail={"items": inspection.data},
                error_type="safety_error",
                meta={"risk_score": inspection.meta.get("risk_score", 0.0)},
            )

        def execute_items(db):
            executed = []
            for item in self.items:
                result = db.sql(item.sql, item.params).run()
                executed.append(
                    {
                        "label": item.label,
                        "ok": result.ok,
                        "code": result.code,
                        "message": result.message,
                        "meta": result.meta,
                    }
                )
                if not result.ok:
                    raise RuntimeError(f"Batch item failed: {item.label or item.sql}")
            return executed

        if self.transactional:
            return self.db.transaction("batch").run(execute_items)
        try:
            return Result.success(execute_items(self.db), message="Batch executed", meta={"rows": len(self.items)})
        except Exception as exc:
            return Result.error_result(
                code="BATCH_FAILED",
                message="Batch execution failed",
                detail=str(exc),
                error_type="batch_error",
            )
