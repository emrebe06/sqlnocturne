"""Transaction helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from sqlnocturne.core.result import Result


@dataclass(slots=True)
class TransactionEvent:
    action: str
    ok: bool
    message: str

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "ok": self.ok,
            "message": self.message,
        }


class Transaction:
    """Context manager for explicit SQLite transactions."""

    def __init__(self, db, *, name: str | None = None):
        self.db = db
        self.name = name or "transaction"
        self.events: list[TransactionEvent] = []
        self.active = False

    def begin(self) -> "Transaction":
        if self.active:
            raise RuntimeError("Transaction is already active")
        self.db.adapter.begin()
        self.active = True
        self.events.append(TransactionEvent("begin", True, "Transaction started"))
        return self

    def commit(self) -> Result:
        if not self.active:
            return Result.error_result(
                code="TRANSACTION_NOT_ACTIVE",
                message="Cannot commit inactive transaction",
                error_type="transaction_error",
            )
        try:
            self.db.adapter.commit()
            self.active = False
            self.events.append(TransactionEvent("commit", True, "Transaction committed"))
            return Result.success(
                [event.to_dict() for event in self.events],
                message="Transaction committed",
                meta={"transaction": self.name},
            )
        except Exception as exc:
            return Result.error_result(
                code="TRANSACTION_COMMIT_FAILED",
                message="Transaction commit failed",
                detail=str(exc),
                error_type="transaction_error",
                meta={"transaction": self.name},
            )

    def rollback(self) -> Result:
        if not self.active:
            return Result.success(
                [event.to_dict() for event in self.events],
                message="Transaction already inactive",
                meta={"transaction": self.name},
            )
        try:
            self.db.adapter.rollback()
            self.active = False
            self.events.append(TransactionEvent("rollback", True, "Transaction rolled back"))
            return Result.success(
                [event.to_dict() for event in self.events],
                message="Transaction rolled back",
                meta={"transaction": self.name},
            )
        except Exception as exc:
            return Result.error_result(
                code="TRANSACTION_ROLLBACK_FAILED",
                message="Transaction rollback failed",
                detail=str(exc),
                error_type="transaction_error",
                meta={"transaction": self.name},
            )

    def run(self, callback: Callable[[Any], Any]) -> Result:
        self.begin()
        try:
            value = callback(self.db)
            commit = self.commit()
            if not commit.ok:
                return commit
            return Result.success(
                value,
                message="Transaction callback executed",
                meta={"transaction": self.name, "events": [event.to_dict() for event in self.events]},
            )
        except Exception as exc:
            rollback = self.rollback()
            return Result.error_result(
                code="TRANSACTION_CALLBACK_FAILED",
                message="Transaction callback failed",
                detail=str(exc),
                error_type="transaction_error",
                meta={
                    "transaction": self.name,
                    "rollback_ok": rollback.ok,
                    "events": [event.to_dict() for event in self.events],
                },
            )

    def __enter__(self) -> "Transaction":
        return self.begin()

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is None:
            self.commit()
            return False
        self.rollback()
        return False
