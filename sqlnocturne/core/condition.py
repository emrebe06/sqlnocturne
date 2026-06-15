"""Query condition model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ALLOWED_OPERATORS = {
    "=",
    "!=",
    "<>",
    ">",
    ">=",
    "<",
    "<=",
    "LIKE",
    "NOT LIKE",
    "IN",
    "NOT IN",
    "IS",
    "IS NOT",
}


@dataclass(slots=True)
class Condition:
    column: str
    operator: str
    value: Any
    boolean: str = "AND"

    def __post_init__(self) -> None:
        self.operator = self.operator.upper().strip()
        self.boolean = self.boolean.upper().strip()
        if self.operator not in ALLOWED_OPERATORS:
            allowed = ", ".join(sorted(ALLOWED_OPERATORS))
            raise ValueError(f"Unsupported SQL operator {self.operator!r}; allowed: {allowed}")
        if self.boolean not in {"AND", "OR"}:
            raise ValueError("Condition boolean must be AND or OR")
        if not self.column or not isinstance(self.column, str):
            raise ValueError("Condition column must be a non-empty string")

    @property
    def is_sequence_operator(self) -> bool:
        return self.operator in {"IN", "NOT IN"}

    @property
    def is_null_check(self) -> bool:
        return self.operator in {"IS", "IS NOT"} and self.value is None

    def clone(self, *, boolean: str | None = None) -> "Condition":
        return Condition(self.column, self.operator, self.value, boolean or self.boolean)


class ConditionGroup:
    """Small helper for future nested expressions.

    V0.1 does not expose a complicated boolean expression API, but keeping this
    object makes compiler code easier to extend without changing public methods.
    """

    def __init__(self, conditions: list[Condition] | None = None):
        self.conditions = list(conditions or [])

    def add(self, condition: Condition) -> "ConditionGroup":
        self.conditions.append(condition)
        return self

    def __bool__(self) -> bool:
        return bool(self.conditions)

    def __iter__(self):
        return iter(self.conditions)

    def __len__(self) -> int:
        return len(self.conditions)
