"""Risk score helpers."""

from __future__ import annotations


def clamp_score(score: float) -> float:
    if score < 0:
        return 0.0
    if score > 1:
        return 1.0
    return round(float(score), 4)


def risk_level(score: float) -> str:
    value = clamp_score(score)
    if value <= 0.20:
        return "safe"
    if value <= 0.50:
        return "watch"
    if value <= 0.80:
        return "risky"
    return "dangerous"


def merge_scores(*scores: float) -> float:
    """Combine independent heuristic scores without instantly maxing out."""

    total = 0.0
    for score in scores:
        score = clamp_score(score)
        total = 1 - ((1 - total) * (1 - score))
    return clamp_score(total)
