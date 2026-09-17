"""FastAPI application exposing the phase-0 health check and probe."""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from wife_system.api.schemas import (
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    ProbeRequest,
    ProbeResponse,
)
from wife_system.agent.application import AgentApplication, AgentApplicationError
from wife_system.api.agent_routes import AgentIdentity, router as agent_router
from wife_system.probes import DuplicateProbeRequestError, ProbeService


LOGGER = logging.getLogger("wife_system.api")
MAX_IDEMPOTENCY_KEY_LENGTH = 256


class ApiError(RuntimeError):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        request_id: str | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.safe_message = message
        self.request_id = request_id
        self.retryable = retryable


def _emit(event: str, **fields: Any) -> None:
    LOGGER.info(json.dumps({"event": event, **fields}, ensure_ascii=False, separators=(",", ":")))


def _error_response(
    *, request_id: str, status_code: int, code: str, message: str, retryable: bool
) -> JSONResponse:
    payload = ErrorResponse(
        request_id=request_id,
        error=ErrorDetail(code=code, message=message, retryable=retryable),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def get_probe_service(request: Request) -> ProbeService:
    return request.app.state.probe_service


def require_idempotency_key(
    request: Request,
    value: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            min_length=1,
            max_length=MAX_IDEMPOTENCY_KEY_LENGTH,
        ),
    ],
) -> str:
    if not value.strip():
        raise ApiError(
            status_code=422,
            code="invalid_request",
            message="A valid Idempotency-Key header is required.",
            request_id=request.state.request_id,
        )
    return value


def create_app(
    *,
    probe_service: ProbeService | None = None,
    agent_application: AgentApplication | None = None,
    agent_identity: AgentIdentity | None = None,
) -> FastAPI:
    application = FastAPI(title="wife-system", version="0.1.0")
    application.state.probe_service = ProbeService() if probe_service is None else probe_service
    application.state.agent_application = agent_application
    application.state.agent_identity = agent_identity or AgentIdentity(
        actor_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        permissions=frozenset({"finance:read", "finance:write"}),
    )

    @application.middleware("http")
    async def assign_request_id(request: Request, call_next: Any) -> Any:
        request.state.request_id = str(uuid.uuid4())
        _emit(
            "request_received",
            request_id=request.state.request_id,
            method=request.method,
            path=request.url.path,
        )
        return await call_next(request)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        del exc
        request_id = request.state.request_id
        _emit("request_failed", request_id=request_id, code="invalid_request")
        return _error_response(
            request_id=request_id,
            status_code=422,
            code="invalid_request",
            message="The request failed validation.",
            retryable=False,
        )

    @application.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        request_id = exc.request_id or request.state.request_id
        _emit("request_failed", request_id=request_id, code=exc.code)
        return _error_response(
            request_id=request_id,
            status_code=exc.status_code,
            code=exc.code,
            message=exc.safe_message,
            retryable=exc.retryable,
        )

    @application.exception_handler(AgentApplicationError)
    async def agent_error_handler(request: Request, exc: AgentApplicationError) -> JSONResponse:
        request_id = request.state.request_id
        _emit("request_failed", request_id=request_id, code=exc.code)
        messages = {
            "agent_unavailable": "The agent service is unavailable.",
            "duplicate_request_conflict": "The source event was reused with different input.",
            "permission_denied": "This action is not permitted.",
            "confirmation_required": "This action requires the matching confirmation code.",
            "pending_action_not_found": "The pending action was not found.",
            "pending_action_expired": "The pending action has expired.",
            "pending_action_stale": "The pending action must be reviewed again.",
            "validation_error": "The request failed validation.",
            "persistence_error": "The request could not be persisted.",
            "database_unavailable": "The finance database is unavailable.",
        }
        return _error_response(
            request_id=request_id,
            status_code=exc.status_code,
            code=exc.code,
            message=messages.get(exc.code, "The agent request could not be completed."),
            retryable=exc.retryable,
        )

    @application.exception_handler(Exception)
    async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = request.state.request_id
        _emit(
            "request_failed",
            request_id=request_id,
            code="internal_error",
            error_type=type(exc).__name__,
        )
        return _error_response(
            request_id=request_id,
            status_code=500,
            code="internal_error",
            message="The service could not complete the request.",
            retryable=False,
        )

    @application.get("/healthz", response_model=HealthResponse)
    def healthz() -> HealthResponse:
        return HealthResponse(status="ok", service="wife-system")

    @application.post(
        "/api/v1/probes",
        response_model=ProbeResponse,
        responses={
            409: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            500: {"model": ErrorResponse},
        },
    )
    def create_probe(
        request: Request,
        payload: ProbeRequest,
        idempotency_key: Annotated[str, Depends(require_idempotency_key)],
        service: Annotated[ProbeService, Depends(get_probe_service)],
    ) -> ProbeResponse:
        key_digest = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
        try:
            result = service.create(
                idempotency_key=idempotency_key,
                challenge=payload.challenge,
                candidate_request_id=request.state.request_id,
            )
        except DuplicateProbeRequestError as exc:
            _emit(
                "probe_conflict",
                request_id=exc.request_id,
                idempotency_key_hash=key_digest,
            )
            raise ApiError(
                status_code=409,
                code="duplicate_request_conflict",
                message="The idempotency key was already used for different input.",
                request_id=exc.request_id,
            ) from exc

        record = result.record
        request.state.request_id = record.request_id
        _emit(
            "probe_replayed" if result.replayed else "probe_created",
            request_id=record.request_id,
            idempotency_key_hash=key_digest,
            receipt=record.receipt,
        )
        return ProbeResponse(
            request_id=record.request_id,
            challenge=record.challenge,
            receipt=record.receipt,
            created_at=record.created_at,
            replayed=result.replayed,
        )

    application.include_router(agent_router)
    return application


app = create_app()
