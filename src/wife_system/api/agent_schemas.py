"""Strict HTTP contracts for P2 Agent run, resume, and status."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator


class AgentHttpModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateAgentRunRequest(AgentHttpModel):
    client_event_id: uuid.UUID
    conversation_id: uuid.UUID
    message: Annotated[StrictStr, Field(min_length=1, max_length=4000)]

    @field_validator("message")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value


class ResumeExpenseValues(AgentHttpModel):
    record_intent: Literal["record"] | None = None
    amount: Annotated[StrictStr, Field(min_length=1, max_length=32)] | None = None
    account_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    occurred_at: datetime | None = None

    @field_validator("occurred_at")
    @classmethod
    def aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("occurred_at must include a timezone")
        return value


class ResumeAgentRunRequest(AgentHttpModel):
    conversation_id: uuid.UUID
    action: Literal["confirm", "cancel", "provide_input"]
    confirmation_code: Annotated[StrictStr, Field(min_length=1, max_length=16)] | None = None
    values: ResumeExpenseValues | None = None


class AgentRunResponse(AgentHttpModel):
    run_id: uuid.UUID
    status: Literal["running", "success", "error", "paused"]
    replayed: bool
    answer: str | None
    error_code: str | None
    pending_action_id: uuid.UUID | None
    pause_reason: str | None
    result: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
