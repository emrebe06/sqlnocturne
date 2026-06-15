from sqlnocturne import Database


def test_describe_table_rejects_unsafe_identifier():
    db = Database("sqlite:///:memory:")
    try:
        result = db.describe('users"; DROP TABLE users; --')
        assert result.ok is False
        assert result.code == "INSPECT_FAILED"
    finally:
        db.close()
