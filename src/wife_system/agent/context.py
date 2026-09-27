"""Trusted execution context kept outside model-controlled tool arguments."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RunContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    agent_run_id: uuid.UUID
    actor_id: uuid.UUID
    user_id: uuid.UUID | None = None
    conversation_id: uuid.UUID
    source_system: Literal["desktop_chat", "wechat_openclaw", "api_test"]
    source_event_id: str | None = None
    received_at: datetime
    permissions: frozenset[str]
    pending_action_id: uuid.UUID | None = None
    approval_grant_id: uuid.UUID | None = None
    module_id: str = "daily_finance"
    profile_id: str = "daily_finance.assistant@1"
    user_message: str | None = Field(default=None, exclude=True)
    session_id: uuid.UUID | None = None
    device_id: uuid.UUID | None = None
    channel: str = "desktop_chat"
    attempt_no: int = Field(default=1, ge=1, le=3)
    tool_deadline_monotonic: float | None = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def normalize_scope(self) -> "RunContext":
        """Keep legacy actor-only callers while making the trusted scope explicit."""
        if self.user_id is None:
            object.__setattr__(self, "user_id", self.actor_id)
        elif self.user_id != self.actor_id:
            raise ValueError("user_id must equal actor_id")
        return self

    @field_validator("received_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("received_at must include a timezone")
        return value


ToolExecutionContext = RunContext
