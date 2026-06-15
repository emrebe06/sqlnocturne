from sqlnocturne.core.result import Result


def test_success_result_shape():
    result = Result.success([{"id": 1}], message="Rows selected", meta={"rows": 1})

    payload = result.to_dict()

    assert payload["ok"] is True
    assert payload["code"] == "OK"
    assert payload["message"] == "Rows selected"
    assert payload["data"] == [{"id": 1}]
    assert payload["meta"]["rows"] == 1
    assert payload["meta"]["engine"] == "sqlnocturne"
    assert payload["error"] is None


def test_error_result_shape():
    result = Result.error_result(
        code="DANGEROUS_QUERY",
        message="DELETE without WHERE is blocked",
        detail="Safe mode prevents full table delete",
        error_type="safety_error",
        meta={"risk_score": 0.98},
    )

    payload = result.to_dict()

    assert payload["ok"] is False
    assert payload["code"] == "DANGEROUS_QUERY"
    assert payload["error"]["type"] == "safety_error"
    assert payload["meta"]["risk_score"] == 0.98
    assert "DANGEROUS_QUERY" in result.to_json()
