"""Strict HTTP boundary for persistent activity imports."""

from __future__ import annotations

import json
import re
import uuid
from typing import Annotated, TypeVar

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from starlette.concurrency import run_in_threadpool

from wife_system.activity_import.context import ImportIdentity
from wife_system.activity_import.errors import ActivityImportError
from wife_system.activity_import.schemas import BatchResponse, CommitRequest, CommitResponse, PreviewRequest
from wife_system.activity_import.service import ActivityImportService, validate_idempotency_key

MAX_BODY_BYTES = 96 * 1024
T = TypeVar("T", bound=BaseModel)
router = APIRouter(prefix="/api/v1/activity-imports", tags=["activity-imports"])


def get_import_identity(request: Request) -> ImportIdentity:
    identity = request.app.state.activity_import_identity
    if identity is None:
        raise ActivityImportError("invalid_request")
    return identity


def get_import_service(request: Request) -> ActivityImportService:
    service = request.app.state.activity_import_service
    if service is None:
        raise ActivityImportError("database_unavailable")
    return service


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(_: str) -> object:
    raise ValueError("invalid JSON constant")


async def _body(request: Request, model: type[T]) -> T:
    media_types = request.headers.getlist("content-type")
    if len(media_types) != 1 or not re.fullmatch(
        r'application/json(?:\s*;\s*charset\s*=\s*(?:"utf-8"|utf-8))?\s*',
        media_types[0],
        flags=re.IGNORECASE,
    ):
        raise ActivityImportError("invalid_content_type")
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > MAX_BODY_BYTES:
            raise ActivityImportError("import_text_too_large")
        data.extend(chunk)
    try:
        value = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_invalid_constant,
        )
        return model.model_validate(value)
    except (ValueError, TypeError, UnicodeError, RecursionError, ValidationError):
        raise ActivityImportError("invalid_request") from None


def _idempotency_key(request: Request) -> str:
    values = request.headers.getlist("idempotency-key")
    if len(values) != 1:
        raise ActivityImportError("invalid_request")
    return validate_idempotency_key(values[0])


Identity = Annotated[ImportIdentity, Depends(get_import_identity)]
Service = Annotated[ActivityImportService, Depends(get_import_service)]


@router.post("/preview")
async def preview(request: Request, identity: Identity, service: Service) -> JSONResponse:
    key = _idempotency_key(request)
    payload = await _body(request, PreviewRequest)
    result = await run_in_threadpool(
        service.preview,
        identity,
        payload,
        key,
        request_id=uuid.UUID(request.state.request_id),
    )
    return JSONResponse(
        status_code=200 if result.replayed else 201,
        content=result.model_dump(mode="json"),
    )


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: uuid.UUID,
    request: Request,
    identity: Identity,
    service: Service,
) -> BatchResponse:
    return await run_in_threadpool(
        service.get,
        identity,
        batch_id,
        request_id=uuid.UUID(request.state.request_id),
    )


@router.post("/{batch_id}/commit", response_model=CommitResponse)
async def commit(
    batch_id: uuid.UUID,
    request: Request,
    identity: Identity,
    service: Service,
) -> CommitResponse:
    key = _idempotency_key(request)
    payload = await _body(request, CommitRequest)
    return await run_in_threadpool(
        service.commit,
        identity,
        batch_id,
        payload,
        key,
        request_id=uuid.UUID(request.state.request_id),
    )
