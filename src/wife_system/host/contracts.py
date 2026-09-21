"""Serializable contracts for trusted P4 Host modules.

Runtime callables deliberately live in :mod:`wife_system.host.tools`; every
model in this module is safe to validate and serialize as data.
"""

from __future__ import annotations

import re
import json
import math
import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator,
    model_validator,
)


HOST_API_MAJOR = 1
MAX_MODEL_TURNS = 4
MAX_TOOL_CALLS = 8
MAX_WRITE_CALLS = 1
MAX_PROVIDER_TIMEOUT_SECONDS = 15
MAX_TOOL_TIMEOUT_SECONDS = 10
MAX_PROVIDER_RETRIES = 1
MAX_MEMORY_ITEMS = 8

LOCAL_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$", re.ASCII)
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$", re.ASCII
)
CANONICAL_ID_PATTERN = re.compile(
    r"^(?P<module>[a-z][a-z0-9_]{0,63})\."
    r"(?P<local>[a-z][a-z0-9_]{0,63})@(?P<major>0|[1-9][0-9]*)$",
    re.ASCII,
)
PERMISSION_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]{0,63}:[a-z][a-z0-9_]{0,63}$", re.ASCII
)
API_PREFIX_PATTERN = re.compile(
    r"^/api/v1/[a-z][a-z0-9_-]*(?:/[a-z][a-z0-9_-]*)*$", re.ASCII
)

MEMORY_KINDS = frozenset(
    {"preference", "constraint", "goal", "communication_style"}
)
MEMORY_SENSITIVITIES = frozenset({"private", "restricted"})
EVENT_TYPES = frozenset(
    {
        "agent.run_status_changed@1",
        "memory.changed@1",
        "module.setting_changed@1",
        "auth.session_revoked@1",
    }
)
STOP_CODES = frozenset(
    {
        "max_model_turns_exceeded",
        "tool_limit_exceeded",
        "write_limit_exceeded",
        "model_timeout",
        "tool_timeout",
        "cancelled",
        "tool_not_allowed",
    }
)


def _require_exact_ascii(value: str, pattern: re.Pattern[str], label: str) -> str:
    if not value.isascii() or pattern.fullmatch(value) is None:
        raise ValueError(f"invalid {label}")
    return value


def validate_local_name(value: str) -> str:
    return _require_exact_ascii(value, LOCAL_NAME_PATTERN, "local name")


def validate_semver(value: str) -> str:
    return _require_exact_ascii(value, SEMVER_PATTERN, "semantic version")


def canonical_parts(value: str) -> tuple[str, str, int]:
    if not value.isascii():
        raise ValueError("invalid canonical id")
    matched = CANONICAL_ID_PATTERN.fullmatch(value)
    if matched is None:
        raise ValueError("invalid canonical id")
    return matched["module"], matched["local"], int(matched["major"])


class StrictContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ProfileLimits(StrictContract):
    max_model_turns: int = Field(default=MAX_MODEL_TURNS, ge=1, le=MAX_MODEL_TURNS)
    max_tool_calls: int = Field(default=MAX_TOOL_CALLS, ge=1, le=MAX_TOOL_CALLS)
    max_write_calls: int = Field(default=MAX_WRITE_CALLS, ge=0, le=MAX_WRITE_CALLS)
    provider_timeout_seconds: int = Field(
        default=MAX_PROVIDER_TIMEOUT_SECONDS,
        ge=1,
        le=MAX_PROVIDER_TIMEOUT_SECONDS,
    )
    tool_timeout_seconds: int = Field(
        default=MAX_TOOL_TIMEOUT_SECONDS,
        ge=1,
        le=MAX_TOOL_TIMEOUT_SECONDS,
    )
    retryable_provider_retries: int = Field(
        default=MAX_PROVIDER_RETRIES,
        ge=0,
        le=MAX_PROVIDER_RETRIES,
    )


class MemoryGrant(StrictContract):
    namespace: str
    kinds: frozenset[Literal[
        "preference", "constraint", "goal", "communication_style"
    ]] = Field(default_factory=lambda: frozenset(MEMORY_KINDS))
    limit: int = Field(default=MAX_MEMORY_ITEMS, ge=0, le=MAX_MEMORY_ITEMS)

    @field_validator("namespace")
    @classmethod
    def valid_namespace(cls, value: str) -> str:
        if value == "shared.confirmed":
            return value
        pieces = value.split(".")
        if len(pieces) != 2 or pieces[1] not in {"confirmed", "candidates"}:
            raise ValueError("invalid memory namespace")
        validate_local_name(pieces[0])
        return value


class ToolContract(StrictContract):
    canonical_id: str
    alias: str
    description: str = Field(min_length=1, max_length=500)
    required_permission: str
    is_write: bool = False

    @field_validator("canonical_id")
    @classmethod
    def valid_canonical_id(cls, value: str) -> str:
        canonical_parts(value)
        return value

    @field_validator("alias")
    @classmethod
    def valid_alias(cls, value: str) -> str:
        return validate_local_name(value)

    @field_validator("required_permission")
    @classmethod
    def valid_permission(cls, value: str) -> str:
        return _require_exact_ascii(value, PERMISSION_PATTERN, "permission")


class ToolProvenance(StrictContract):
    canonical_tool_id: str
    module_id: str
    profile_id: str

    @field_validator("canonical_tool_id", "profile_id")
    @classmethod
    def valid_canonical_ids(cls, value: str) -> str:
        canonical_parts(value)
        return value

    @field_validator("module_id")
    @classmethod
    def valid_module_id(cls, value: str) -> str:
        return validate_local_name(value)


class ToolSafeError(StrictContract):
    code: str
    message: str = Field(min_length=1, max_length=500)
    retryable: bool

    @field_validator("code")
    @classmethod
    def valid_code(cls, value: str) -> str:
        return validate_local_name(value)


class ToolOk(StrictContract):
    status: Literal["ok"] = "ok"
    data: dict[str, Any]
    provenance: ToolProvenance


class ToolNeedsInput(StrictContract):
    status: Literal["needs_input"] = "needs_input"
    pending_action_id: uuid.UUID
    missing_fields: tuple[str, ...]
    question_code: str
    choices: tuple[dict[str, str], ...] = ()
    provenance: ToolProvenance

    @field_validator("missing_fields")
    @classmethod
    def valid_missing_fields(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        for value in values:
            validate_local_name(value)
        return values

    @field_validator("question_code")
    @classmethod
    def valid_question_code(cls, value: str) -> str:
        return validate_local_name(value)


class ToolNeedsConfirmation(StrictContract):
    status: Literal["needs_confirmation"] = "needs_confirmation"
    pending_action_id: uuid.UUID
    confirmation_code: str = Field(min_length=1, max_length=64)
    summary: dict[str, str]
    provenance: ToolProvenance


class ToolFailed(StrictContract):
    status: Literal["error"] = "error"
    error: ToolSafeError
    provenance: ToolProvenance


ToolResultValue = Annotated[
    ToolOk | ToolNeedsInput | ToolNeedsConfirmation | ToolFailed,
    Field(discriminator="status"),
]


class ToolExecutionResult(RootModel[ToolResultValue]):
    """Strict discriminated output envelope exposed to the model loop."""


class SettingContract(StrictContract):
    key: str
    schema_version: int = Field(ge=1)

    @field_validator("key")
    @classmethod
    def valid_key(cls, value: str) -> str:
        return validate_local_name(value)


class AgentProfile(StrictContract):
    profile_id: str
    module_id: str
    version: str
    display_name: str = Field(min_length=1, max_length=120)
    system_prompt: str = Field(min_length=1, max_length=32_768)
    tool_grants: tuple[str, ...]
    memory_grants: tuple[MemoryGrant, ...] = ()
    limits: ProfileLimits = Field(default_factory=ProfileLimits)

    @field_validator("profile_id")
    @classmethod
    def valid_profile_id(cls, value: str) -> str:
        canonical_parts(value)
        return value

    @field_validator("module_id")
    @classmethod
    def valid_module_id(cls, value: str) -> str:
        return validate_local_name(value)

    @field_validator("version")
    @classmethod
    def valid_version(cls, value: str) -> str:
        return validate_semver(value)

    @field_validator("tool_grants")
    @classmethod
    def valid_tool_grants(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        for value in values:
            canonical_parts(value)
        if len(values) != len(set(values)):
            raise ValueError("duplicate profile tool grant")
        return values

    @model_validator(mode="after")
    def ids_match_module_and_version(self) -> "AgentProfile":
        module_id, _, major = canonical_parts(self.profile_id)
        if module_id != self.module_id or major != int(self.version.split(".", 1)[0]):
            raise ValueError("profile id must match its module and version major")
        namespaces = [grant.namespace for grant in self.memory_grants]
        if len(namespaces) != len(set(namespaces)):
            raise ValueError("duplicate profile memory grant")
        return self


class ModuleManifest(StrictContract):
    module_id: str
    version: str
    host_api_major: int
    display_name: str = Field(min_length=1, max_length=120)
    enabled_by_default: bool
    profiles: tuple[AgentProfile, ...]
    tools: tuple[ToolContract, ...]
    permissions: frozenset[str]
    api_prefixes: tuple[str, ...]
    memory_namespaces: tuple[str, ...]
    settings_schema_version: int = Field(ge=1)
    settings: tuple[SettingContract, ...] = ()
    published_events: tuple[str, ...] = ()
    subscribed_events: tuple[str, ...] = ()
    migration_owner: str

    @field_validator("module_id", "migration_owner")
    @classmethod
    def valid_local_names(cls, value: str) -> str:
        return validate_local_name(value)

    @field_validator("version")
    @classmethod
    def valid_version(cls, value: str) -> str:
        return validate_semver(value)

    @field_validator("permissions")
    @classmethod
    def valid_permissions(cls, values: frozenset[str]) -> frozenset[str]:
        for value in values:
            _require_exact_ascii(value, PERMISSION_PATTERN, "permission")
        return values

    @field_validator("api_prefixes")
    @classmethod
    def valid_api_prefixes(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        for value in values:
            _require_exact_ascii(value, API_PREFIX_PATTERN, "api prefix")
        return values

    @field_validator("memory_namespaces")
    @classmethod
    def valid_memory_namespaces(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        for value in values:
            MemoryGrant(namespace=value)
        return values

    @field_validator("published_events", "subscribed_events")
    @classmethod
    def valid_events(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(value not in EVENT_TYPES for value in values):
            raise ValueError("unknown event type")
        return values

    @model_validator(mode="after")
    def validate_internal_ownership(self) -> "ModuleManifest":
        major = int(self.version.split(".", 1)[0])
        if self.migration_owner != self.module_id:
            raise ValueError("migration owner must equal module id")
        for profile in self.profiles:
            if profile.module_id != self.module_id:
                raise ValueError("profile belongs to another module")
        for tool in self.tools:
            module_id, _, tool_major = canonical_parts(tool.canonical_id)
            if module_id != self.module_id or tool_major != major:
                raise ValueError("tool id must match its module and version major")
            if tool.required_permission not in self.permissions:
                raise ValueError("tool permission must be declared by its module")
        allowed_namespaces = set(self.memory_namespaces) | {"shared.confirmed"}
        for namespace in self.memory_namespaces:
            if namespace != "shared.confirmed" and not namespace.startswith(
                f"{self.module_id}."
            ):
                raise ValueError("memory namespace belongs to another module")
        for profile in self.profiles:
            for grant in profile.memory_grants:
                if grant.namespace not in allowed_namespaces:
                    raise ValueError("profile grants an undeclared memory namespace")
        return self


class ModuleSummary(StrictContract):
    module_id: str
    version: str
    display_name: str
    enabled: bool
    profile_ids: tuple[str, ...]
    api_prefixes: tuple[str, ...]
    settings_schema_version: int


class EventEnvelope(StrictContract):
    event_id: uuid.UUID
    event_type: str
    version: Literal[1] = 1
    occurred_at: datetime
    user_id: uuid.UUID
    producer_module: str
    correlation_id: str = Field(min_length=1, max_length=128)
    idempotency_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    sensitivity: Literal["private", "restricted"]
    payload: dict[str, Any]

    @field_validator("event_type")
    @classmethod
    def valid_event_type(cls, value: str) -> str:
        if value not in EVENT_TYPES:
            raise ValueError("unknown event type")
        return value

    @field_validator("producer_module")
    @classmethod
    def valid_producer(cls, value: str) -> str:
        return validate_local_name(value)

    @field_validator("occurred_at")
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone")
        return value


class ModuleSettingValue(StrictContract):
    module_id: str
    key: str
    schema_version: int = Field(ge=1)
    version_id: int = Field(ge=1)
    value: dict[str, Any]

    @field_validator("module_id", "key")
    @classmethod
    def valid_names(cls, value: str) -> str:
        return validate_local_name(value)

    @field_validator("value")
    @classmethod
    def bounded_canonical_json(cls, value: dict[str, Any]) -> dict[str, Any]:
        def reject_unsafe(item: Any) -> None:
            if isinstance(item, float) and not math.isfinite(item):
                raise ValueError("setting value must be finite JSON")
            if isinstance(item, dict):
                for key, nested in item.items():
                    if not isinstance(key, str):
                        raise ValueError("setting object keys must be strings")
                    if key.casefold() in {"api_key", "password", "secret", "token"}:
                        raise ValueError("secret values are not module settings")
                    reject_unsafe(nested)
            elif isinstance(item, (list, tuple)):
                for nested in item:
                    reject_unsafe(nested)

        reject_unsafe(value)
        try:
            encoded = json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise ValueError("setting value must be canonical JSON") from exc
        if len(encoded) > 8 * 1024:
            raise ValueError("setting value exceeds 8 KiB")
        return value
