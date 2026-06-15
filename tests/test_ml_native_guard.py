from sqlnocturne.safety import MLGuard, SafetyGuard


def test_ml_guard_scores_obvious_injection():
    report = MLGuard().inspect("SELECT * FROM users WHERE id = 1 OR 1=1 --")

    assert report["risk_score"] > 0.70
    assert "tautology" in report["warnings"]


def test_safety_guard_includes_ml_report():
    report = SafetyGuard("strict").inspect("SELECT id FROM users WHERE id = ? LIMIT ?")

    assert report["allowed"] is True
    assert report["ml"]["engine"] == "sqlnocturne-mlguard-v1"


def test_safety_guard_blocks_ml_shape():
    report = SafetyGuard("strict").inspect("SELECT * FROM users WHERE id = 1 OR 1=1; DROP TABLE users")

    assert report["allowed"] is False
    assert report["risk_score"] >= 0.80
