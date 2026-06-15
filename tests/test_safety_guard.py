from sqlnocturne.safety import SafetyGuard


def test_delete_without_where_blocked():
    result = SafetyGuard("strict").inspect("DELETE FROM users")

    assert result["allowed"] is False
    assert result["code"] == "DELETE_WITHOUT_WHERE"


def test_update_without_where_blocked():
    result = SafetyGuard("strict").inspect("UPDATE users SET name = ?", "UPDATE")

    assert result["allowed"] is False
    assert result["code"] == "UPDATE_WITHOUT_WHERE"


def test_select_star_without_limit_warns():
    result = SafetyGuard("strict").inspect("SELECT * FROM users")

    assert result["allowed"] is True
    assert result["code"] == "WARNINGS"
    assert result["warnings"]


def test_multiple_statements_blocked():
    result = SafetyGuard("strict").inspect("SELECT 1; DELETE FROM users")

    assert result["allowed"] is False
    assert result["code"] == "MULTIPLE_STATEMENTS"


def test_safe_select_allowed():
    result = SafetyGuard("strict").inspect("SELECT id FROM users WHERE id = ? LIMIT ?")

    assert result["allowed"] is True
    assert result["level"] in {"safe", "watch"}
