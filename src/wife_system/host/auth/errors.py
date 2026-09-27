from __future__ import annotations

from enum import StrEnum


class AuthErrorCode(StrEnum):
    AUTHENTICATION_REQUIRED = "authentication_required"
    INVALID_CREDENTIALS = "invalid_credentials"
    SESSION_REVOKED = "session_revoked"
    SESSION_EXPIRED = "session_expired"
    INVALID_REFRESH_TOKEN = "invalid_refresh_token"
    SESSION_REFRESH_REPLAYED = "session_refresh_replayed"
    CHANNEL_ADAPTER_UNAUTHORIZED = "channel_adapter_unauthorized"
    BOOTSTRAP_UNAUTHORIZED = "bootstrap_unauthorized"
    SESSION_NOT_FOUND = "session_not_found"
    BINDING_NOT_FOUND = "binding_not_found"
    ACCOUNT_NOT_FOUND = "account_not_found"
    ALREADY_INITIALIZED = "already_initialized"
    ACTIVE_SESSION_LIMIT = "active_session_limit"
    CHANNEL_IDENTITY_CONFLICT = "channel_identity_conflict"
    BINDING_CODE_INVALID = "binding_code_invalid"
    ONE_TIME_SECRET_UNAVAILABLE = "one_time_secret_unavailable"
    INVALID_HANDLE = "invalid_handle"
    INVALID_PASSWORD = "invalid_password"
    INVALID_DEVICE = "invalid_device"
    INVALID_CHANNEL = "invalid_channel"
    LOGIN_RATE_LIMITED = "login_rate_limited"


AUTH_ERROR_CODES = frozenset(code.value for code in AuthErrorCode)


class AuthError(Exception):
    """A stable, non-sensitive authentication or binding failure."""

    def __init__(self, code: str | AuthErrorCode, *, retryable: bool = False, retry_after: int | None = None) -> None:
        normalized = code.value if isinstance(code, AuthErrorCode) else code
        if normalized not in AUTH_ERROR_CODES:
            raise ValueError(f"unknown AuthError code: {normalized}")
        super().__init__(normalized)
        self.code = normalized
        self.retryable = retryable
        self.retry_after = retry_after
