"""Small Host workflow shell around registered, versioned action handlers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from wife_system.agent.models import AgentRunRecord
from wife_system.host.context import PrincipalContext


LEASE_DURATION = timedelta(seconds=60)
MAX_RUN_ATTEMPTS = 3


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class WorkflowError(RuntimeError):
    def __init__(self, code: str, *, retryable: bool = False) -> None:
        self.code = code
        self.retryable = retryable
        super().__init__(code)


class ActionHandler(Protocol):
    action_type: str
    action_schema_version: int

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    def summarize(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    def validate_versions(self, principal: PrincipalContext, payload: dict[str, Any]) -> None: ...

    def commit(
        self,
        principal: PrincipalContext,
        payload: dict[str, Any],
        source_event_id: str,
    ) -> dict[str, Any]: ...


class ActionHandlerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[tuple[str, int], ActionHandler] = {}

    def register(self, handler: ActionHandler) -> None:
        key = (handler.action_type, handler.action_schema_version)
        if key in self._handlers:
            raise WorkflowError("duplicate_action_handler")
        if handler.action_schema_version != 1:
            raise WorkflowError("unsupported_action_schema")
        self._handlers[key] = handler

    def resolve(self, action_type: str, schema_version: int) -> ActionHandler:
        try:
            return self._handlers[(action_type, schema_version)]
        except KeyError as exc:
            raise WorkflowError("action_handler_not_found") from exc


class RunLeaseCoordinator:
    """Database CAS for a 60-second lease and at most three attempts."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def acquire(
        self,
        run_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
        now: datetime | None = None,
    ) -> AgentRunRecord:
        at = _utc(now or datetime.now(UTC))
        with self._sessions() as session, session.begin():
            row = session.scalar(
                select(AgentRunRecord).where(
                    AgentRunRecord.id == run_id,
                    AgentRunRecord.user_id == user_id,
                )
            )
            if row is None:
                raise WorkflowError("run_not_found")
            current_expiry = None if row.lease_expires_at is None else _utc(row.lease_expires_at)
            if row.status != "running":
                return row
            if current_expiry is not None and current_expiry > at:
                raise WorkflowError("run_lease_active", retryable=True)
            if row.attempt_no >= MAX_RUN_ATTEMPTS:
                raise WorkflowError("run_attempts_exhausted")
            expected_attempt = row.attempt_no
            result = session.execute(
                update(AgentRunRecord)
                .where(
                    AgentRunRecord.id == run_id,
                    AgentRunRecord.user_id == user_id,
                    AgentRunRecord.status == "running",
                    AgentRunRecord.attempt_no == expected_attempt,
                    (AgentRunRecord.lease_expires_at.is_(None) | (AgentRunRecord.lease_expires_at <= at)),
                )
                .values(
                    attempt_no=expected_attempt + 1,
                    lease_expires_at=at + LEASE_DURATION,
                    updated_at=at,
                )
                .execution_options(synchronize_session=False)
            )
            if result.rowcount != 1:
                raise WorkflowError("run_lease_active", retryable=True)
            session.refresh(row)
            session.expunge(row)
            return row

    def renew(
        self,
        run_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
        attempt_no: int,
        now: datetime | None = None,
    ) -> None:
        at = _utc(now or datetime.now(UTC))
        with self._sessions() as session, session.begin():
            result = session.execute(
                update(AgentRunRecord)
                .where(
                    AgentRunRecord.id == run_id,
                    AgentRunRecord.user_id == user_id,
                    AgentRunRecord.status == "running",
                    AgentRunRecord.attempt_no == attempt_no,
                )
                .values(lease_expires_at=at + LEASE_DURATION, updated_at=at)
                .execution_options(synchronize_session=False)
            )
            if result.rowcount != 1:
                raise WorkflowError("run_lease_lost", retryable=True)
