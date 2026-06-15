"""Runtime and database health checks."""

from __future__ import annotations

from dataclasses import dataclass, field
import platform
from time import perf_counter

from sqlnocturne.core.result import Result


@dataclass(slots=True)
class HealthCheck:
    name: str
    ok: bool
    message: str
    details: dict = field(default_factory=dict)
    time_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "ok": self.ok,
            "message": self.message,
            "details": self.details,
            "time_ms": self.time_ms,
        }


def timed_check(name: str, callback) -> HealthCheck:
    start = perf_counter()
    try:
        details = callback()
        elapsed = (perf_counter() - start) * 1000
        return HealthCheck(name, True, "OK", details or {}, round(elapsed, 3))
    except Exception as exc:
        elapsed = (perf_counter() - start) * 1000
        return HealthCheck(name, False, str(exc), {}, round(elapsed, 3))


def check_runtime() -> Result:
    from sqlnocturne import __version__

    checks = [
        HealthCheck(
            "python",
            True,
            "OK",
            {
                "version": platform.python_version(),
                "implementation": platform.python_implementation(),
                "platform": platform.platform(),
            },
            0.0,
        ),
        HealthCheck(
            "sqlnocturne",
            True,
            "OK",
            {"version": __version__},
            0.0,
        ),
    ]
    return Result.success(
        [check.to_dict() for check in checks],
        message="Runtime health checked",
        meta={"ok": all(check.ok for check in checks), "rows": len(checks)},
    )


def check_database(db) -> Result:
    checks = [
        timed_check("adapter", lambda: db.adapter.capabilities()),
        timed_check("dialect", lambda: db.dialect.to_dict()),
        timed_check("select_one", lambda: db.sql("SELECT 1 AS ok").result(fetch="one").to_dict()),
        timed_check("tables", lambda: db.tables().to_dict()),
    ]
    return Result.success(
        [check.to_dict() for check in checks],
        message="Database health checked",
        meta={
            "ok": all(check.ok for check in checks),
            "rows": len(checks),
            "adapter": db.adapter.name,
            "dialect": db.dialect.name,
        },
    )
