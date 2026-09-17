"""Pydantic request and response contracts for the HTTP boundary."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProbeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    challenge: str = Field(min_length=1, max_length=128)

    @field_validator("challenge")
    @classmethod
    def reject_blank_challenge(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("challenge must not be blank")
        return value


class ProbeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    challenge: str
    receipt: str
    created_at: datetime
    replayed: bool


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    service: str


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    retryable: bool


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    error: ErrorDetail
