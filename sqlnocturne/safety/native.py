"""Optional native bridge for SQLNocturne safety.

Python remains the product surface. If the native library is present, the guard
can ask C/C++/ASM-backed code for a second opinion. If it is not present,
SQLNocturne keeps working with pure Python.
"""

from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
from typing import Any


def _candidate_names() -> list[str]:
    if os.name == "nt":
        return ["sqlnocturne_native.dll", "nocturne_native.dll"]
    if hasattr(os, "uname") and os.uname().sysname == "Darwin":  # type: ignore[attr-defined]
        return ["libsqlnocturne_native.dylib", "libnocturne_native.dylib"]
    return ["libsqlnocturne_native.so", "libnocturne_native.so"]


def _candidate_paths() -> list[Path]:
    env = os.environ.get("SQLNOCTURNE_NATIVE_LIBRARY")
    paths: list[Path] = [Path(env)] if env else []
    root = Path(__file__).resolve().parents[1]
    for name in _candidate_names():
        paths.extend(
            [
                Path.cwd() / name,
                Path.cwd() / "build" / "Release" / name,
                Path.cwd() / "native-build" / "Release" / name,
                Path.cwd() / "native-build" / name,
                root / "native" / "build" / "Release" / name,
                root / "native" / "build" / name,
            ]
        )
    return paths


class NativeSafety:
    def __init__(self, library: str | os.PathLike[str] | None = None):
        self.library_path = Path(library).expanduser() if library else self._discover()
        self.lib = ctypes.CDLL(str(self.library_path))
        self._configure()

    @classmethod
    def available(cls) -> bool:
        return cls._discover(required=False) is not None

    @staticmethod
    def _discover(required: bool = True) -> Path | None:
        for path in _candidate_paths():
            if path and path.exists():
                return path
        if required:
            raise FileNotFoundError("SQLNocturne native library was not found")
        return None

    def inspect(self, sql: str, mode: str = "strict") -> dict[str, Any]:
        raw = sql.encode("utf-8")
        ptr = self.lib.nocturne_validate_query_json(raw, mode.encode("utf-8"))
        if not ptr:
            return {"engine": "native", "available": False, "risk_score": 0.0, "warnings": []}
        try:
            text = ctypes.cast(ptr, ctypes.c_char_p).value.decode("utf-8")
            data = json.loads(text)
            data["engine"] = "sqlnocturne-native"
            data["available"] = True
            return data
        finally:
            self.lib.nocturne_free_string(ptr)

    def runtime(self) -> dict[str, Any]:
        ptr = self.lib.nocturne_runtime_json()
        if not ptr:
            return {"available": False}
        try:
            return json.loads(ctypes.cast(ptr, ctypes.c_char_p).value.decode("utf-8"))
        finally:
            self.lib.nocturne_free_string(ptr)

    def _configure(self) -> None:
        self.lib.nocturne_validate_query_json.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.nocturne_validate_query_json.restype = ctypes.c_void_p
        self.lib.nocturne_runtime_json.argtypes = []
        self.lib.nocturne_runtime_json.restype = ctypes.c_void_p
        self.lib.nocturne_free_string.argtypes = [ctypes.c_void_p]
        self.lib.nocturne_free_string.restype = None


_NATIVE: NativeSafety | None | bool = None


def inspect_native(sql: str, mode: str = "strict") -> dict[str, Any] | None:
    global _NATIVE
    if _NATIVE is False:
        return None
    if _NATIVE is None:
        try:
            _NATIVE = NativeSafety()
        except Exception:
            _NATIVE = False
            return None
    assert isinstance(_NATIVE, NativeSafety)
    try:
        return _NATIVE.inspect(sql, mode)
    except Exception:
        return None
