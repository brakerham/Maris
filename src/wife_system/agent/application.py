"""P2 Agent application service with persistent run idempotency and resume."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import threading
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from wife_system.agent.context import RunContext
from wife_system.agent.finance_tools import (
    FinanceToolAdapter,
    RecordExpenseToolInput,
    finance_registry,
)
from wife_system.agent.loop import AgentRunner
from wife_system.agent.models import AgentRunRecord
from wife_system.agent.pending import PendingAction, PendingActionError, PendingActionStore
from wife_system.agent.types import AgentRunResult, RunStatus
from wife_system.agent.providers import ModelProvider
from wife_system.finance import FinanceService


LOGGER = logging.getLogger("wife_system.agent")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class AgentApplicationError(RuntimeError):
    def __init__(self, code: str, *, status_code: int = 409, retryable: bool = False) -> None:
        self.code = code
        self.status_code = status_code
        self.retryable = retryable
        super().__init__(code)


class AgentRunView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: uuid.UUID
    status: Literal["running", "success", "error", "paused"]
    replayed: bool = False
    answer: str | None = None
    error_code: str | None = None
    pending_action_id: uuid.UUID | None = None
    pause_reason: str | None = None
    result: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class AgentApplication:
    def __init__(
        self,
        *,
        sessions: sessionmaker[Session],
        runner: AgentRunner,
        finance_tools: FinanceToolAdapter,
        pending: PendingActionStore,
        digest_key: bytes,
    ) -> None:
        if not digest_key:
            raise ValueError("digest_key must not be empty")
        self._sessions = sessions
        self._runner = runner
        self._finance_tools = finance_tools
        self._pending = pending
        self._digest_key = digest_key
        self._locks_guard = threading.Lock()
        self._run_locks: dict[uuid.UUID, threading.Lock] = {}
        self._pending_locks: dict[uuid.UUID, threading.Lock] = {}

    def _digest(self, scope: str, value: str) -> str:
        return hmac.new(self._digest_key, f"{scope}\0{value}".encode(), hashlib.sha256).hexdigest()

    def _lock_for(self, values: dict[uuid.UUID, threading.Lock], key: uuid.UUID) -> threading.Lock:
        with self._locks_guard:
            return values.setdefault(key, threading.Lock())

    @staticmethod
    def _view(row: AgentRunRecord, *, replayed: bool = False) -> AgentRunView:
        return AgentRunView(
            run_id=row.id,
            status=row.status,
            replayed=replayed,
            answer=row.answer,
            error_code=row.error_code,
            pending_action_id=row.pending_action_id,
            pause_reason=row.pause_reason,
            result=None if row.result_json is None else json.loads(row.result_json),
            created_at=_utc(row.created_at),
            updated_at=_utc(row.updated_at),
        )

    def _load(
        self, run_id: uuid.UUID, *, user_id: uuid.UUID | None = None
    ) -> AgentRunRecord | None:
        try:
            with self._sessions() as session:
                row = session.get(AgentRunRecord, run_id)
                if row is not None and user_id is not None and row.user_id != user_id:
                    return None
                return row
        except SQLAlchemyError as exc:
            raise AgentApplicationError(
                "database_unavailable", status_code=503, retryable=True
            ) from exc

    def _claim_run(
        self,
        *,
        actor_id: uuid.UUID,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        source_system: str,
        source_event_id: str,
        message: str,
        now: datetime,
        module_id: str,
        profile_id: str,
    ) -> tuple[AgentRunRecord, bool]:
        event_digest = self._digest("source-event", source_event_id)
        fingerprint = self._digest("message", message)
        row = AgentRunRecord(
            user_id=user_id,
            actor_id=actor_id,
            conversation_id=conversation_id,
            source_system=source_system,
            source_event_digest=event_digest,
            request_fingerprint=fingerprint,
            status="running",
            model_name=type(self._runner.provider).__name__,
            module_id=module_id,
            profile_id=profile_id,
            profile_version="1.0.0",
            attempt_no=1,
            lease_expires_at=now + timedelta(seconds=60),
            action_schema_version=1,
            created_at=_utc(now),
            updated_at=_utc(now),
        )
        try:
            with self._sessions() as session, session.begin():
                session.add(row)
            return row, False
        except IntegrityError:
            try:
                with self._sessions() as session:
                    existing = session.scalar(
                        select(AgentRunRecord).where(
                            AgentRunRecord.user_id == user_id,
                            AgentRunRecord.source_system == source_system,
                            AgentRunRecord.source_event_digest == event_digest,
                        )
                    )
                    if existing is None:
                        raise AgentApplicationError("persistence_error", status_code=503, retryable=True)
                    if (
                        existing.request_fingerprint != fingerprint
                        or existing.conversation_id != conversation_id
                    ):
                        raise AgentApplicationError("duplicate_request_conflict")
                    return existing, True
            except SQLAlchemyError as exc:
                raise AgentApplicationError(
                    "database_unavailable", status_code=503, retryable=True
                ) from exc
        except SQLAlchemyError as exc:
            raise AgentApplicationError(
                "database_unavailable", status_code=503, retryable=True
            ) from exc

    def _save_result(self, run_id: uuid.UUID, result: AgentRunResult, *, now: datetime) -> AgentRunView:
        with self._sessions() as session, session.begin():
            row = session.get(AgentRunRecord, run_id)
            if row is None:
                raise AgentApplicationError("pending_action_not_found", status_code=404)
            row.status = result.status.value
            row.answer = result.answer
            row.error_code = result.error_code
            row.pause_reason = result.pause_reason
            row.pending_action_id = None if result.pending_action_id is None else uuid.UUID(result.pending_action_id)
            row.result_json = None if result.result is None else json.dumps(
                result.result, sort_keys=True, separators=(",", ":")
            )
            row.events_json = json.dumps(
                [event.model_dump(mode="json") for event in result.events],
                sort_keys=True,
                separators=(",", ":"),
            )
            row.updated_at = _utc(now)
            for event in result.events:
                LOGGER.info(
                    json.dumps(
                        {
                            "event": "agent_execution",
                            "run_id": str(run_id),
                            "sequence": event.sequence,
                            "kind": event.kind,
                            "model_turn": event.model_turn,
                            "tool_name": event.tool_name,
                            "duration_ms": event.duration_ms,
                            "outcome": event.outcome,
                        },
                        separators=(",", ":"),
                    )
                )
        loaded = self._load(run_id)
        assert loaded is not None
        return self._view(loaded)

    def _save_resume(
        self,
        run_id: uuid.UUID,
        *,
        status: str,
        now: datetime,
        pause_reason: str | None = None,
        error_code: str | None = None,
        result: dict[str, Any] | None = None,
    ) -> AgentRunView:
        with self._sessions() as session, session.begin():
            row = session.get(AgentRunRecord, run_id)
            if row is None:
                raise AgentApplicationError("pending_action_not_found", status_code=404)
            row.status = status
            row.pause_reason = pause_reason
            row.error_code = error_code
            row.result_json = None if result is None else json.dumps(result, sort_keys=True, separators=(",", ":"))
            row.updated_at = _utc(now)
        loaded = self._load(run_id)
        assert loaded is not None
        return self._view(loaded)

    def start(
        self,
        *,
        actor_id: uuid.UUID,
        conversation_id: uuid.UUID,
        client_event_id: uuid.UUID,
        message: str,
        permissions: frozenset[str],
        received_at: datetime | None = None,
        user_id: uuid.UUID | None = None,
        module_id: str = "daily_finance",
        profile_id: str = "daily_finance.assistant@1",
    ) -> AgentRunView:
        now = _utc(received_at or datetime.now(UTC))
        scope_user_id = user_id or actor_id
        if scope_user_id != actor_id:
            raise AgentApplicationError("permission_denied", status_code=403)
        row, replayed = self._claim_run(
            actor_id=actor_id,
            user_id=scope_user_id,
            conversation_id=conversation_id,
            source_system="desktop_chat",
            source_event_id=str(client_event_id),
            message=message,
            now=now,
            module_id=module_id,
            profile_id=profile_id,
        )
        lock = self._lock_for(self._run_locks, row.id)
        with lock:
            current = self._load(row.id, user_id=scope_user_id)
            assert current is not None
            if current.status != "running":
                return self._view(current, replayed=replayed)
            recovered = self._pending.active_for_run(row.id, user_id=scope_user_id)
            if recovered is not None:
                result = AgentRunResult(
                    request_id=str(row.id),
                    status=RunStatus.PAUSED,
                    pending_action_id=str(recovered.id),
                    pause_reason=recovered.status,
                    events=(),
                )
                view = self._save_result(row.id, result, now=now)
                return view.model_copy(update={"replayed": replayed})
            if replayed:
                return self._view(current, replayed=True)
            context = RunContext(
                agent_run_id=row.id,
                actor_id=actor_id,
                conversation_id=conversation_id,
                source_system="desktop_chat",
                source_event_id=str(client_event_id),
                received_at=now,
                permissions=permissions,
                user_message=message,
            )
            result = self._runner.run(message, str(row.id), context=context)
            view = self._save_result(row.id, result, now=datetime.now(UTC))
            return view.model_copy(update={"replayed": replayed})

    def get(
        self,
        run_id: uuid.UUID,
        *,
        actor_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> AgentRunView:
        scope_user_id = user_id or actor_id
        row = self._load(run_id, user_id=scope_user_id)
        if (
            row is None
            or scope_user_id != actor_id
            or row.actor_id != actor_id
            or row.conversation_id != conversation_id
        ):
            raise AgentApplicationError("pending_action_not_found", status_code=404)
        if row.status == "paused" and row.pending_action_id is not None:
            try:
                pending = self._pending.get(
                    row.pending_action_id,
                    actor_id=actor_id,
                    conversation_id=conversation_id,
                )
                if pending.status in {"cancelled", "committed"}:
                    return self._save_resume(
                        run_id,
                        status="success",
                        now=datetime.now(UTC),
                        result=pending.final_result or {"status": pending.status},
                    )
            except PendingActionError as exc:
                if exc.code == "pending_action_expired":
                    return self._save_resume(
                        run_id,
                        status="paused",
                        now=datetime.now(UTC),
                        pause_reason="expired",
                        error_code=exc.code,
                        result={"status": "expired"},
                    )
                raise AgentApplicationError(exc.code, retryable=exc.retryable) from exc
        return self._view(row)

    def _pending_for_run(
        self,
        run_id: uuid.UUID,
        *,
        actor_id: uuid.UUID,
        conversation_id: uuid.UUID,
        now: datetime,
    ) -> PendingAction:
        run = self.get(run_id, actor_id=actor_id, conversation_id=conversation_id)
        if run.pending_action_id is None:
            raise AgentApplicationError("pending_action_not_found", status_code=404)
        try:
            return self._pending.get(
                run.pending_action_id,
                actor_id=actor_id,
                conversation_id=conversation_id,
                now=now,
            )
        except PendingActionError as exc:
            raise AgentApplicationError(exc.code, status_code=409, retryable=exc.retryable) from exc

    def resume(
        self,
        run_id: uuid.UUID,
        *,
        actor_id: uuid.UUID,
        conversation_id: uuid.UUID,
        action: Literal["confirm", "cancel", "provide_input"],
        permissions: frozenset[str],
        confirmation_code: str | None = None,
        values: dict[str, Any] | None = None,
        now: datetime | None = None,
        user_id: uuid.UUID | None = None,
    ) -> AgentRunView:
        at = _utc(now or datetime.now(UTC))
        scope_user_id = user_id or actor_id
        if scope_user_id != actor_id:
            raise AgentApplicationError("permission_denied", status_code=403)
        pending = self._pending_for_run(
            run_id, actor_id=actor_id, conversation_id=conversation_id, now=at
        )
        if "finance:write" not in permissions:
            raise AgentApplicationError("permission_denied", status_code=403)
        lock = self._lock_for(self._pending_locks, pending.id)
        with lock:
            pending = self._pending.get(
                pending.id, actor_id=actor_id, conversation_id=conversation_id, now=at
            )
            if action == "cancel":
                self._pending.cancel(pending, now=at)
                return self._save_resume(run_id, status="success", now=at, result={"status": "cancelled"})
            if action == "provide_input":
                supplied = dict(values or {})
                record_intent = supplied.pop("record_intent", None)
                merged = {**pending.action, **supplied}
                try:
                    parsed = RecordExpenseToolInput.model_validate(merged)
                    missing = [
                        key
                        for key in ("amount", "account_id", "category_id")
                        if getattr(parsed, key) is None
                    ]
                    if "record_intent" in pending.missing_fields and record_intent != "record":
                        missing.insert(0, "record_intent")
                    versions, _, _ = self._finance_tools._resource_versions(parsed)
                    updated = self._pending.supplement(
                        pending.id,
                        actor_id=actor_id,
                        conversation_id=conversation_id,
                        values=parsed.model_dump(mode="json"),
                        missing_fields=missing,
                        resource_versions=versions,
                        now=at,
                    )
                except Exception as exc:
                    if isinstance(exc, PendingActionError):
                        raise AgentApplicationError(exc.code, retryable=exc.retryable) from exc
                    raise AgentApplicationError("validation_error", status_code=422) from exc
                return self._save_resume(
                    run_id,
                    status="paused",
                    now=at,
                    pause_reason=updated.status,
                    result={
                        "status": updated.status,
                        "pending_action_id": str(updated.id),
                        "confirmation_code": updated.confirmation_code if not missing else None,
                        "missing_fields": missing,
                    },
                )
            if confirmation_code != pending.confirmation_code:
                raise AgentApplicationError("confirmation_required", status_code=409)
            if pending.status == "committed":
                replay = self._finance_tools.commit(pending)
                return self._save_resume(run_id, status="success", now=at, result=replay)
            if pending.status not in {"needs_confirmation", "committing"}:
                raise AgentApplicationError("confirmation_required", status_code=409)
            try:
                self._finance_tools.validate_versions(pending)
                if pending.status == "needs_confirmation":
                    self._pending.claim_commit(
                        pending, approval_grant_id=uuid.uuid4(), now=at
                    )
                committing = self._pending.get(
                    pending.id, actor_id=actor_id, conversation_id=conversation_id, now=at
                )
                result = self._finance_tools.commit(committing)
                if result["status"] == "committed":
                    self._pending.mark_committed(pending.id, result, now=at)
                    return self._save_resume(run_id, status="success", now=at, result=result)
                error = result.get("error", {})
                return self._save_resume(
                    run_id,
                    status="paused",
                    now=at,
                    pause_reason="committing",
                    error_code=error.get("code"),
                    result=result,
                )
            except PendingActionError as exc:
                raise AgentApplicationError(exc.code, retryable=exc.retryable) from exc


def build_agent_application(
    *,
    sessions: sessionmaker[Session],
    finance: FinanceService,
    provider: ModelProvider,
    digest_key: bytes,
) -> AgentApplication:
    """Build the replaceable-model P2 service over shared short-lived sessions."""

    pending = PendingActionStore(sessions)
    adapter = FinanceToolAdapter(finance, pending)
    runner = AgentRunner(provider=provider, tools=finance_registry(adapter))
    return AgentApplication(
        sessions=sessions,
        runner=runner,
        finance_tools=adapter,
        pending=pending,
        digest_key=digest_key,
    )
