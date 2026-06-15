"""Safety rules for SQLNocturne."""

from __future__ import annotations

from dataclasses import dataclass

from sqlnocturne.safety.tokenizer import first_keyword, normalized_tokens, split_statements


@dataclass(slots=True)
class RuleFinding:
    code: str
    message: str
    risk: float
    blocking: bool = False

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "risk": self.risk,
            "blocking": self.blocking,
        }


STRICT_MODES = {"strict", "paranoid"}
SCHEMA_DANGER = {"DROP", "TRUNCATE", "ALTER"}


def query_type(sql: str, explicit: str | None = None) -> str:
    if explicit:
        return explicit.upper()
    return first_keyword(sql) or "RAW"


def has_where(tokens: list[str]) -> bool:
    return "WHERE" in tokens


def has_limit(tokens: list[str]) -> bool:
    return "LIMIT" in tokens


def inspect_rules(sql: str, mode: str, explicit_type: str | None = None) -> list[RuleFinding]:
    mode = mode or "strict"
    tokens = normalized_tokens(sql)
    qtype = query_type(sql, explicit_type)
    findings: list[RuleFinding] = []

    statements = split_statements(sql)
    if len(statements) > 1:
        findings.append(
            RuleFinding(
                "MULTIPLE_STATEMENTS",
                "Multiple SQL statements are not allowed in strict modes",
                0.95,
                mode in STRICT_MODES,
            )
        )

    if qtype == "DELETE" and not has_where(tokens):
        findings.append(
            RuleFinding(
                "DELETE_WITHOUT_WHERE",
                "DELETE without WHERE can remove an entire table",
                0.98,
                mode in STRICT_MODES,
            )
        )

    if qtype == "UPDATE" and not has_where(tokens):
        findings.append(
            RuleFinding(
                "UPDATE_WITHOUT_WHERE",
                "UPDATE without WHERE can modify an entire table",
                0.94,
                mode in STRICT_MODES,
            )
        )

    if qtype == "SELECT" and "*" in tokens and not has_limit(tokens):
        findings.append(
            RuleFinding(
                "SELECT_STAR_WITHOUT_LIMIT",
                "SELECT * without LIMIT can pull too much data",
                0.32,
                False,
            )
        )

    if qtype in SCHEMA_DANGER:
        findings.append(
            RuleFinding(
                "DANGEROUS_SCHEMA_OPERATION",
                f"{qtype} is dangerous in strict modes",
                0.9,
                mode in STRICT_MODES,
            )
        )

    if mode == "paranoid" and qtype in {"DELETE", "UPDATE"}:
        findings.append(
            RuleFinding(
                "PARANOID_WRITE_REVIEW",
                f"{qtype} requires extra review in paranoid mode",
                0.55,
                False,
            )
        )

    return findings
