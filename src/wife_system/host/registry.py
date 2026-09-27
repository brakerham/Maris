"""Atomic validation and registration of trusted builtin Host modules."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from wife_system.host.contracts import (
    HOST_API_MAJOR,
    AgentProfile,
    ModuleManifest,
    ModuleSummary,
)
from wife_system.host.tools import CatalogTool, ToolCatalog


DEFAULT_KNOWN_PERMISSIONS = frozenset(
    {
        "finance:read",
        "finance:write",
        "host:modules",
        "host:memory",
        "host:settings",
    }
)
HOST_CORE_EVENTS = frozenset(
    {
        "agent.run_status_changed@1",
        "memory.changed@1",
        "module.setting_changed@1",
        "auth.session_revoked@1",
    }
)


class RegistryStartupError(RuntimeError):
    """Safe startup diagnostic; no manifest contents are embedded in messages."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class ModuleDefinition:
    manifest: ModuleManifest
    tools: tuple[CatalogTool, ...] = ()
    routes: tuple[str, ...] = ()
    router_factory: Callable[..., Any] | None = None
    service_factory: Callable[..., Any] | None = None
    ui_manifest_factory: Callable[..., Any] | None = None
    subscriber_handlers: tuple[tuple[str, Callable[[Any], None]], ...] = ()


class ModuleEnablement:
    """Replaceable per-user enablement store used by schema and execution gates."""

    def __init__(
        self,
        defaults: dict[str, bool],
        sessions: sessionmaker[Session] | None = None,
    ) -> None:
        self._defaults = dict(defaults)
        self._sessions = sessions
        self._overrides: dict[tuple[Any, str], bool] = {}
        self._lock = threading.RLock()

    def is_enabled(self, user_id: Any, module_id: str) -> bool:
        if self._sessions is not None:
            try:
                from wife_system.host.state_models import ModuleSettingRecord

                with self._sessions() as session:
                    row = session.scalar(
                        select(ModuleSettingRecord).where(
                            ModuleSettingRecord.user_id == user_id,
                            ModuleSettingRecord.module_id == module_id,
                            ModuleSettingRecord.key == "module_enabled",
                        )
                    )
                if row is not None:
                    value = json.loads(row.value_json)
                    if isinstance(value, dict) and isinstance(value.get("enabled"), bool):
                        return value["enabled"]
            except SQLAlchemyError as exc:
                raise RegistryStartupError(
                    "module_state_unavailable", "Module state is unavailable."
                ) from exc
        with self._lock:
            return self._overrides.get(
                (user_id, module_id), self._defaults.get(module_id, False)
            )

    def set_enabled(self, user_id: Any, module_id: str, enabled: bool) -> None:
        if module_id not in self._defaults:
            raise RegistryStartupError("module_not_found", "The module was not found.")
        if self._sessions is not None:
            from datetime import UTC, datetime
            from wife_system.host.state_models import ModuleSettingRecord

            try:
                with self._sessions() as session, session.begin():
                    row = session.scalar(
                        select(ModuleSettingRecord).where(
                            ModuleSettingRecord.user_id == user_id,
                            ModuleSettingRecord.module_id == module_id,
                            ModuleSettingRecord.key == "module_enabled",
                        )
                    )
                    encoded = json.dumps(
                        {"enabled": bool(enabled)}, separators=(",", ":"), sort_keys=True
                    )
                    if row is None:
                        session.add(
                            ModuleSettingRecord(
                                user_id=user_id,
                                module_id=module_id,
                                key="module_enabled",
                                value_json=encoded,
                                schema_version=1,
                                version_id=1,
                                updated_at=datetime.now(UTC),
                            )
                        )
                    else:
                        row.value_json = encoded
                        row.schema_version = 1
                        row.version_id += 1
                        row.updated_at = datetime.now(UTC)
                return
            except SQLAlchemyError as exc:
                raise RegistryStartupError(
                    "module_state_unavailable", "Module state is unavailable."
                ) from exc
        with self._lock:
            self._overrides[(user_id, module_id)] = enabled


class ModuleRegistry:
    """Validated registry built all-or-nothing from explicit definitions."""

    def __init__(
        self,
        definitions: tuple[ModuleDefinition, ...] | list[ModuleDefinition],
        *,
        host_api_major: int = HOST_API_MAJOR,
        known_permissions: frozenset[str] = DEFAULT_KNOWN_PERMISSIONS,
        sessions: sessionmaker[Session] | None = None,
    ) -> None:
        validated = self._validate_all(
            tuple(definitions), host_api_major, known_permissions
        )
        self._definitions = {item.manifest.module_id: item for item in validated}
        self._profiles = {
            profile.profile_id: profile
            for item in validated
            for profile in item.manifest.profiles
        }
        self._tool_catalog = ToolCatalog(
            [tool for item in validated for tool in item.tools]
        )
        self.enablement = ModuleEnablement(
            {
                item.manifest.module_id: item.manifest.enabled_by_default
                for item in validated
            },
            sessions,
        )

    @staticmethod
    def _duplicate(values: list[str]) -> bool:
        return len(values) != len(set(values))

    @classmethod
    def _validate_all(
        cls,
        definitions: tuple[ModuleDefinition, ...],
        host_api_major: int,
        known_permissions: frozenset[str],
    ) -> tuple[ModuleDefinition, ...]:
        manifests = [item.manifest for item in definitions]
        module_ids = [item.module_id for item in manifests]
        if cls._duplicate(module_ids):
            raise RegistryStartupError("duplicate_module", "A module id is duplicated.")

        for manifest in manifests:
            if manifest.host_api_major != host_api_major:
                raise RegistryStartupError(
                    "host_api_incompatible", "A module uses an incompatible Host API."
                )
            if not manifest.permissions.issubset(known_permissions):
                raise RegistryStartupError(
                    "unknown_permission", "A module declares an unknown permission."
                )

        cls._reject_duplicates(
            "duplicate_profile",
            [profile.profile_id for manifest in manifests for profile in manifest.profiles],
            "An Agent Profile id is duplicated.",
        )
        cls._reject_duplicates(
            "duplicate_tool",
            [tool.canonical_id for manifest in manifests for tool in manifest.tools],
            "A canonical tool id is duplicated.",
        )
        cls._reject_duplicates(
            "duplicate_tool_alias",
            [tool.alias for manifest in manifests for tool in manifest.tools],
            "A tool alias is duplicated.",
        )
        api_prefixes = [
            prefix for manifest in manifests for prefix in manifest.api_prefixes
        ]
        cls._reject_duplicates(
            "duplicate_api_prefix", api_prefixes, "An API prefix is duplicated."
        )
        for index, left in enumerate(api_prefixes):
            for right in api_prefixes[index + 1 :]:
                if left.startswith(f"{right}/") or right.startswith(f"{left}/"):
                    raise RegistryStartupError(
                        "duplicate_api_prefix", "API prefixes overlap."
                    )
        cls._reject_duplicates(
            "duplicate_memory_namespace",
            [
                namespace
                for manifest in manifests
                for namespace in manifest.memory_namespaces
                if namespace != "shared.confirmed"
            ],
            "A module memory namespace is duplicated.",
        )
        cls._reject_duplicates(
            "duplicate_route",
            [route for item in definitions for route in item.routes],
            "A route is duplicated.",
        )
        setting_ids = [
            f"{manifest.module_id}.{setting.key}"
            for manifest in manifests
            for setting in manifest.settings
        ]
        cls._reject_duplicates(
            "duplicate_setting_key", setting_ids, "A module setting key is duplicated."
        )

        declared_tools = {
            tool.canonical_id: tool for manifest in manifests for tool in manifest.tools
        }
        runtime_tools: dict[str, CatalogTool] = {}
        for definition in definitions:
            local_manifest_ids = {
                tool.canonical_id for tool in definition.manifest.tools
            }
            local_runtime_ids = {tool.contract.canonical_id for tool in definition.tools}
            if local_manifest_ids != local_runtime_ids:
                raise RegistryStartupError(
                    "tool_definition_mismatch",
                    "A module's runtime tools do not match its manifest.",
                )
            for tool in definition.tools:
                if tool.module_id != definition.manifest.module_id:
                    raise RegistryStartupError(
                        "tool_definition_mismatch",
                        "A runtime tool belongs to another module.",
                    )
                if declared_tools[tool.contract.canonical_id] != tool.contract:
                    raise RegistryStartupError(
                        "tool_definition_mismatch",
                        "A runtime tool differs from its manifest contract.",
                    )
                runtime_tools[tool.contract.canonical_id] = tool

        for manifest in manifests:
            for profile in manifest.profiles:
                if not set(profile.tool_grants).issubset(runtime_tools):
                    raise RegistryStartupError(
                        "unknown_tool_grant", "A Profile grants an unknown tool."
                    )

        published = set(HOST_CORE_EVENTS)
        published.update(event for manifest in manifests for event in manifest.published_events)
        for manifest in manifests:
            if not set(manifest.subscribed_events).issubset(published):
                raise RegistryStartupError(
                    "unresolved_event_subscription",
                    "A subscribed event has no registered publisher.",
                )
        for definition in definitions:
            handler_events = [event for event, _ in definition.subscriber_handlers]
            if len(handler_events) != len(set(handler_events)):
                raise RegistryStartupError(
                    "duplicate_event_subscription", "An event handler is duplicated."
                )
            if set(handler_events) != set(definition.manifest.subscribed_events):
                raise RegistryStartupError(
                    "event_handler_mismatch", "Subscriber handlers do not match the manifest."
                )
        return definitions

    @classmethod
    def _reject_duplicates(
        cls, code: str, values: list[str], message: str
    ) -> None:
        if cls._duplicate(values):
            raise RegistryStartupError(code, message)

    @property
    def tool_catalog(self) -> ToolCatalog:
        return self._tool_catalog

    @property
    def module_ids(self) -> tuple[str, ...]:
        return tuple(self._definitions)

    def definition(self, module_id: str) -> ModuleDefinition:
        try:
            return self._definitions[module_id]
        except KeyError as exc:
            raise RegistryStartupError("module_not_found", "The module was not found.") from exc

    def resolve_profile(self, user_id: Any, profile_id: str) -> AgentProfile:
        profile = self._profiles.get(profile_id)
        if profile is None:
            raise RegistryStartupError("profile_not_found", "The Profile was not found.")
        if not self.enablement.is_enabled(user_id, profile.module_id):
            raise RegistryStartupError("module_disabled", "The module is disabled.")
        return profile

    def set_enabled(self, user_id: Any, module_id: str, enabled: bool) -> None:
        self.enablement.set_enabled(user_id, module_id, enabled)

    def summaries(
        self, user_id: Any, permissions: frozenset[str]
    ) -> tuple[ModuleSummary, ...]:
        result: list[ModuleSummary] = []
        for definition in self._definitions.values():
            manifest = definition.manifest
            enabled = self.enablement.is_enabled(user_id, manifest.module_id)
            if not enabled:
                continue
            if manifest.permissions and manifest.permissions.isdisjoint(permissions):
                continue
            result.append(
                ModuleSummary(
                    module_id=manifest.module_id,
                    version=manifest.version,
                    display_name=manifest.display_name,
                    enabled=True,
                    profile_ids=tuple(profile.profile_id for profile in manifest.profiles),
                    api_prefixes=manifest.api_prefixes,
                    settings_schema_version=manifest.settings_schema_version,
                )
            )
        return tuple(result)
