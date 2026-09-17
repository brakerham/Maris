from __future__ import annotations


RETRYABLE_CODES = {"concurrent_modification", "database_unavailable"}


class FinanceError(Exception):
    """Stable, privacy-safe application error."""

    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        self.retryable = code in RETRYABLE_CODES
        self.message = message or code.replace("_", " ")
        super().__init__(self.message)

    def as_dict(self) -> dict[str, object]:
        return {"code": self.code, "message": self.message, "retryable": self.retryable}
