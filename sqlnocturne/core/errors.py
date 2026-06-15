"""Error classes used by SQLNocturne.

Public query execution prefers returning ``Result`` objects, but exceptions are
still useful for setup problems, programmer mistakes, and CLI failures.
"""


class NocturneError(Exception):
    """Base exception for every SQLNocturne controlled error."""

    code = "NOCTURNE_ERROR"
    error_type = "nocturne_error"

    def __init__(self, message: str, *, detail: str | None = None, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.detail = detail or message
        if code:
            self.code = code

    def to_error(self) -> dict:
        return {
            "type": self.error_type,
            "detail": self.detail,
        }

    def to_dict(self) -> dict:
        return {
            "ok": False,
            "code": self.code,
            "message": self.message,
            "error": self.to_error(),
        }


class ConnectionError(NocturneError):
    code = "CONNECTION_ERROR"
    error_type = "connection_error"


class AdapterError(NocturneError):
    code = "ADAPTER_ERROR"
    error_type = "adapter_error"


class QueryError(NocturneError):
    code = "QUERY_ERROR"
    error_type = "query_error"


class SafetyError(NocturneError):
    code = "SAFETY_ERROR"
    error_type = "safety_error"


class MigrationError(NocturneError):
    code = "MIGRATION_ERROR"
    error_type = "migration_error"


def error_from_exception(exc: Exception) -> dict:
    if isinstance(exc, NocturneError):
        return exc.to_error()
    return {
        "type": exc.__class__.__name__,
        "detail": str(exc),
    }
