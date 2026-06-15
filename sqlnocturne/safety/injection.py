"""Heuristic SQL injection detector.

This is intentionally described as heuristic. It is meant to catch obvious
dangerous raw SQL shapes, not to replace parameterized queries.
"""

from __future__ import annotations

import re

from sqlnocturne.safety.tokenizer import split_statements, uppercase_keywords


PATTERNS = [
    ("tautology_or_1_eq_1", re.compile(r"\bOR\s+1\s*=\s*1\b", re.IGNORECASE)),
    ("tautology_or_true", re.compile(r"\bOR\s+TRUE\b", re.IGNORECASE)),
    ("line_comment", re.compile(r"--")),
    ("block_comment", re.compile(r"/\*")),
    ("union_select", re.compile(r"\bUNION\s+SELECT\b", re.IGNORECASE)),
    ("stacked_drop", re.compile(r";\s*DROP\b", re.IGNORECASE)),
    ("sleep_probe", re.compile(r"\b(SLEEP|BENCHMARK)\s*\(", re.IGNORECASE)),
    ("information_schema_probe", re.compile(r"\bINFORMATION_SCHEMA\b", re.IGNORECASE)),
]


def detect_injection(sql: str) -> dict:
    warnings: list[str] = []
    score = 0.0
    text = sql or ""
    for name, pattern in PATTERNS:
        if pattern.search(text):
            warnings.append(name)
            score += 0.16
    if len(split_statements(text)) > 1:
        warnings.append("multiple_statements")
        score += 0.24
    upper = uppercase_keywords(text)
    if upper.count("'") % 2 == 1:
        warnings.append("unbalanced_single_quote")
        score += 0.18
    if upper.count('"') % 2 == 1:
        warnings.append("unbalanced_double_quote")
        score += 0.12
    return {
        "risk_score": min(score, 1.0),
        "warnings": warnings,
        "suspicious": bool(warnings),
    }
