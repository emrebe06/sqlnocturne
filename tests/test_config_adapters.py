import pytest

from sqlnocturne import Database
from sqlnocturne.core.config import DatabaseConfig
from sqlnocturne.core.errors import AdapterError


def test_sqlite_bare_path_gets_db_suffix():
    config = DatabaseConfig("sqlite:///shop")

    assert config.sqlite_path.endswith("shop.db")
    assert config.database_name == "shop.db"


def test_sqlite_explicit_suffix_is_preserved():
    config = DatabaseConfig("sqlite:///shop.sqlite3")

    assert config.sqlite_path.endswith("shop.sqlite3")


def test_postgresql_scheme_alias_and_connect_false():
    db = Database("postgres://user:pass@localhost:5432/app", connect=False)
    try:
        assert db.config.scheme == "postgresql"
        assert db.dialect.name == "postgresql"
        assert db.adapter.name == "postgresql"
    finally:
        db.close()


def test_mysql_connect_false():
    db = Database("mysql://user:pass@localhost:3306/app", connect=False)
    try:
        assert db.config.scheme == "mysql"
        assert db.dialect.name == "mysql"
        assert db.adapter.name == "mysql"
    finally:
        db.close()


def test_network_adapter_without_driver_returns_controlled_error():
    db = Database("postgresql://user:pass@localhost:5432/app", connect=False)
    try:
        with pytest.raises(AdapterError) as error:
            db.connect()
        assert error.value.code in {"DRIVER_NOT_INSTALLED", "CONNECTION_ERROR"}
    finally:
        db.close()
