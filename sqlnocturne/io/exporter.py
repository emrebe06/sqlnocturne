"""JSON export helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from sqlnocturne.core.result import Result


def rows_from_result(result_or_rows) -> list[dict]:
    if hasattr(result_or_rows, "to_dict"):
        payload = result_or_rows.to_dict()
        data = payload.get("data")
    else:
        data = result_or_rows
    if data is None:
        return []
    if isinstance(data, dict) and "items" in data:
        data = data["items"]
    if isinstance(data, dict):
        return [data]
    return list(data)


def export_json(result_or_rows, path: str | Path | None = None, *, indent: int = 2) -> Result:
    rows = rows_from_result(result_or_rows)
    text = json.dumps(rows, ensure_ascii=False, indent=indent, default=str)
    if path is None:
        return Result.success(text, message="Rows exported to JSON string", meta={"rows": len(rows), "format": "json"})
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return Result.success({"path": str(target)}, message="Rows exported to JSON file", meta={"rows": len(rows), "format": "json"})


def export_json_lines(result_or_rows, path: str | Path | None = None) -> Result:
    rows = rows_from_result(result_or_rows)
    text = "\n".join(json.dumps(row, ensure_ascii=False, default=str) for row in rows)
    if path is None:
        return Result.success(text, message="Rows exported to JSONL string", meta={"rows": len(rows), "format": "jsonl"})
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text + ("\n" if text else ""), encoding="utf-8")
    return Result.success({"path": str(target)}, message="Rows exported to JSONL file", meta={"rows": len(rows), "format": "jsonl"})


def export_result_payload(result: Result, path: str | Path | None = None) -> Result:
    text = result.to_json(indent=2)
    if path is None:
        return Result.success(text, message="Result payload exported", meta={"format": "json"})
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return Result.success({"path": str(target)}, message="Result payload exported", meta={"format": "json"})
