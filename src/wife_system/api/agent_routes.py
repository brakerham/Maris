"""Thin FastAPI boundary for the persistent P2 Agent application."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, ConfigDict

from wife_system.agent.application import AgentApplication
from wife_system.api.agent_schemas import (
    AgentRunResponse as LegacyAgentRunResponse,
    CreateAgentRunRequest,
    ResumeAgentRunRequest,
)


class AgentRunResponse(LegacyAgentRunResponse):
    status: Literal["running", "success", "error", "paused", "cancelled"]


class AgentIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    actor_id: uuid.UUID
    user_id: uuid.UUID | None = None
    permissions: frozenset[str]
    session_id: uuid.UUID | None = None
    device_id: uuid.UUID | None = None
    channel: str = "desktop_chat"
    authenticated_at: datetime | None = None


def get_agent_application(request: Request) -> AgentApplication:
    from wife_system.agent.application import AgentApplicationError

    application = getattr(request.app.state, "agent_application", None)
    if application is None:
        raise AgentApplicationError("agent_unavailable", status_code=503, retryable=True)
    return application


def get_agent_identity(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> AgentIdentity:
    runtime = getattr(request.app.state, "host_runtime", None)
    if runtime is None:
        return request.app.state.agent_identity
    from wife_system.host.auth.errors import AuthError

    if authorization is None or not authorization.startswith("Bearer "):
        raise AuthError("authentication_required")
    authenticated = runtime.auth.authenticate_access(authorization[7:], now=datetime.now(UTC))
    channel = {
        "windows_desktop": "desktop_chat",
        "api_test": "api_test",
    }.get(authenticated.platform)
    if channel is None:
        raise AuthError("invalid_channel")
    return AgentIdentity(
        actor_id=authenticated.user_id,
        user_id=authenticated.user_id,
        permissions=runtime.owner_permissions,
        session_id=authenticated.session_id,
        device_id=authenticated.device_id,
        channel=channel,
        authenticated_at=authenticated.authenticated_at,
    )


router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/runs", response_model=AgentRunResponse)
def create_agent_run(
    request: Request,
    payload: CreateAgentRunRequest,
    identity: Annotated[AgentIdentity, Depends(get_agent_identity)],
    application: Annotated[AgentApplication, Depends(get_agent_application)],
) -> AgentRunResponse:
    user_id = identity.user_id or identity.actor_id
    runtime = getattr(request.app.state, "host_runtime", None)
    module_id = "daily_finance"
    profile_id = "daily_finance.assistant@1"
    if runtime is not None:
        conversation = runtime.conversations.get(payload.conversation_id, user_id=user_id)
        runtime.registry.resolve_profile(user_id, conversation.profile_id)
        module_id, profile_id = conversation.module_id, conversation.profile_id
    result = application.start(
        actor_id=identity.actor_id,
        user_id=user_id,
        conversation_id=payload.conversation_id,
        client_event_id=payload.client_event_id,
        message=payload.message,
        permissions=identity.permissions,
        module_id=module_id,
        profile_id=profile_id,
        session_id=identity.session_id,
        device_id=identity.device_id,
        channel=identity.channel,
        authenticated_at=identity.authenticated_at,
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
        user_id=identity.user_id or identity.actor_id,
        conversation_id=payload.conversation_id,
        action=payload.action,
        permissions=identity.permissions,
        confirmation_code=payload.confirmation_code,
        values=None if payload.values is None else payload.values.model_dump(exclude_none=True, mode="json"),
        session_id=identity.session_id,
        device_id=identity.device_id,
        channel=identity.channel,
        authenticated_at=identity.authenticated_at,
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
        user_id=identity.user_id or identity.actor_id,
        conversation_id=conversation_id,
    )
    return AgentRunResponse.model_validate(result.model_dump())
