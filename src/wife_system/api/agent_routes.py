"""Thin FastAPI boundary for the persistent P2 Agent application."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict

from wife_system.agent.application import AgentApplication
from wife_system.api.agent_schemas import (
    AgentRunResponse,
    CreateAgentRunRequest,
    ResumeAgentRunRequest,
)


class AgentIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    actor_id: uuid.UUID
    permissions: frozenset[str]


def get_agent_application(request: Request) -> AgentApplication:
    from wife_system.agent.application import AgentApplicationError

    application = getattr(request.app.state, "agent_application", None)
    if application is None:
        raise AgentApplicationError("agent_unavailable", status_code=503, retryable=True)
    return application


def get_agent_identity(request: Request) -> AgentIdentity:
    return request.app.state.agent_identity


router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/runs", response_model=AgentRunResponse)
def create_agent_run(
    payload: CreateAgentRunRequest,
    identity: Annotated[AgentIdentity, Depends(get_agent_identity)],
    application: Annotated[AgentApplication, Depends(get_agent_application)],
) -> AgentRunResponse:
    result = application.start(
        actor_id=identity.actor_id,
        conversation_id=payload.conversation_id,
        client_event_id=payload.client_event_id,
        message=payload.message,
        permissions=identity.permissions,
    )
    return AgentRunResponse.model_validate(result.model_dump())


@router.post("/runs/{run_id}/resume", response_model=AgentRunResponse)
def resume_agent_run(
    run_id: uuid.UUID,
    payload: ResumeAgentRunRequest,
    identity: Annotated[AgentIdentity, Depends(get_agent_identity)],
    application: Annotated[AgentApplication, Depends(get_agent_application)],
) -> AgentRunResponse:
    result = application.resume(
        run_id,
        actor_id=identity.actor_id,
        conversation_id=payload.conversation_id,
        action=payload.action,
        permissions=identity.permissions,
        confirmation_code=payload.confirmation_code,
        values=None if payload.values is None else payload.values.model_dump(exclude_none=True, mode="json"),
    )
    return AgentRunResponse.model_validate(result.model_dump())


@router.get("/runs/{run_id}", response_model=AgentRunResponse)
def get_agent_run(
    run_id: uuid.UUID,
    conversation_id: uuid.UUID,
    identity: Annotated[AgentIdentity, Depends(get_agent_identity)],
    application: Annotated[AgentApplication, Depends(get_agent_application)],
) -> AgentRunResponse:
    result = application.get(
        run_id,
        actor_id=identity.actor_id,
        conversation_id=conversation_id,
    )
    return AgentRunResponse.model_validate(result.model_dump())
