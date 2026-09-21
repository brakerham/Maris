"""Explicit P4-A Host composition root."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from wife_system.host.auth.service import AuthSecrets, AuthService
from wife_system.host.cursor import CursorCodec
from wife_system.host.events import InProcessEventBus
from wife_system.host.registry import ModuleRegistry, RegistryStartupError
from wife_system.host.runtime import HostRuntime
from wife_system.host.state import (
    ConversationService,
    HostIdempotency,
    HostCommandService,
    HostKeys,
    HostStateError,
    MemoryService,
    ModuleSettingService,
)
from wife_system.modules import build_builtin_registry


def build_host_runtime(
    *,
    sessions: sessionmaker[Session],
    finance_adapter: object,
    auth_secrets: AuthSecrets,
    state_keys: HostKeys,
    cursor_secret: bytes,
    alembic_head: str = "p4_host_state",
) -> HostRuntime:
    """Build the trusted builtin registry and all Host state services."""

    registry = build_builtin_registry(finance_adapter)
    idempotency = HostIdempotency(state_keys)
    events = InProcessEventBus()

    def validate_setting(module_id: str, key: str, value: dict, schema_version: int) -> None:
        manifest = registry.definition(module_id).manifest
        declared = {item.key: item.schema_version for item in manifest.settings}
        if declared.get(key) != schema_version or schema_version != manifest.settings_schema_version:
            raise HostStateError("invalid_setting", status_code=422)
        if not isinstance(value, dict):
            raise HostStateError("invalid_setting", status_code=422)

    permissions: set[str] = {"host:modules", "host:memory", "host:settings"}
    for module_id in registry.module_ids:
        permissions.update(registry.definition(module_id).manifest.permissions)

    return HostRuntime(
        sessions=sessions,
        auth=AuthService(sessions, auth_secrets),
        registry=registry,
        conversations=ConversationService(sessions, idempotency),
        memories=MemoryService(sessions, idempotency, events),
        settings=ModuleSettingService(sessions, idempotency, events, validate_setting),
        commands=HostCommandService(sessions, idempotency),
        cursor=CursorCodec(cursor_secret),
        alembic_head=alembic_head,
        owner_permissions=frozenset(permissions),
    )


__all__ = ["build_host_runtime"]
