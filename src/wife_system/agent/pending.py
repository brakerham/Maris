"""Database-backed pending-action state machine."""

from __future__ import annotations

import json
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from wife_system.agent.models import PendingActionRecord


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class PendingActionError(RuntimeError):
    def __init__(self, code: str, *, retryable: bool = False) -> None:
        self.code = code
        self.retryable = retryable
        super().__init__(code)


class PendingAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: uuid.UUID
    user_id: uuid.UUID
    run_id: uuid.UUID
    actor_id: uuid.UUID
    conversation_id: uuid.UUID
    source_system: str
    action_type: str
    action: dict[str, Any]
    missing_fields: tuple[str, ...]
    resource_versions: dict[str, int]
    status: str
    version_id: int
    confirmation_code: str
    approval_grant_id: uuid.UUID | None
    final_result: dict[str, Any] | None
    created_at: datetime
    expires_at: datetime
    module_id: str
    profile_id: str
    action_schema_version: int
    commit_attempt_no: int
    commit_lease_expires_at: datetime | None


class CommitClaim(BaseModel):
    """The database fence owned by exactly one pending commit worker."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pending_action_id: uuid.UUID
    version_id: int
    attempt_no: int
    lease_expires_at: datetime


class PendingActionStore:
    def __init__(self, sessions: sessionmaker[Session], *, ttl: timedelta = timedelta(hours=24)) -> None:
        self._sessions = sessions
        self._ttl = ttl

    @staticmethod
    def _view(row: PendingActionRecord) -> PendingAction:
        return PendingAction(
            id=row.id,
            user_id=row.user_id,
            run_id=row.run_id,
            actor_id=row.actor_id,
            conversation_id=row.conversation_id,
            source_system=row.source_system,
            action_type=row.action_type,
            action=json.loads(row.action_json),
            missing_fields=tuple(json.loads(row.missing_fields_json)),
            resource_versions=json.loads(row.resource_versions_json),
            status=row.status,
            version_id=row.version_id,
            confirmation_code=row.confirmation_code,
            approval_grant_id=row.approval_grant_id,
            final_result=None if row.final_result_json is None else json.loads(row.final_result_json),
            created_at=_utc(row.created_at),
            expires_at=_utc(row.expires_at),
            module_id=row.module_id,
            profile_id=row.profile_id,
            action_schema_version=row.action_schema_version,
            commit_attempt_no=row.commit_attempt_no,
            commit_lease_expires_at=(
                None
                if row.commit_lease_expires_at is None
                else _utc(row.commit_lease_expires_at)
            ),
        )

    def create(
        self,
        *,
        run_id: uuid.UUID,
        actor_id: uuid.UUID,
        conversation_id: uuid.UUID,
        source_system: str,
        action_type: str,
        action: dict[str, Any],
        missing_fields: list[str],
        resource_versions: dict[str, int],
        now: datetime,
        user_id: uuid.UUID | None = None,
        module_id: str = "daily_finance",
        profile_id: str = "daily_finance.assistant@1",
        action_schema_version: int = 1,
    ) -> PendingAction:
        scope_user_id = user_id or actor_id
        if scope_user_id != actor_id:
            raise PendingActionError("permission_denied")
        status = "needs_input" if missing_fields else "needs_confirmation"
        for _ in range(5):
            row = PendingActionRecord(
                user_id=scope_user_id,
                run_id=run_id,
                actor_id=actor_id,
                conversation_id=conversation_id,
                source_system=source_system,
                module_id=module_id,
                profile_id=profile_id,
                action_schema_version=action_schema_version,
                action_type=action_type,
                action_json=json.dumps(action, sort_keys=True, separators=(",", ":")),
                missing_fields_json=json.dumps(missing_fields, separators=(",", ":")),
                resource_versions_json=json.dumps(resource_versions, sort_keys=True, separators=(",", ":")),
                status=status,
                confirmation_code=secrets.token_hex(3).upper(),
                created_at=_utc(now),
                updated_at=_utc(now),
                expires_at=_utc(now) + self._ttl,
            )
            try:
                with self._sessions() as session, session.begin():
                    session.add(row)
                return self._view(row)
            except IntegrityError:
                with self._sessions() as session:
                    existing = session.scalar(
                        select(PendingActionRecord).where(
                            PendingActionRecord.run_id == run_id,
                            PendingActionRecord.user_id == scope_user_id,
                        )
                    )
                    if existing is not None:
                        return self._view(existing)
                continue
        raise PendingActionError("persistence_error", retryable=True)

    def get(
        self,
        action_id: uuid.UUID,
        *,
        actor_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        now: datetime | None = None,
    ) -> PendingAction:
        check_time = _utc(now or datetime.now(UTC))
        scope_user_id = user_id or actor_id
        if scope_user_id != actor_id:
            raise PendingActionError("permission_denied")
        with self._sessions() as session, session.begin():
            row = session.get(PendingActionRecord, action_id)
            if (
                row is None
                or row.user_id != scope_user_id
                or row.actor_id != actor_id
                or row.conversation_id != conversation_id
            ):
                raise PendingActionError("pending_action_not_found")
            if row.status not in {"committed", "cancelled", "expired"} and _utc(row.expires_at) <= check_time:
                row.status = "expired"
                row.version_id += 1
                row.updated_at = check_time
            view = self._view(row)
        if view.status == "expired":
            raise PendingActionError("pending_action_expired")
        return view

    def active_for_run(
        self, run_id: uuid.UUID, *, user_id: uuid.UUID | None = None
    ) -> PendingAction | None:
        with self._sessions() as session:
            statement = select(PendingActionRecord).where(PendingActionRecord.run_id == run_id)
            if user_id is not None:
                statement = statement.where(PendingActionRecord.user_id == user_id)
            row = session.scalar(
                statement
                .order_by(PendingActionRecord.created_at.desc(), PendingActionRecord.id)
                .limit(1)
            )
            return None if row is None else self._view(row)

    def supplement(
        self,
        action_id: uuid.UUID,
        *,
        actor_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        values: dict[str, Any],
        missing_fields: list[str],
        resource_versions: dict[str, int],
        now: datetime,
    ) -> PendingAction:
        current = self.get(
            action_id,
            actor_id=actor_id,
            conversation_id=conversation_id,
            user_id=user_id,
            now=now,
        )
        if current.status != "needs_input":
            raise PendingActionError("pending_action_stale", retryable=True)
        action = {**current.action, **values}
        next_status = "needs_input" if missing_fields else "needs_confirmation"
        with self._sessions() as session, session.begin():
            result = session.execute(
                update(PendingActionRecord)
                .where(
                    PendingActionRecord.id == action_id,
                    PendingActionRecord.status == "needs_input",
                    PendingActionRecord.version_id == current.version_id,
                )
                .values(
                    action_json=json.dumps(action, sort_keys=True, separators=(",", ":")),
                    missing_fields_json=json.dumps(missing_fields, separators=(",", ":")),
                    resource_versions_json=json.dumps(resource_versions, sort_keys=True, separators=(",", ":")),
                    status=next_status,
                    version_id=current.version_id + 1,
                    updated_at=_utc(now),
                )
            )
            if result.rowcount != 1:
                raise PendingActionError("pending_action_stale", retryable=True)
        return self.get(
            action_id,
            actor_id=actor_id,
            conversation_id=conversation_id,
            user_id=user_id,
            now=now,
        )

    def claim_commit(
        self,
        action: PendingAction,
        *,
        approval_grant_id: uuid.UUID,
        now: datetime,
        user_id: uuid.UUID | None = None,
        lease_duration: timedelta = timedelta(seconds=60),
    ) -> CommitClaim:
        scope_user_id = user_id or action.user_id
        if scope_user_id != action.user_id:
            raise PendingActionError("permission_denied")
        at = _utc(now)
        lease_expires_at = at + lease_duration
        with self._sessions() as session, session.begin():
            current = session.scalar(
                select(PendingActionRecord).where(
                    PendingActionRecord.id == action.id,
                    PendingActionRecord.user_id == scope_user_id,
                )
            )
            if current is None:
                raise PendingActionError("pending_action_not_found")
            if current.status == "committed":
                raise PendingActionError("pending_action_committed")
            if current.status == "cancelled":
                raise PendingActionError("pending_action_cancelled")
            if current.status == "expired" or _utc(current.expires_at) <= at:
                if current.status not in {"committed", "cancelled", "expired"}:
                    current.status = "expired"
                    current.version_id += 1
                    current.updated_at = at
                raise PendingActionError("pending_action_expired")
            if current.status == "committing":
                lease = (
                    None
                    if current.commit_lease_expires_at is None
                    else _utc(current.commit_lease_expires_at)
                )
                if lease is not None and lease > at:
                    raise PendingActionError("commit_in_progress", retryable=True)
                expected_version = current.version_id
                expected_attempt = current.commit_attempt_no
                result = session.execute(
                    update(PendingActionRecord)
                    .where(
                        PendingActionRecord.id == action.id,
                        PendingActionRecord.user_id == scope_user_id,
                        PendingActionRecord.status == "committing",
                        PendingActionRecord.version_id == expected_version,
                        PendingActionRecord.commit_attempt_no == expected_attempt,
                        (
                            PendingActionRecord.commit_lease_expires_at.is_(None)
                            | (PendingActionRecord.commit_lease_expires_at <= at)
                        ),
                    )
                    .values(
                        version_id=expected_version + 1,
                        commit_attempt_no=expected_attempt + 1,
                        commit_lease_expires_at=lease_expires_at,
                        approval_grant_id=approval_grant_id,
                        updated_at=at,
                    )
                    .execution_options(synchronize_session=False)
                )
                next_version = expected_version + 1
                next_attempt = expected_attempt + 1
            elif current.status == "needs_confirmation":
                if current.version_id != action.version_id:
                    raise PendingActionError("pending_action_stale", retryable=True)
                result = session.execute(
                    update(PendingActionRecord)
                    .where(
                        PendingActionRecord.id == action.id,
                        PendingActionRecord.user_id == scope_user_id,
                        PendingActionRecord.status == "needs_confirmation",
                        PendingActionRecord.version_id == action.version_id,
                    )
                    .values(
                        status="committing",
                        version_id=action.version_id + 1,
                        commit_attempt_no=PendingActionRecord.commit_attempt_no + 1,
                        commit_lease_expires_at=lease_expires_at,
                        approval_grant_id=approval_grant_id,
                        updated_at=at,
                    )
                    .execution_options(synchronize_session=False)
                )
                next_version = action.version_id + 1
                next_attempt = current.commit_attempt_no + 1
            elif current.status == "needs_input":
                raise PendingActionError("confirmation_required")
            else:
                raise PendingActionError("pending_action_stale", retryable=True)
            if result.rowcount != 1:
                raise PendingActionError("pending_action_stale", retryable=True)
        return CommitClaim(
            pending_action_id=action.id,
            version_id=next_version,
            attempt_no=next_attempt,
            lease_expires_at=lease_expires_at,
        )

    def mark_committed(
        self,
        action_id: uuid.UUID,
        result: dict[str, Any],
        *,
        claim: CommitClaim,
        now: datetime,
        user_id: uuid.UUID | None = None,
    ) -> None:
        encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
        with self._sessions() as session, session.begin():
            statement = update(PendingActionRecord).where(
                PendingActionRecord.id == action_id,
                PendingActionRecord.status == "committing",
                PendingActionRecord.version_id == claim.version_id,
                PendingActionRecord.commit_attempt_no == claim.attempt_no,
            )
            if user_id is not None:
                statement = statement.where(PendingActionRecord.user_id == user_id)
            changed = session.execute(
                statement
                .values(
                    status="committed",
                    final_result_json=encoded,
                    version_id=claim.version_id + 1,
                    commit_lease_expires_at=None,
                    updated_at=_utc(now),
                )
            )
            if changed.rowcount != 1:
                raise PendingActionError("pending_action_stale", retryable=True)

    def cancel(self, action: PendingAction, *, now: datetime) -> PendingAction:
        if action.status == "committing":
            raise PendingActionError("commit_in_progress", retryable=True)
        if action.status == "committed":
            raise PendingActionError("pending_action_committed")
        if action.status == "cancelled":
            return action
        with self._sessions() as session, session.begin():
            result = session.execute(
                update(PendingActionRecord)
                .where(
                    PendingActionRecord.id == action.id,
                    PendingActionRecord.status.in_(("needs_input", "needs_confirmation")),
                    PendingActionRecord.version_id == action.version_id,
                )
                .values(status="cancelled", version_id=action.version_id + 1, updated_at=_utc(now))
            )
            if result.rowcount != 1:
                raise PendingActionError("pending_action_stale", retryable=True)
        return self.get(action.id, actor_id=action.actor_id, conversation_id=action.conversation_id, now=now)
