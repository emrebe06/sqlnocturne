"""Main safety guard."""

from __future__ import annotations

from sqlnocturne.safety.injection import detect_injection
from sqlnocturne.safety.ml_guard import MLGuard
from sqlnocturne.safety.native import inspect_native
from sqlnocturne.safety.risk import clamp_score, merge_scores, risk_level
from sqlnocturne.safety.rules import inspect_rules, query_type
from sqlnocturne.safety.tokenizer import normalize_sql


class SafetyGuard:
    """Inspect SQL before execution."""

    def __init__(self, mode: str = "strict"):
        if mode not in {"off", "normal", "strict", "paranoid"}:
            raise ValueError("mode must be off, normal, strict, or paranoid")
        self.mode = mode
        self.ml_guard = MLGuard()

    def inspect(self, sql: str, query_type_hint: str | None = None) -> dict:
        normalized = normalize_sql(sql)
        qtype = query_type(normalized, query_type_hint)
        ml = self.ml_guard.inspect(normalized)
        native = inspect_native(normalized, self.mode)
        if self.mode == "off":
            injection = detect_injection(normalized)
            score = max(clamp_score(injection["risk_score"] * 0.5), ml["risk_score"] * 0.35)
            return {
                "allowed": True,
                "risk_score": clamp_score(score),
                "level": risk_level(score),
                "code": "OK",
                "message": "Safety guard disabled",
                "warnings": injection["warnings"],
                "mode": self.mode,
                "query_type": qtype,
                "ml": ml,
                "native": native,
            }

        findings = inspect_rules(normalized, self.mode, qtype)
        injection = detect_injection(normalized)
        rule_score = max((finding.risk for finding in findings), default=0.02)
        injection_score = injection["risk_score"]
        score = merge_scores(rule_score, injection_score, ml["risk_score"])
        if native:
            score = merge_scores(score, float(native.get("risk_score", 0.0)))

        warnings = [finding.message for finding in findings]
        warnings.extend(injection["warnings"])
        warnings.extend(f"ml:{item}" for item in ml.get("warnings", []))
        if native and native.get("code") == "WARNINGS":
            warnings.append("native:warnings")
        blocking_findings = [finding for finding in findings if finding.blocking]
        blocked_by_injection = injection_score >= 0.80 and self.mode in {"strict", "paranoid"}
        blocked_by_ml = not ml["allowed"] and self.mode in {"strict", "paranoid"}
        blocked_by_native = bool(native and native.get("allowed") is False and self.mode in {"strict", "paranoid"})
        allowed = not blocking_findings and not blocked_by_injection and not blocked_by_ml and not blocked_by_native
        if self.mode == "normal":
            allowed = True

        code = "OK"
        message = "Query allowed"
        if not allowed:
            if blocking_findings:
                code = blocking_findings[0].code
                message = blocking_findings[0].message
            elif blocked_by_native and native:
                code = str(native.get("code", "NATIVE_GUARD_BLOCK"))
                message = str(native.get("message", "Native guard blocked query"))
            elif blocked_by_ml:
                code = "ML_GUARD_BLOCK"
                message = "ML guard blocked suspicious SQL shape"
            else:
                code = "SUSPICIOUS_SQL"
                message = "SQL contains suspicious injection signals"
        elif warnings:
            code = "WARNINGS"
            message = "Query allowed with warnings"

        return {
            "allowed": allowed,
            "risk_score": score,
            "level": risk_level(score),
            "code": code,
            "message": message,
            "warnings": warnings,
            "mode": self.mode,
            "query_type": qtype,
            "normalized_sql": normalized,
            "findings": [finding.to_dict() for finding in findings],
            "ml": ml,
            "native": native,
        }

    def assert_allowed(self, sql: str, query_type_hint: str | None = None) -> None:
        inspection = self.inspect(sql, query_type_hint)
        if not inspection["allowed"]:
            from sqlnocturne.core.errors import SafetyError

            raise SafetyError(inspection["message"], detail=", ".join(inspection["warnings"]), code=inspection["code"])
