"""P4-A Host authentication and state HTTP endpoints."""

from __future__ import annotations

import json
import hashlib
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request

from wife_system.api.host_schemas import (
    BindingCodeRequest,
    BindingCodeResponse,
    BindingConsumeRequest,
    BindingResponse,
    BootstrapStatusResponse,
    ConversationCreateRequest,
    ConversationResponse,
    InitializeRequest,
    InitializeResponse,
    LoginRequest,
    MemoryCandidateDecisionRequest,
    MemoryCandidateResponse,
    MemoryResponse,
    MessageResponse,
    ModuleResponse,
    PasswordChangeRequest,
    Page,
    ReadyResponse,
    RefreshRequest,
    SessionResponse,
    SettingPutRequest,
    SettingResponse,
    SuccessResponse,
    TokenResponse,
)
from wife_system.host.auth.errors import AuthError
from wife_system.host.auth.service import AuthenticatedSession, SessionTokens
from wife_system.host.context import PrincipalContext
from wife_system.host.cursor import InvalidCursorError
from wife_system.host.events import EventEnvelope
from wife_system.host.registry import RegistryStartupError
from wife_system.host.runtime import HostRuntime
from wife_system.host.state import CommandOutcome, HostStateError
from wife_system.finance.models import BOOTSTRAP_USER_ID


router = APIRouter(tags=["host"])


def _publish_session_revoked(
    runtime: HostRuntime,
    authenticated: AuthenticatedSession,
    session_id: uuid.UUID,
    reason: str,
    occurred_at: datetime,
) -> None:
    digest = hashlib.sha256(f"{session_id}:{reason}".encode()).hexdigest()
    runtime.events.publish(
        EventEnvelope(
            event_id=uuid.uuid4(),
            event_type="auth.session_revoked@1",
            occurred_at=occurred_at,
            user_id=authenticated.user_id,
            producer_module="host_core",
            correlation_id=str(uuid.uuid4()),
            idempotency_digest=digest,
            sensitivity="private",
            payload={"session_id": str(session_id), "reason": reason},
        )
    )


def get_host_runtime(request: Request) -> HostRuntime:
    runtime = getattr(request.app.state, "host_runtime", None)
    if runtime is None:
        raise HostStateError("backend_not_ready", status_code=503, retryable=True)
    return runtime


def require_host_idempotency_key(
    value: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
) -> str:
    normalized = value.strip()
    if not normalized or any(ord(char) < 32 or ord(char) > 126 for char in normalized):
        raise HostStateError("invalid_request", status_code=422)
    return normalized


def bearer_token(authorization: Annotated[str | None, Header()] = None) -> str:
    if authorization is None or not authorization.startswith("Bearer "):
        raise AuthError("authentication_required")
    token = authorization[7:]
    if not token or token != token.strip():
        raise AuthError("authentication_required")
    return token


def get_authenticated_session(
    token: Annotated[str, Depends(bearer_token)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> AuthenticatedSession:
    return runtime.auth.authenticate_access(token, now=datetime.now(UTC))


def get_principal(
    authenticated: Annotated[AuthenticatedSession, Depends(get_authenticated_session)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> PrincipalContext:
    channels = {"windows_desktop": "desktop_chat", "api_test": "api_test"}
    channel = channels.get(authenticated.platform)
    if channel is None:
        raise AuthError("invalid_device")
    return PrincipalContext(
        user_id=authenticated.user_id,
        session_id=authenticated.session_id,
        device_id=authenticated.device_id,
        channel=channel,
        permissions=runtime.owner_permissions,
        authenticated_at=authenticated.authenticated_at,
    )


def _tokens(value: SessionTokens) -> TokenResponse:
    return TokenResponse(**value.__dict__)


@router.get("/api/v1/auth/bootstrap-status", response_model=BootstrapStatusResponse)
def bootstrap_status(
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> BootstrapStatusResponse:
    return BootstrapStatusResponse(needs_initialization=runtime.auth.bootstrap_status())


@router.post("/api/v1/auth/initialize", response_model=InitializeResponse)
def initialize(
    request: Request,
    payload: InitializeRequest,
    idempotency_key: Annotated[str, Depends(require_host_idempotency_key)],
    bootstrap_token: Annotated[str, Header(alias="X-Bootstrap-Token")],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> InitializeResponse:
    now = datetime.now(UTC)
    normalized_handle = runtime.auth.validate_initialize_gate(
        handle=payload.handle,
        password=payload.password,
        bootstrap_token=bootstrap_token.encode("utf-8"),
        client_host=request.client.host if request.client is not None else "",
    )
    result, _ = runtime.commands.execute(
        user_id=BOOTSTRAP_USER_ID,
        operation="auth.initialize",
        idempotency_key=idempotency_key,
        payload=payload.model_dump(mode="json"),
        now=now,
        command=lambda session: {
            "user_id": str(
                runtime.auth.initialize_in_session(
                    session,
                    normalized_handle=normalized_handle,
                    password=payload.password,
                    now=now,
                )
            )
        },
    )
    return InitializeResponse(user_id=uuid.UUID(result["user_id"]))


@router.post("/api/v1/auth/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> TokenResponse:
    return _tokens(
        runtime.auth.login(
            handle=payload.handle,
            password=payload.password,
            client_fingerprint=payload.client_fingerprint,
            device_name=payload.device_name,
            platform=payload.platform,
            now=datetime.now(UTC),
        )
    )


@router.post("/api/v1/auth/refresh", response_model=TokenResponse)
def refresh(
    payload: RefreshRequest,
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> TokenResponse:
    return _tokens(runtime.auth.refresh(payload.refresh_token, now=datetime.now(UTC)))


@router.post("/api/v1/auth/logout", response_model=SuccessResponse)
def logout(
    token: Annotated[str, Depends(bearer_token)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> SuccessResponse:
    now = datetime.now(UTC)
    authenticated = runtime.auth.authenticate_access(token, now=now)
    runtime.auth.logout(token, now=now)
    _publish_session_revoked(runtime, authenticated, authenticated.session_id, "logout", now)
    return SuccessResponse()


@router.post("/api/v1/auth/password/change", response_model=TokenResponse)
def change_password(
    payload: PasswordChangeRequest,
    token: Annotated[str, Depends(bearer_token)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> TokenResponse:
    now = datetime.now(UTC)
    authenticated = runtime.auth.authenticate_access(token, now=now)
    result = _tokens(
        runtime.auth.change_password(
            token,
            old_password=payload.old_password,
            new_password=payload.new_password,
            now=now,
        )
    )
    _publish_session_revoked(
        runtime, authenticated, authenticated.session_id, "password_changed", now
    )
    return result


@router.get("/api/v1/auth/sessions", response_model=list[SessionResponse])
def sessions(
    authenticated: Annotated[AuthenticatedSession, Depends(get_authenticated_session)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> list[SessionResponse]:
    return [SessionResponse(**item.__dict__) for item in runtime.auth.list_sessions(authenticated, now=datetime.now(UTC))]


@router.delete("/api/v1/auth/sessions/{session_id}", response_model=SuccessResponse)
def revoke_session(
    session_id: uuid.UUID,
    authenticated: Annotated[AuthenticatedSession, Depends(get_authenticated_session)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> SuccessResponse:
    now = datetime.now(UTC)
    runtime.auth.revoke_session(authenticated, session_id, now=now)
    _publish_session_revoked(runtime, authenticated, session_id, "revoked", now)
    return SuccessResponse()


@router.post(
    "/api/v1/channel-bindings/codes",
    response_model=BindingCodeResponse,
    status_code=201,
)
def create_binding_code(
    payload: BindingCodeRequest,
    idempotency_key: Annotated[str, Depends(require_host_idempotency_key)],
    authenticated: Annotated[AuthenticatedSession, Depends(get_authenticated_session)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> BindingCodeResponse:
    now = datetime.now(UTC)
    result, replayed = runtime.commands.execute(
        user_id=authenticated.user_id,
        operation="binding.code.create",
        idempotency_key=idempotency_key,
        payload=payload.model_dump(mode="json"),
        now=now,
        replay_error="one_time_secret_unavailable",
        command=lambda session: (
            lambda created: CommandOutcome(
                public_result={
                    "code_id": str(created.code_id),
                    "code": created.code,
                    "expires_at": created.expires_at.isoformat(),
                    "replayed": False,
                },
                receipt_result={
                    "code_id": str(created.code_id),
                    "expires_at": created.expires_at.isoformat(),
                    "status": "created",
                    "secret_available": False,
                },
            )
        )(runtime.auth.create_binding_code_in_session(
            session, principal=authenticated, channel=payload.channel, now=now
        )),
    )
    return BindingCodeResponse.model_validate(result)


@router.post("/api/v1/channel-bindings/consume", response_model=BindingResponse)
def consume_binding_code(
    payload: BindingConsumeRequest,
    idempotency_key: Annotated[str, Depends(require_host_idempotency_key)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
    adapter_token: Annotated[str | None, Header(alias="X-Channel-Adapter-Token")] = None,
) -> BindingResponse:
    now = datetime.now(UTC)
    adapter_bytes = None if adapter_token is None else adapter_token.encode("utf-8")
    receipt_user_id = runtime.auth.binding_command_user_id(adapter_bytes, payload.code_id)

    def consume_command(session):
        consumed = runtime.auth.consume_binding_code_in_session(
            session,
            code_id=payload.code_id,
            channel=payload.channel,
            provider_account=payload.provider_account,
            external_subject=payload.external_subject,
            code=payload.code,
            now=now,
        )
        if consumed.error_code is not None:
            return CommandOutcome(
                public_result={},
                receipt_result={"code_id": str(payload.code_id), "status": "rejected"},
                error_code=consumed.error_code,
            )
        assert consumed.view is not None
        bound = consumed.view
        safe = {
            "binding_id": str(bound.binding_id),
            "channel": bound.channel,
            "created_at": bound.created_at.isoformat(),
        }
        return CommandOutcome(public_result={**safe, "replayed": False}, receipt_result=safe)

    result, replayed = runtime.commands.execute(
        user_id=receipt_user_id,
        operation="binding.code.consume",
        idempotency_key=idempotency_key,
        payload=payload.model_dump(mode="json"),
        now=now,
        command=consume_command,
    )
    result["replayed"] = replayed
    return BindingResponse.model_validate(result)


@router.get("/api/v1/channel-bindings", response_model=list[BindingResponse])
def list_bindings(
    principal: Annotated[PrincipalContext, Depends(get_principal)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> list[BindingResponse]:
    return [BindingResponse(**item.__dict__) for item in runtime.auth.list_bindings(principal.user_id)]


@router.delete("/api/v1/channel-bindings/{binding_id}", response_model=SuccessResponse)
def revoke_binding(
    binding_id: uuid.UUID,
    idempotency_key: Annotated[str, Depends(require_host_idempotency_key)],
    principal: Annotated[PrincipalContext, Depends(get_principal)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> SuccessResponse:
    now = datetime.now(UTC)
    runtime.commands.execute(
        user_id=principal.user_id,
        operation="binding.revoke",
        idempotency_key=idempotency_key,
        payload={"binding_id": str(binding_id)},
        now=now,
        command=lambda session: (
            runtime.auth.revoke_binding_in_session(
                session, user_id=principal.user_id, binding_id=binding_id, now=now
            )
            and CommandOutcome(
                public_result={"success": True},
                receipt_result={"binding_id": str(binding_id), "status": "revoked"},
            )
        ),
    )
    return SuccessResponse()


@router.get("/api/v1/modules", response_model=list[ModuleResponse])
def modules(
    principal: Annotated[PrincipalContext, Depends(get_principal)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> list[ModuleResponse]:
    return [ModuleResponse.model_validate(item.model_dump()) for item in runtime.registry.summaries(principal.user_id, principal.permissions)]


@router.get("/api/v1/modules/{module_id}", response_model=ModuleResponse)
def module(
    module_id: str,
    principal: Annotated[PrincipalContext, Depends(get_principal)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> ModuleResponse:
    for item in runtime.registry.summaries(principal.user_id, principal.permissions):
        if item.module_id == module_id:
            return ModuleResponse.model_validate(item.model_dump())
    raise RegistryStartupError("module_not_found", "The module was not found.")


def _conversation(row, *, replayed: bool = False) -> ConversationResponse:
    return ConversationResponse(
        id=row.id,
        channel=row.channel,
        module_id=row.module_id,
        profile_id=row.profile_id,
        status=row.status,
        last_message_at=row.last_message_at,
        created_at=row.created_at,
        replayed=replayed,
    )


@router.post("/api/v1/conversations", response_model=ConversationResponse)
def create_conversation(
    payload: ConversationCreateRequest,
    idempotency_key: Annotated[str, Depends(require_host_idempotency_key)],
    principal: Annotated[PrincipalContext, Depends(get_principal)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> ConversationResponse:
    if payload.channel != principal.channel:
        raise HostStateError("invalid_channel", status_code=422)
    profile = runtime.registry.resolve_profile(principal.user_id, payload.profile_id)
    if profile.module_id != payload.module_id:
        raise RegistryStartupError("profile_not_found", "The Profile was not found.")
    row, replayed = runtime.conversations.create(
        user_id=principal.user_id,
        channel=payload.channel,
        module_id=payload.module_id,
        profile_id=payload.profile_id,
        idempotency_key=idempotency_key,
    )
    return _conversation(row, replayed=replayed)


@router.get("/api/v1/conversations", response_model=Page[ConversationResponse])
def list_conversations(
    principal: Annotated[PrincipalContext, Depends(get_principal)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query(max_length=512)] = None,
) -> Page[ConversationResponse]:
    endpoint = "conversations:v1"
    before = None if cursor is None else runtime.cursor.decode(
        cursor, endpoint=endpoint, user_id=principal.user_id, filter_fingerprint=""
    )
    rows = runtime.conversations.list(user_id=principal.user_id, limit=limit + 1, before=before)
    visible = rows[:limit]
    next_cursor = None
    if len(rows) > limit:
        last = visible[-1]
        next_cursor = runtime.cursor.encode(
            endpoint=endpoint,
            user_id=principal.user_id,
            filter_fingerprint="",
            sort_time=last.created_at,
            item_id=last.id,
        )
    return Page(items=[_conversation(row) for row in visible], next_cursor=next_cursor)


@router.get("/api/v1/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: uuid.UUID,
    principal: Annotated[PrincipalContext, Depends(get_principal)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> ConversationResponse:
    return _conversation(runtime.conversations.get(conversation_id, user_id=principal.user_id))


@router.get("/api/v1/conversations/{conversation_id}/messages", response_model=Page[MessageResponse])
def messages(
    conversation_id: uuid.UUID,
    principal: Annotated[PrincipalContext, Depends(get_principal)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query(max_length=512)] = None,
) -> Page[MessageResponse]:
    endpoint = f"conversation-messages:v1:{conversation_id}"
    before = None if cursor is None else runtime.cursor.decode(
        cursor, endpoint=endpoint, user_id=principal.user_id, filter_fingerprint=""
    )
    rows = runtime.conversations.messages(
        conversation_id, user_id=principal.user_id, limit=limit + 1, before=before
    )
    visible = rows[:limit]
    next_cursor = None
    if len(rows) > limit:
        last = visible[-1]
        next_cursor = runtime.cursor.encode(
            endpoint=endpoint,
            user_id=principal.user_id,
            filter_fingerprint="",
            sort_time=last.created_at,
            item_id=last.id,
        )
    return Page(items=[
        MessageResponse(
            id=row.id,
            role=row.role,
            content=row.content,
            sensitivity=row.sensitivity,
            created_at=row.created_at,
        )
        for row in visible
    ], next_cursor=next_cursor)


@router.get("/api/v1/memory-candidates", response_model=Page[MemoryCandidateResponse])
def memory_candidates(
    principal: Annotated[PrincipalContext, Depends(get_principal)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query(max_length=512)] = None,
    status: Annotated[str | None, Query()] = None,
) -> Page[MemoryCandidateResponse]:
    if status is not None and status not in {"pending", "confirmed", "rejected", "expired"}:
        raise HostStateError("invalid_request", status_code=422)
    fingerprint = status or "all"
    endpoint = "memory-candidates:v1"
    before = None if cursor is None else runtime.cursor.decode(
        cursor,
        endpoint=endpoint,
        user_id=principal.user_id,
        filter_fingerprint=fingerprint,
    )
    rows = runtime.memories.candidates(
        user_id=principal.user_id,
        status=status,
        limit=limit + 1,
        before=before,
    )
    visible = rows[:limit]
    next_cursor = None
    if len(rows) > limit:
        last = visible[-1]
        next_cursor = runtime.cursor.encode(
            endpoint=endpoint,
            user_id=principal.user_id,
            filter_fingerprint=fingerprint,
            sort_time=last.created_at,
            item_id=last.id,
        )
    return Page(items=[
        MemoryCandidateResponse(
            id=row.id,
            source_namespace=row.source_namespace,
            target_namespace=row.target_namespace,
            kind=row.kind,
            value=json.loads(row.value_json),
            sensitivity=row.sensitivity,
            status=row.status,
            expires_at=row.expires_at,
        )
        for row in visible
    ], next_cursor=next_cursor)


@router.post("/api/v1/memory-candidates/{candidate_id}/confirm", response_model=MemoryResponse)
def confirm_memory_candidate(
    candidate_id: uuid.UUID,
    payload: MemoryCandidateDecisionRequest,
    idempotency_key: Annotated[str, Depends(require_host_idempotency_key)],
    principal: Annotated[PrincipalContext, Depends(get_principal)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> MemoryResponse:
    allowed = frozenset(
        namespace
        for summary in runtime.registry.summaries(principal.user_id, principal.permissions)
        for namespace in runtime.registry.definition(summary.module_id).manifest.memory_namespaces
        if namespace.endswith(".confirmed")
    ) | frozenset({"shared.confirmed"})
    item, _ = runtime.memories.decide(
        candidate_id,
        user_id=principal.user_id,
        confirm=True,
        target_namespace=None,
        allowed_namespaces=allowed,
        idempotency_key=idempotency_key,
    )
    if item is None:
        raise HostStateError("memory_not_found", status_code=404)
    return MemoryResponse(
        id=item.id,
        namespace=item.namespace,
        kind=item.kind,
        value=json.loads(item.value_json),
        sensitivity=item.sensitivity,
        status=item.status,
        confirmed_at=item.confirmed_at,
    )


@router.post("/api/v1/memory-candidates/{candidate_id}/reject", response_model=SuccessResponse)
def reject_memory_candidate(
    candidate_id: uuid.UUID,
    idempotency_key: Annotated[str, Depends(require_host_idempotency_key)],
    principal: Annotated[PrincipalContext, Depends(get_principal)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> SuccessResponse:
    runtime.memories.decide(
        candidate_id,
        user_id=principal.user_id,
        confirm=False,
        target_namespace=None,
        allowed_namespaces=frozenset(),
        idempotency_key=idempotency_key,
    )
    return SuccessResponse()


@router.get("/api/v1/memories", response_model=list[MemoryResponse])
def memories(
    principal: Annotated[PrincipalContext, Depends(get_principal)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> list[MemoryResponse]:
    allowed = frozenset(
        namespace
        for summary in runtime.registry.summaries(principal.user_id, principal.permissions)
        for namespace in runtime.registry.definition(summary.module_id).manifest.memory_namespaces
        if namespace.endswith(".confirmed")
    ) | frozenset({"shared.confirmed"})
    return [
        MemoryResponse(
            id=row.id,
            namespace=row.namespace,
            kind=row.kind,
            value=json.loads(row.value_json),
            sensitivity=row.sensitivity,
            status=row.status,
            confirmed_at=row.confirmed_at,
        )
        for row in runtime.memories.retrieve(
            user_id=principal.user_id,
            allowed_namespaces=allowed,
            profile_limit=8,
        )
    ]


@router.delete("/api/v1/memories/{memory_id}", response_model=SuccessResponse)
def delete_memory(
    memory_id: uuid.UUID,
    idempotency_key: Annotated[str, Depends(require_host_idempotency_key)],
    principal: Annotated[PrincipalContext, Depends(get_principal)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> SuccessResponse:
    runtime.memories.delete(
        memory_id,
        user_id=principal.user_id,
        idempotency_key=idempotency_key,
    )
    return SuccessResponse()


@router.get("/api/v1/settings/{module_id}", response_model=list[SettingResponse])
def settings(
    module_id: str,
    principal: Annotated[PrincipalContext, Depends(get_principal)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> list[SettingResponse]:
    runtime.registry.definition(module_id)
    return [
        SettingResponse(
            id=row.id,
            module_id=row.module_id,
            key=row.key,
            value=json.loads(row.value_json),
            schema_version=row.schema_version,
            version_id=row.version_id,
            updated_at=row.updated_at,
        )
        for row in runtime.settings.get(user_id=principal.user_id, module_id=module_id)
    ]


@router.put("/api/v1/settings/{module_id}", response_model=SettingResponse)
def put_setting(
    module_id: str,
    payload: SettingPutRequest,
    idempotency_key: Annotated[str, Depends(require_host_idempotency_key)],
    principal: Annotated[PrincipalContext, Depends(get_principal)],
    runtime: Annotated[HostRuntime, Depends(get_host_runtime)],
) -> SettingResponse:
    runtime.registry.definition(module_id)
    row, replayed = runtime.settings.put(
        user_id=principal.user_id,
        module_id=module_id,
        key=payload.key,
        value=payload.value,
        schema_version=payload.schema_version,
        expected_version=payload.expected_version,
        idempotency_key=idempotency_key,
    )
    return SettingResponse(
        id=row.id,
        module_id=row.module_id,
        key=row.key,
        value=json.loads(row.value_json),
        schema_version=row.schema_version,
        version_id=row.version_id,
        updated_at=row.updated_at,
        replayed=replayed,
    )


@router.get("/readyz", response_model=ReadyResponse)
def readyz(runtime: Annotated[HostRuntime, Depends(get_host_runtime)]) -> ReadyResponse:
    ready, code = runtime.readiness()
    if not ready:
        raise HostStateError(code or "backend_not_ready", status_code=503, retryable=True)
    return ReadyResponse()
