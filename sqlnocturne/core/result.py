"""Standard JSON-first result object."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any


def _default_meta() -> dict:
    return {
        "engine": "sqlnocturne",
        "adapter": "sqlite",
    }


@dataclass(slots=True)
class Result:
    """A stable success/error object returned by public SQLNocturne operations."""

    ok: bool
    code: str = "OK"
    message: str = "Query executed"
    data: Any = None
    meta: dict = field(default_factory=_default_meta)
    error: dict | None = None

    @classmethod
    def success(
        cls,
        data: Any = None,
        *,
        code: str = "OK",
        message: str = "Query executed",
        meta: dict | None = None,
    ) -> "Result":
        merged = _default_meta()
        if meta:
            merged.update(meta)
        return cls(True, code, message, data, merged, None)

    @classmethod
    def error_result(
        cls,
        *,
        code: str,
        message: str,
        detail: str | dict | None = None,
        error_type: str = "query_error",
        meta: dict | None = None,
        data: Any = None,
    ) -> "Result":
        merged = _default_meta()
        if meta:
            merged.update(meta)
        if isinstance(detail, dict):
            error = dict(detail)
            error.setdefault("type", error_type)
        else:
            error = {
                "type": error_type,
                "detail": detail or message,
            }
        return cls(False, code, message, data, merged, error)

    @classmethod
    def from_safety(cls, inspection: dict) -> "Result":
        return cls.error_result(
            code=inspection.get("code", "DANGEROUS_QUERY"),
            message=inspection.get("message", "Query blocked by safety guard"),
            detail={
                "type": "safety_error",
                "detail": inspection.get("message", "Query blocked"),
                "warnings": inspection.get("warnings", []),
            },
            error_type="safety_error",
            meta={
                "risk_score": inspection.get("risk_score", 0.0),
                "risk_level": inspection.get("level", "unknown"),
                "safe_mode": inspection.get("mode"),
                "guard": "sqlnocturne",
            },
        )

    def with_meta(self, **items: Any) -> "Result":
        self.meta.update(items)
        return self

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "code": self.code,
            "message": self.message,
            "data": self.data,
            "meta": self.meta,
            "error": self.error,
        }

    def to_json(self, *, indent: int | None = None) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, default=str)

    def __bool__(self) -> bool:
        return self.ok

    def __iter__(self):
        if isinstance(self.data, list):
            return iter(self.data)
        if self.data is None:
            return iter(())
        return iter([self.data])
