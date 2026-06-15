"""Small feature-based ML-style SQL guard.

This is intentionally local and deterministic for V0.1. It behaves like a tiny
linear model over SQL features: no network, no dependency, no hidden training
artifact. Later versions can replace the coefficients with a real trained
model while preserving this report shape.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from sqlnocturne.safety.tokenizer import normalized_tokens, split_statements, uppercase_keywords


@dataclass(frozen=True, slots=True)
class MLFeature:
    name: str
    value: float
    weight: float

    @property
    def contribution(self) -> float:
        return self.value * self.weight

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "weight": self.weight,
            "contribution": round(self.contribution, 5),
        }


class MLGuard:
    """Dependency-free model used as a second opinion under rule/native guards."""

    def __init__(self, threshold: float = 0.74):
        self.threshold = threshold

    def inspect(self, sql: str) -> dict:
        text = sql or ""
        upper = uppercase_keywords(text)
        tokens = normalized_tokens(text)
        token_set = set(tokens)
        statements = split_statements(text)
        features = [
            MLFeature("empty", 1.0 if not text.strip() else 0.0, 3.2),
            MLFeature("multi_statement", max(0.0, len(statements) - 1), 1.6),
            MLFeature("delete_without_where", 1.0 if "DELETE" in token_set and "WHERE" not in token_set else 0.0, 2.8),
            MLFeature("update_without_where", 1.0 if "UPDATE" in token_set and "WHERE" not in token_set else 0.0, 2.6),
            MLFeature("schema_danger", 1.0 if token_set & {"DROP", "TRUNCATE", "ALTER"} else 0.0, 2.1),
            MLFeature("union_select", 1.0 if "UNION SELECT" in upper else 0.0, 2.3),
            MLFeature("tautology", 1.0 if " OR 1=1" in upper or " OR TRUE" in upper else 0.0, 3.5),
            MLFeature("comment_probe", float(upper.count("--") + upper.count("/*")), 1.0),
            MLFeature("time_probe", 1.0 if "SLEEP(" in upper or "BENCHMARK(" in upper else 0.0, 1.7),
            MLFeature("information_schema", 1.0 if "INFORMATION_SCHEMA" in upper else 0.0, 0.9),
            MLFeature("select_star_no_limit", 1.0 if "SELECT" in token_set and "*" in token_set and "LIMIT" not in token_set else 0.0, 0.7),
            MLFeature("token_volume", min(len(tokens) / 120.0, 1.0), 0.35),
        ]
        logit = -2.85 + sum(feature.contribution for feature in features)
        score = 1.0 / (1.0 + math.exp(-logit))
        active = [feature for feature in features if feature.value > 0]
        return {
            "engine": "sqlnocturne-mlguard-v1",
            "risk_score": round(score, 5),
            "allowed": score < self.threshold,
            "threshold": self.threshold,
            "features": [feature.to_dict() for feature in active],
            "warnings": [feature.name for feature in active if feature.weight >= 0.7],
        }
