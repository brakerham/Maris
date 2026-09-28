"""Fail-closed production composition root for Uvicorn and the desktop supervisor."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from fastapi import FastAPI

from wife_system.activity_import.service import ActivityImportService
from wife_system.agent.application import build_agent_application
from wife_system.agent.finance_tools import FinanceToolAdapter
from wife_system.agent.pending import PendingActionStore
from wife_system.agent.providers import ModelProvider
from wife_system.api.app import create_app
from wife_system.api.desktop_runtime import DesktopRuntimeGate
from wife_system.finance import FinanceService, IdempotencyKeys
from wife_system.finance.db import make_engine, make_session_factory
from wife_system.host.auth.service import AuthSecrets
from wife_system.host.factory import build_host_runtime
from wife_system.host.state import HostKeys


class ProductionConfigError(RuntimeError):
    """A safe startup error whose message contains only a field identifier."""


@dataclass(frozen=True)
class ProductionConfig:
    database_url: str
    bootstrap_token: bytes
    binding_hmac_key: bytes
    adapter_token: bytes
    host_state_key: bytes
    cursor_key: bytes
    agent_digest_key: bytes
    finance_receipt_key: bytes
    alembic_head: str = "p4_host_state"
    desktop_managed: bool = False
    desktop_startup_nonce: bytes | None = None

    def __post_init__(self) -> None:
        if not self.database_url.strip():
            raise ProductionConfigError("missing_database_url")
        for name in (
            "bootstrap_token",
            "binding_hmac_key",
            "adapter_token",
            "host_state_key",
            "cursor_key",
            "agent_digest_key",
            "finance_receipt_key",
        ):
            value = getattr(self, name)
            if not isinstance(value, bytes) or len(value) < 32:
                raise ProductionConfigError(f"invalid_{name}")
        if not self.alembic_head.strip():
            raise ProductionConfigError("invalid_alembic_head")
        if self.desktop_managed and (
            not isinstance(self.desktop_startup_nonce, bytes)
            or len(self.desktop_startup_nonce) < 32
        ):
            raise ProductionConfigError("invalid_desktop_startup_nonce")
        if not self.desktop_managed and self.desktop_startup_nonce is not None:
            raise ProductionConfigError("unexpected_desktop_startup_nonce")

    @classmethod
    def from_environment(
        cls, environment: Mapping[str, str] | None = None
    ) -> "ProductionConfig":
        values = os.environ if environment is None else environment

        def required(name: str) -> str:
            value = values.get(name)
            if value is None or not value.strip():
                raise ProductionConfigError(f"missing_{name.casefold()}")
            return value

        def secret(name: str) -> bytes:
            value = required(name).encode("utf-8")
            if len(value) < 32:
                raise ProductionConfigError(f"invalid_{name.casefold()}")
            return value

        desktop_profile = values.get("WIFE_DESKTOP_PROFILE", "").strip()
        if desktop_profile not in {"", "managed"}:
            raise ProductionConfigError("invalid_wife_desktop_profile")
        nonce = values.get("WIFE_DESKTOP_STARTUP_NONCE")
        return cls(
            database_url=required("WIFE_DATABASE_URL"),
            bootstrap_token=secret("WIFE_BOOTSTRAP_TOKEN"),
            binding_hmac_key=secret("WIFE_BINDING_HMAC_KEY"),
            adapter_token=secret("WIFE_ADAPTER_TOKEN"),
            host_state_key=secret("WIFE_HOST_STATE_KEY"),
            cursor_key=secret("WIFE_CURSOR_KEY"),
            agent_digest_key=secret("WIFE_AGENT_DIGEST_KEY"),
            finance_receipt_key=secret("WIFE_FINANCE_RECEIPT_KEY"),
            alembic_head=values.get("WIFE_ALEMBIC_HEAD", "p4_host_state"),
            desktop_managed=desktop_profile == "managed",
            desktop_startup_nonce=nonce.encode("utf-8") if nonce is not None else None,
        )


def create_production_app(
    config: ProductionConfig | None = None,
    *,
    provider: ModelProvider | None = None,
) -> FastAPI:
    """Compose every production dependency without implicit fake services."""

    resolved = config or ProductionConfig.from_environment()
    engine = make_engine(resolved.database_url)
    sessions = make_session_factory(engine)
    finance_keys = IdempotencyKeys({1: resolved.finance_receipt_key})
    finance = FinanceService(sessions, finance_keys)
    host_finance_adapter = FinanceToolAdapter(finance, PendingActionStore(sessions))
    activity_import = ActivityImportService(sessions, finance_keys)
    runtime = build_host_runtime(
        sessions=sessions,
        finance_adapter=host_finance_adapter,
        auth_secrets=AuthSecrets(
            bootstrap_token=resolved.bootstrap_token,
            binding_hmac_key=resolved.binding_hmac_key,
            adapter_token=resolved.adapter_token,
        ),
        state_keys=HostKeys({1: resolved.host_state_key}),
        cursor_secret=resolved.cursor_key,
        alembic_head=resolved.alembic_head,
        agent_provider_ready=provider is not None,
    )
    if provider is None:
        agent = None
    else:
        agent = build_agent_application(
            sessions=sessions,
            finance=finance,
            provider=provider,
            digest_key=resolved.agent_digest_key,
            host_runtime=runtime,
        )
    application = create_app(
        host_runtime=runtime,
        agent_application=agent,
        activity_import_service=activity_import,
        desktop_runtime_gate=DesktopRuntimeGate(
            managed=resolved.desktop_managed,
            startup_nonce=resolved.desktop_startup_nonce,
        ),
    )
    application.state.engine = engine
    application.state.sessions = sessions
    return application


def create_production_openapi_app() -> FastAPI:
    """Build the production route graph without opening a database.

    OpenAPI generation inspects route contracts only. Runtime dependencies stay
    fail-closed and are never invoked by this offline export seam.
    """

    return create_app()


__all__ = [
    "ProductionConfig",
    "ProductionConfigError",
    "create_production_app",
    "create_production_openapi_app",
]
