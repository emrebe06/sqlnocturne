"""Human-readable safety reports."""

from __future__ import annotations

from dataclasses import dataclass, field
import json


@dataclass(slots=True)
class SafetyReport:
    sql: str
    inspection: dict
    notes: list[str] = field(default_factory=list)

    @property
    def allowed(self) -> bool:
        return bool(self.inspection.get("allowed", False))

    @property
    def risk_score(self) -> float:
        return float(self.inspection.get("risk_score", 0.0))

    @property
    def level(self) -> str:
        return str(self.inspection.get("level", "unknown"))

    def add_note(self, note: str) -> "SafetyReport":
        self.notes.append(note)
        return self

    def to_dict(self) -> dict:
        return {
            "sql": self.sql,
            "allowed": self.allowed,
            "risk_score": self.risk_score,
            "level": self.level,
            "code": self.inspection.get("code"),
            "message": self.inspection.get("message"),
            "warnings": self.inspection.get("warnings", []),
            "notes": self.notes,
            "inspection": self.inspection,
        }

    def to_json(self, *, indent: int | None = None) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_text(self) -> str:
        lines = [
            f"SQLNocturne Safety Report",
            f"Allowed: {self.allowed}",
            f"Risk: {self.risk_score:.2f} ({self.level})",
            f"Code: {self.inspection.get('code')}",
            f"Message: {self.inspection.get('message')}",
            "",
            "SQL:",
            self.sql,
        ]
        warnings = self.inspection.get("warnings", [])
        if warnings:
            lines.append("")
            lines.append("Warnings:")
            for warning in warnings:
                lines.append(f"- {warning}")
        if self.notes:
            lines.append("")
            lines.append("Notes:")
            for note in self.notes:
                lines.append(f"- {note}")
        return "\n".join(lines)


def build_report(sql: str, inspection: dict) -> SafetyReport:
    report = SafetyReport(sql, inspection)
    if not report.allowed:
        report.add_note("The query should not be executed in the current safe mode.")
    elif report.risk_score > 0.5:
        report.add_note("The query is allowed but should be reviewed.")
    else:
        report.add_note("The query is considered low risk by the current heuristic rules.")
    return report
