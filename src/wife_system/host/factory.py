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
    agent_provider_ready: bool = True,
) -> HostRuntime:
    """Build the trusted builtin registry and all Host state services."""

    registry = build_builtin_registry(finance_adapter, sessions=sessions)
    idempotency = HostIdempotency(state_keys)
    events = InProcessEventBus()

    def validate_memory_grant(
        user_id,
        profile_id: str,
        source_namespace: str,
        target_namespace: str,
        kind: str,
        operation: str,
        expected_profile_version: str | None,
    ) -> str:
        try:
            profile = registry.resolve_profile(user_id, profile_id)
        except RegistryStartupError as exc:
            if expected_profile_version is not None:
                raise HostStateError("memory_candidate_conflict") from exc
            raise HostStateError("memory_namespace_forbidden", status_code=403) from exc
        source_module = source_namespace.split(".", 1)[0]
        grant = next(
            (item for item in profile.memory_grants if item.namespace == target_namespace),
            None,
        )
        valid = (
            profile.module_id == source_module
            and grant is not None
            and kind in grant.kinds
            and operation in grant.operations
            and (
                expected_profile_version is None
                or profile.version == expected_profile_version
            )
        )
        if not valid and expected_profile_version is not None:
            raise HostStateError("memory_candidate_conflict")
        if not valid:
            raise HostStateError("memory_namespace_forbidden", status_code=403)
        return profile.version

    def validate_setting(module_id: str, key: str, value: dict, schema_version: int) -> None:
        manifest = registry.definition(module_id).manifest
        declared = {item.key: item.schema_version for item in manifest.settings}
        if declared.get(key) != schema_version or schema_version != manifest.settings_schema_version:
            raise HostStateError("invalid_setting", status_code=422)
        if not isinstance(value, dict):
            raise HostStateError("invalid_setting", status_code=422)
        if key == "module_enabled" and (
            set(value) != {"enabled"} or not isinstance(value["enabled"], bool)
        ):
            raise HostStateError("invalid_setting", status_code=422)

    permissions: set[str] = {"host:modules", "host:memory", "host:settings"}
    for module_id in registry.module_ids:
        permissions.update(registry.definition(module_id).manifest.permissions)
        definition = registry.definition(module_id)
        for event_type, handler in definition.subscriber_handlers:
            events.subscribe(event_type, handler)

    return HostRuntime(
        sessions=sessions,
        auth=AuthService(sessions, auth_secrets),
        registry=registry,
        conversations=ConversationService(sessions, idempotency),
        memories=MemoryService(sessions, idempotency, events, validate_memory_grant),
        settings=ModuleSettingService(sessions, idempotency, events, validate_setting),
        commands=HostCommandService(sessions, idempotency),
        cursor=CursorCodec(cursor_secret),
        alembic_head=alembic_head,
        owner_permissions=frozenset(permissions),
        events=events,
        agent_provider_ready=agent_provider_ready,
    )


__all__ = ["build_host_runtime"]
