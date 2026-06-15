"""Optional QuickAPI response helper.

This module intentionally does not import QuickAPI. SQLNocturne remains a
separate product; this helper only shapes a SQLNocturne Result into a plain dict
that a QuickAPI route can pass to its own response factory.
"""

from __future__ import annotations


def nocturne_response(result):
    if hasattr(result, "to_dict"):
        return result.to_dict()
    if isinstance(result, dict):
        return result
    return {
        "ok": True,
        "code": "OK",
        "message": "Value returned",
        "data": result,
        "meta": {"engine": "sqlnocturne"},
        "error": None,
    }


def quickapi_payload(result) -> tuple[bool, dict]:
    payload = nocturne_response(result)
    return bool(payload.get("ok")), payload
