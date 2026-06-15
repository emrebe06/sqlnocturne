"""Adapter contract helpers.

These objects make SQLNocturne's future multi-database direction explicit. A
new adapter can expose a manifest so applications can inspect what is supported
before relying on backend-specific behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AdapterFeature:
    name: str
    supported: bool
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "supported": self.supported,
            "notes": self.notes,
        }


@dataclass(slots=True)
class AdapterManifest:
    name: str
    dialect: str
    driver: str
    version: str = "unknown"
    features: list[AdapterFeature] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def feature(self, name: str, supported: bool, notes: str = "") -> "AdapterManifest":
        self.features.append(AdapterFeature(name, supported, notes))
        return self

    def supports(self, name: str) -> bool:
        for feature in self.features:
            if feature.name == name:
                return feature.supported
        return False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "dialect": self.dialect,
            "driver": self.driver,
            "version": self.version,
            "features": [feature.to_dict() for feature in self.features],
            "metadata": self.metadata,
        }


def sqlite_manifest(*, memory: bool = False) -> AdapterManifest:
    return (
        AdapterManifest(
            name="sqlite",
            dialect="sqlite",
            driver="sqlite3",
            version="stdlib",
            metadata={"memory": memory},
        )
        .feature("transactions", True, "SQLite transactions are available through sqlite3.")
        .feature("savepoints", True, "SQLite supports SAVEPOINT syntax.")
        .feature("foreign_keys", True, "Enabled by PRAGMA foreign_keys = ON.")
        .feature("schemas", False, "SQLite does not support named schemas like PostgreSQL.")
        .feature("returning", True, "Modern SQLite supports RETURNING; SQLNocturne does not require it yet.")
        .feature("json_type", False, "JSON can be stored as TEXT in V0.1.")
        .feature("upsert", True, "SQLite supports ON CONFLICT; portable helper is used first.")
    )


def future_postgresql_manifest() -> AdapterManifest:
    return (
        AdapterManifest(name="postgresql", dialect="postgresql", driver="external", version="future")
        .feature("transactions", True)
        .feature("savepoints", True)
        .feature("foreign_keys", True)
        .feature("schemas", True)
        .feature("returning", True)
        .feature("json_type", True)
        .feature("upsert", True)
    )


def future_mysql_manifest() -> AdapterManifest:
    return (
        AdapterManifest(name="mysql", dialect="mysql", driver="external", version="future")
        .feature("transactions", True)
        .feature("savepoints", True)
        .feature("foreign_keys", True)
        .feature("schemas", True, "Database/schema naming differs by engine.")
        .feature("returning", False, "RETURNING availability depends on version and statement type.")
        .feature("json_type", True)
        .feature("upsert", True)
    )


def manifest_for(name: str) -> AdapterManifest:
    key = (name or "sqlite").lower()
    if key == "sqlite":
        return sqlite_manifest()
    if key in {"postgres", "postgresql"}:
        return future_postgresql_manifest()
    if key == "mysql":
        return future_mysql_manifest()
    return AdapterManifest(
        name=key,
        dialect=key,
        driver="unknown",
        version="unknown",
        features=[],
        metadata={"registered": False},
    )


def compare_manifests(*manifests: AdapterManifest) -> dict:
    feature_names = sorted({feature.name for manifest in manifests for feature in manifest.features})
    rows = []
    for feature_name in feature_names:
        row = {"feature": feature_name}
        for manifest in manifests:
            row[manifest.name] = manifest.supports(feature_name)
        rows.append(row)
    return {
        "adapters": [manifest.name for manifest in manifests],
        "features": rows,
    }


def known_manifests() -> list[AdapterManifest]:
    return [
        sqlite_manifest(),
        future_postgresql_manifest(),
        future_mysql_manifest(),
    ]
