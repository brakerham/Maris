"""Narrow managed-desktop startup nonce gate."""

from __future__ import annotations

import hmac
from dataclasses import dataclass


class DesktopReadinessError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class DesktopRuntimeGate:
    managed: bool = False
    startup_nonce: bytes | None = None

    def __post_init__(self) -> None:
        if self.managed and (not isinstance(self.startup_nonce, bytes) or len(self.startup_nonce) < 32):
            raise ValueError("invalid_desktop_startup_nonce")
        if not self.managed and self.startup_nonce is not None:
            raise ValueError("unexpected_desktop_startup_nonce")

    def verify_desktop_ready(self, supplied: str | None) -> None:
        if not self.managed:
            raise DesktopReadinessError("desktop_profile_required")
        if supplied is None:
            raise DesktopReadinessError("desktop_startup_nonce_required")
        assert self.startup_nonce is not None
        if not hmac.compare_digest(supplied.encode("utf-8"), self.startup_nonce):
            raise DesktopReadinessError("desktop_startup_nonce_mismatch")


DISABLED_DESKTOP_GATE = DesktopRuntimeGate()
