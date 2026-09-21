"""Trusted Host identity and run contexts.

These values are constructed by authenticated adapters and never exposed as
model-controlled tool arguments.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class PrincipalContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: uuid.UUID
    session_id: uuid.UUID | None
    device_id: uuid.UUID | None
    channel: str
    permissions: frozenset[str]
    authenticated_at: datetime

    @field_validator("authenticated_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("authenticated_at must include a timezone")
        return value


class HostRunContext(PrincipalContext):
    agent_run_id: uuid.UUID
    conversation_id: uuid.UUID
    module_id: str
    profile_id: str
    source_system: str
    source_event_id: str | None
    received_at: datetime
    pending_action_id: uuid.UUID | None = None
    approval_grant_id: uuid.UUID | None = None

    @field_validator("received_at")
    @classmethod
    def require_aware_received_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("received_at must include a timezone")
        return value
