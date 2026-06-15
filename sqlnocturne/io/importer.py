"""JSON import helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlnocturne.core.result import Result


def load_json_rows(source: str | Path | list[dict]) -> list[dict]:
    if isinstance(source, list):
        return source
    value = str(source)
    path = Path(value)
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = value
    data = json.loads(text)
    if isinstance(data, dict) and "items" in data:
        data = data["items"]
    if isinstance(data, dict):
        return [data]
    if not isinstance(data, list):
        raise ValueError("JSON import expects an object, list, or {'items': [...]} payload")
    return data


def import_json_rows(db, table: str, source: str | Path | list[dict], *, transactional: bool = True) -> Result:
    try:
        rows = load_json_rows(source)
    except Exception as exc:
        return Result.error_result(
            code="IMPORT_PARSE_FAILED",
            message="Could not parse JSON rows",
            detail=str(exc),
            error_type="import_error",
        )

    batch = db.batch(transactional=transactional)
    for row in rows:
        if not isinstance(row, dict):
            return Result.error_result(
                code="IMPORT_ROW_INVALID",
                message="Every imported row must be an object",
                detail=repr(row),
                error_type="import_error",
            )
        batch.insert(table, row)
    result = batch.run()
    if result.ok:
        result.message = "JSON rows imported"
        result.meta["imported_rows"] = len(rows)
    return result
