"""Strict P4-A Host HTTP contracts."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, field_validator


class HostHttpModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BootstrapStatusResponse(HostHttpModel):
    needs_initialization: bool


class InitializeRequest(HostHttpModel):
    handle: StrictStr = Field(min_length=3, max_length=64)
    password: StrictStr = Field(min_length=12, max_length=128)


class InitializeResponse(HostHttpModel):
    initialized: Literal[True] = True
    user_id: uuid.UUID


class LoginRequest(HostHttpModel):
    handle: StrictStr = Field(min_length=1, max_length=64)
    password: StrictStr = Field(min_length=1, max_length=128)
    client_fingerprint: StrictStr = Field(min_length=1, max_length=128)
    device_name: StrictStr = Field(min_length=1, max_length=80)
    platform: Literal["windows_desktop", "api_test"]


class RefreshRequest(HostHttpModel):
    refresh_token: StrictStr = Field(min_length=40, max_length=128)


class TokenResponse(HostHttpModel):
    session_id: uuid.UUID
    device_id: uuid.UUID
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime


class PasswordChangeRequest(HostHttpModel):
    old_password: StrictStr = Field(min_length=1, max_length=128)
    new_password: StrictStr = Field(min_length=12, max_length=128)


class SuccessResponse(HostHttpModel):
    success: Literal[True] = True


class SessionResponse(HostHttpModel):
    session_id: uuid.UUID
    device_id: uuid.UUID
    device_name: str
    platform: str
    created_at: datetime
    expires_at: datetime
    current: bool


class BindingCodeRequest(HostHttpModel):
    channel: StrictStr = Field(min_length=1, max_length=32)


class BindingCodeResponse(HostHttpModel):
    code_id: uuid.UUID
    code: str
    expires_at: datetime


class BindingConsumeRequest(HostHttpModel):
    channel: StrictStr = Field(min_length=1, max_length=32)
    provider_account: StrictStr = Field(min_length=1, max_length=256)
    external_subject: StrictStr = Field(min_length=1, max_length=256)
    code: StrictStr = Field(pattern=r"^[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}$")


class BindingResponse(HostHttpModel):
    binding_id: uuid.UUID
    channel: str
    created_at: datetime


class ModuleResponse(HostHttpModel):
    module_id: str
    version: str
    display_name: str
    enabled: bool
    profile_ids: tuple[str, ...]
    api_prefixes: tuple[str, ...]
    settings_schema_version: int


class ConversationCreateRequest(HostHttpModel):
    channel: StrictStr = Field(min_length=1, max_length=32)
    module_id: StrictStr = Field(min_length=1, max_length=64)
    profile_id: StrictStr = Field(min_length=1, max_length=140)


class ConversationResponse(HostHttpModel):
    id: uuid.UUID
    channel: str
    module_id: str
    profile_id: str
    status: str
    last_message_at: datetime | None
    created_at: datetime
    replayed: bool = False


class MessageResponse(HostHttpModel):
    id: uuid.UUID
    role: str
    content: str
    sensitivity: str
    created_at: datetime


class MemoryCandidateDecisionRequest(HostHttpModel):
    target_namespace: StrictStr = Field(min_length=1, max_length=140)


class MemoryCandidateResponse(HostHttpModel):
    id: uuid.UUID
    source_namespace: str
    target_namespace: str
    kind: str
    value: dict[str, Any]
    sensitivity: str
    status: str
    expires_at: datetime


class MemoryResponse(HostHttpModel):
    id: uuid.UUID
    namespace: str
    kind: str
    value: dict[str, Any]
    sensitivity: str
    status: str
    confirmed_at: datetime


class SettingPutRequest(HostHttpModel):
    key: StrictStr = Field(min_length=1, max_length=64)
    value: dict[str, Any]
    schema_version: int = Field(ge=1)
    expected_version: int | None = Field(default=None, ge=0)


class SettingResponse(HostHttpModel):
    id: uuid.UUID
    module_id: str
    key: str
    value: dict[str, Any]
    schema_version: int
    version_id: int
    updated_at: datetime
    replayed: bool = False


class ReadyResponse(HostHttpModel):
    status: Literal["ready"] = "ready"
