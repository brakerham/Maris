"""Trusted execution context kept outside model-controlled tool arguments."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RunContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    agent_run_id: uuid.UUID
    actor_id: uuid.UUID
    conversation_id: uuid.UUID
    source_system: Literal["desktop_chat", "wechat_openclaw"]
    source_event_id: str | None = None
    received_at: datetime
    permissions: frozenset[str]
    pending_action_id: uuid.UUID | None = None
    approval_grant_id: uuid.UUID | None = None
    user_message: str | None = Field(default=None, exclude=True)

    @field_validator("received_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("received_at must include a timezone")
        return value


ToolExecutionContext = RunContext
