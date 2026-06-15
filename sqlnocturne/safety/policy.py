"""Policy engine placeholder."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PolicyDecision:
    allowed: bool
    code: str = "OK"
    message: str = "Policy allowed"
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "code": self.code,
            "message": self.message,
            "reasons": self.reasons,
        }


class PolicyEngine:
    """Future hook for table/action policies.

    V0.1 defaults to allow. The shape is already here so larger applications can
    later plug tenant-aware and role-aware checks without changing Database.
    """

    def __init__(self):
        self.rules: list[tuple[str, str, Any]] = []

    def check(self, table: str | None, action: str, context: dict | None = None) -> bool:
        return self.decide(table, action, context).allowed

    def decide(self, table: str | None, action: str, context: dict | None = None) -> PolicyDecision:
        return PolicyDecision(True, reasons=[])
