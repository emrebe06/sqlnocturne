from sqlnocturne.core.result import Result
from sqlnocturne.integrations.quickapi import nocturne_response, quickapi_payload


def test_nocturne_response_from_result():
    result = Result.success({"hello": "world"})

    payload = nocturne_response(result)

    assert payload["ok"] is True
    assert payload["data"] == {"hello": "world"}


def test_quickapi_payload_tuple():
    ok, payload = quickapi_payload(Result.error_result(code="X", message="No"))

    assert ok is False
    assert payload["code"] == "X"
