from __future__ import annotations


class AuthError(Exception):
    """A stable, non-sensitive authentication or binding failure."""

    def __init__(self, code: str, *, retryable: bool = False, retry_after: int | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable
        self.retry_after = retry_after

