"""User-scoped P4-A conversations, memories, settings, and idempotency."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Callable, TypeVar

from sqlalchemy import and_, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from pydantic import ValidationError

from wife_system.host.contracts import ModuleSettingValue
from wife_system.host.events import EventEnvelope, InProcessEventBus
from wife_system.host.state_models import (
    ConversationMessageRecord,
    ConversationRecord,
    HostRequestReceiptRecord,
    MemoryCandidateRecord,
    MemoryItemRecord,
    ModuleSettingRecord,
)


T = TypeVar("T")
LOCAL_NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
MEMORY_KINDS = frozenset({"preference", "constraint", "goal", "communication_style"})
FORBIDDEN_MEMORY_TERMS = frozenset(
    {
        "amount",
        "amount_minor",
        "balance",
        "budget",
        "holding",
        "holdings",
        "market",
        "price",
        "password",
        "token",
        "api_key",
        "external_identity",
        "账目",
        "余额",
        "预算",
        "持仓",
        "行情",
        "密码",
        "密钥",
    }
)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


_SETTING_SECRET_KEYS = frozenset(
    {"apikey", "password", "secret", "token", "credential", "privatekey", "refreshtoken"}
)


def _setting_contains_secret(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).casefold().translate(str.maketrans("", "", "_- ."))
            if normalized in _SETTING_SECRET_KEYS or _setting_contains_secret(nested):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_setting_contains_secret(item) for item in value)
    return False


class HostStateError(RuntimeError):
    def __init__(self, code: str, *, status_code: int = 409, retryable: bool = False) -> None:
        self.code = code
        self.status_code = status_code
        self.retryable = retryable
        super().__init__(code)


@dataclass(frozen=True)
class HostKeys:
    values: dict[int, bytes]
    current_version: int = 1

    def current(self) -> bytes:
        key = self.values.get(self.current_version)
        if key is None or len(key) < 32:
            raise ValueError("a 32-byte host key is required")
        return key


class HostIdempotency:
    def __init__(self, keys: HostKeys) -> None:
        self._keys = keys

    def _digests(
        self, *, user_id: uuid.UUID, operation: str, raw_key: str, payload: dict[str, Any]
    ) -> tuple[str, str]:
        if not isinstance(raw_key, str):
            raise HostStateError("invalid_request", status_code=422)
        value = raw_key.strip()
        if not 1 <= len(value) <= 128 or any(ord(char) < 32 or ord(char) > 126 for char in value):
            raise HostStateError("invalid_request", status_code=422)
        secret = self._keys.current()
        prefix = f"wife.host.v1\0{user_id}\0{operation}\0".encode()
        digest = hmac.new(secret, prefix + value.encode("ascii"), hashlib.sha256).hexdigest()
        fingerprint = hmac.new(
            secret,
            prefix + b"payload\0" + _canonical(payload).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return digest, fingerprint

    def claim(
        self,
        session: Session,
        *,
        user_id: uuid.UUID,
        operation: str,
        raw_key: str,
        payload: dict[str, Any],
        now: datetime,
    ) -> tuple[HostRequestReceiptRecord, dict[str, Any] | None]:
        digest, fingerprint = self._digests(
            user_id=user_id, operation=operation, raw_key=raw_key, payload=payload
        )
        receipt = session.scalar(
            select(HostRequestReceiptRecord).where(
                HostRequestReceiptRecord.user_id == user_id,
                HostRequestReceiptRecord.operation == operation,
                HostRequestReceiptRecord.key_digest == digest,
            )
        )
        if receipt is not None:
            if receipt.request_fingerprint != fingerprint:
                raise HostStateError("idempotency_conflict")
            if receipt.result_json is None:
                raise HostStateError("concurrent_modification", retryable=True)
            return receipt, json.loads(receipt.result_json)
        receipt = HostRequestReceiptRecord(
            user_id=user_id,
            operation=operation,
            key_version=self._keys.current_version,
            key_digest=digest,
            request_fingerprint=fingerprint,
            created_at=_utc(now),
        )
        session.add(receipt)
        try:
            session.flush()
        except IntegrityError as exc:
            raise HostStateError("concurrent_modification", retryable=True) from exc
        return receipt, None

    @staticmethod
    def complete(receipt: HostRequestReceiptRecord, result: dict[str, Any], now: datetime) -> None:
        receipt.result_json = _canonical(result)
        receipt.completed_at = _utc(now)


@dataclass(frozen=True)
class CommandOutcome:
    """Separate the first response from the result that is safe to persist."""

    public_result: dict[str, Any]
    receipt_result: dict[str, Any]
    error_code: str | None = None


class HostCommandService:
    """Commit receipt claim, domain mutation, and safe result atomically."""

    def __init__(self, sessions: sessionmaker[Session], idempotency: HostIdempotency) -> None:
        self._sessions = sessions
        self._idempotency = idempotency

    def execute(
        self,
        *,
        user_id: uuid.UUID,
        operation: str,
        idempotency_key: str,
        payload: dict[str, Any],
        command: Callable[[Session], CommandOutcome | dict[str, Any]],
        now: datetime | None = None,
        replay_error: str | None = None,
    ) -> tuple[dict[str, Any], bool]:
        at = _utc(now or datetime.now(UTC))
        with self._sessions() as session, session.begin():
            receipt, replay = self._idempotency.claim(
                session,
                user_id=user_id,
                operation=operation,
                raw_key=idempotency_key,
                payload=payload,
                now=at,
            )
            if replay is not None:
                if replay_error is not None:
                    from wife_system.host.auth.errors import AuthError

                    raise AuthError(replay_error)
                replayed_error = replay.pop("__error_code", None)
                if replayed_error is not None:
                    from wife_system.host.auth.errors import AuthError

                    raise AuthError(replayed_error)
                return replay, True
            value = command(session)
            outcome = value if isinstance(value, CommandOutcome) else CommandOutcome(value, value)
            safe_result = dict(outcome.receipt_result)
            if outcome.error_code is not None:
                safe_result["__error_code"] = outcome.error_code
            self._idempotency.complete(receipt, safe_result, at)
        if outcome.error_code is not None:
            from wife_system.host.auth.errors import AuthError

            raise AuthError(outcome.error_code)
        return outcome.public_result, False


class ConversationService:
    def __init__(self, sessions: sessionmaker[Session], idempotency: HostIdempotency) -> None:
        self._sessions = sessions
        self._idempotency = idempotency

    def create(
        self,
        *,
        user_id: uuid.UUID,
        channel: str,
        module_id: str,
        profile_id: str,
        idempotency_key: str,
        now: datetime | None = None,
    ) -> tuple[ConversationRecord, bool]:
        at = _utc(now or datetime.now(UTC))
        payload = {"channel": channel, "module_id": module_id, "profile_id": profile_id}
        with self._sessions() as session, session.begin():
            receipt, replay = self._idempotency.claim(
                session,
                user_id=user_id,
                operation="conversation.create",
                raw_key=idempotency_key,
                payload=payload,
                now=at,
            )
            if replay is not None:
                row = session.get(ConversationRecord, uuid.UUID(replay["id"]))
                if row is None or row.user_id != user_id:
                    raise HostStateError("conversation_not_found", status_code=404)
                return row, True
            row = ConversationRecord(
                user_id=user_id,
                channel=channel,
                module_id=module_id,
                profile_id=profile_id,
                created_at=at,
            )
            session.add(row)
            session.flush()
            self._idempotency.complete(receipt, {"id": str(row.id)}, at)
        return row, False

    def get(self, conversation_id: uuid.UUID, *, user_id: uuid.UUID) -> ConversationRecord:
        with self._sessions() as session:
            row = session.scalar(
                select(ConversationRecord).where(
                    ConversationRecord.id == conversation_id,
                    ConversationRecord.user_id == user_id,
                )
            )
            if row is None:
                raise HostStateError("conversation_not_found", status_code=404)
            return row

    def list(
        self,
        *,
        user_id: uuid.UUID,
        limit: int = 50,
        before: tuple[datetime, uuid.UUID] | None = None,
    ) -> list[ConversationRecord]:
        if not 1 <= limit <= 101:
            raise HostStateError("invalid_request", status_code=422)
        statement = select(ConversationRecord).where(ConversationRecord.user_id == user_id)
        if before is not None:
            sort_time, item_id = before
            statement = statement.where(
                or_(
                    ConversationRecord.created_at < _utc(sort_time),
                    and_(
                        ConversationRecord.created_at == _utc(sort_time),
                        ConversationRecord.id > item_id,
                    ),
                )
            )
        with self._sessions() as session:
            return list(
                session.scalars(
                    statement.order_by(ConversationRecord.created_at.desc(), ConversationRecord.id).limit(limit)
                ).all()
            )

    def add_message(
        self,
        conversation_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
        role: str,
        content: str,
        sensitivity: str = "private",
        now: datetime | None = None,
    ) -> ConversationMessageRecord:
        encoded = content.encode("utf-8")
        if not encoded or len(encoded) > 32 * 1024:
            raise HostStateError("invalid_request", status_code=422)
        at = _utc(now or datetime.now(UTC))
        with self._sessions() as session, session.begin():
            conversation = session.scalar(
                select(ConversationRecord).where(
                    ConversationRecord.id == conversation_id,
                    ConversationRecord.user_id == user_id,
                )
            )
            if conversation is None:
                raise HostStateError("conversation_not_found", status_code=404)
            row = ConversationMessageRecord(
                user_id=user_id,
                conversation_id=conversation_id,
                role=role,
                content=content,
                content_digest=hashlib.sha256(encoded).hexdigest(),
                sensitivity=sensitivity,
                created_at=at,
            )
            conversation.last_message_at = at
            session.add(row)
        return row

    def messages(
        self,
        conversation_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
        now: datetime | None = None,
        limit: int = 50,
        before: tuple[datetime, uuid.UUID] | None = None,
    ) -> list[ConversationMessageRecord]:
        if not 1 <= limit <= 101:
            raise HostStateError("invalid_request", status_code=422)
        at = _utc(now or datetime.now(UTC))
        cutoff = at - timedelta(days=90)
        with self._sessions() as session, session.begin():
            conversation = session.scalar(
                select(ConversationRecord.id).where(
                    ConversationRecord.id == conversation_id,
                    ConversationRecord.user_id == user_id,
                )
            )
            if conversation is None:
                raise HostStateError("conversation_not_found", status_code=404)
            session.execute(
                update(ConversationMessageRecord)
                .where(
                    ConversationMessageRecord.user_id == user_id,
                    ConversationMessageRecord.conversation_id == conversation_id,
                    ConversationMessageRecord.created_at <= cutoff,
                    ConversationMessageRecord.deleted_at.is_(None),
                )
                .values(content="", deleted_at=at)
            )
            statement = select(ConversationMessageRecord).where(
                ConversationMessageRecord.user_id == user_id,
                ConversationMessageRecord.conversation_id == conversation_id,
                ConversationMessageRecord.created_at > cutoff,
                ConversationMessageRecord.deleted_at.is_(None),
            )
            if before is not None:
                sort_time, item_id = before
                statement = statement.where(
                    or_(
                        ConversationMessageRecord.created_at < _utc(sort_time),
                        and_(
                            ConversationMessageRecord.created_at == _utc(sort_time),
                            ConversationMessageRecord.id > item_id,
                        ),
                    )
                )
            return list(
                session.scalars(
                    statement.order_by(
                        ConversationMessageRecord.created_at.desc(), ConversationMessageRecord.id
                    ).limit(limit)
                ).all()
            )

    def bounded_history(
        self,
        conversation_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
        exclude_run_id: uuid.UUID | None = None,
        max_items: int = 20,
        max_utf8_bytes: int = 64 * 1024,
    ) -> list[ConversationMessageRecord]:
        """Return the newest bounded window in chronological provider order."""

        statement = select(ConversationMessageRecord).where(
            ConversationMessageRecord.user_id == user_id,
            ConversationMessageRecord.conversation_id == conversation_id,
            ConversationMessageRecord.deleted_at.is_(None),
        )
        if exclude_run_id is not None:
            statement = statement.where(
                or_(
                    ConversationMessageRecord.run_id.is_(None),
                    ConversationMessageRecord.run_id != exclude_run_id,
                )
            )
        with self._sessions() as session:
            rows = list(
                session.scalars(
                    statement.order_by(
                        ConversationMessageRecord.created_at.desc(),
                        ConversationMessageRecord.id,
                    ).limit(max_items)
                ).all()
            )
        selected: list[ConversationMessageRecord] = []
        used = 0
        for row in rows:
            size = len(row.content.encode("utf-8"))
            if used + size > max_utf8_bytes:
                continue
            selected.append(row)
            used += size
        selected.reverse()
        return selected


def _memory_is_forbidden(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).casefold() in FORBIDDEN_MEMORY_TERMS or _memory_is_forbidden(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_memory_is_forbidden(item) for item in value)
    if isinstance(value, str):
        lowered = value.casefold()
        return any(term in lowered for term in FORBIDDEN_MEMORY_TERMS)
    return False


class MemoryService:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        idempotency: HostIdempotency,
        events: InProcessEventBus,
        validate_grant: Callable[
            [uuid.UUID, str, str, str, str, str, str | None], str
        ]
        | None = None,
    ) -> None:
        self._sessions = sessions
        self._idempotency = idempotency
        self._events = events
        self._validate_grant = validate_grant

    @staticmethod
    def _validate_value(value: dict[str, Any]) -> str:
        if not isinstance(value, dict) or _memory_is_forbidden(value):
            raise HostStateError("memory_fact_forbidden", status_code=422)
        encoded = _canonical(value)
        if len(encoded.encode("utf-8")) > 4096:
            raise HostStateError("invalid_request", status_code=422)
        return encoded

    def propose(
        self,
        *,
        user_id: uuid.UUID,
        source_namespace: str,
        target_namespace: str,
        kind: str,
        value: dict[str, Any],
        tags: list[str],
        source_type: str,
        source_ref_digest: str,
        sensitivity: str,
        proposed_by_profile_id: str,
        now: datetime | None = None,
    ) -> MemoryCandidateRecord:
        if kind not in MEMORY_KINDS:
            raise HostStateError("invalid_request", status_code=422)
        if self._validate_grant is None:
            raise HostStateError("memory_namespace_forbidden", status_code=403)
        proposed_by_profile_version = self._validate_grant(
            user_id,
            proposed_by_profile_id,
            source_namespace,
            target_namespace,
            kind,
            "propose",
            None,
        )
        encoded = self._validate_value(value)
        at = _utc(now or datetime.now(UTC))
        row = MemoryCandidateRecord(
            user_id=user_id,
            source_namespace=source_namespace,
            target_namespace=target_namespace,
            kind=kind,
            value_json=encoded,
            tags_json=_canonical(sorted(set(tags))),
            source_type=source_type,
            source_ref_digest=source_ref_digest,
            sensitivity=sensitivity,
            proposed_by_profile_id=proposed_by_profile_id,
            proposed_by_profile_version=proposed_by_profile_version,
            created_at=at,
            expires_at=at + timedelta(days=30),
        )
        with self._sessions() as session, session.begin():
            session.add(row)
        return row

    def candidates(
        self,
        *,
        user_id: uuid.UUID,
        now: datetime | None = None,
        status: str | None = None,
        limit: int = 50,
        before: tuple[datetime, uuid.UUID] | None = None,
    ) -> list[MemoryCandidateRecord]:
        if not 1 <= limit <= 101:
            raise HostStateError("invalid_request", status_code=422)
        at = _utc(now or datetime.now(UTC))
        with self._sessions() as session, session.begin():
            session.execute(
                update(MemoryCandidateRecord)
                .where(
                    MemoryCandidateRecord.user_id == user_id,
                    MemoryCandidateRecord.status == "pending",
                    MemoryCandidateRecord.expires_at <= at,
                )
                .values(status="expired", value_json="{}", decided_at=at, version_id=MemoryCandidateRecord.version_id + 1)
            )
            statement = select(MemoryCandidateRecord).where(
                MemoryCandidateRecord.user_id == user_id
            )
            if status is not None:
                statement = statement.where(MemoryCandidateRecord.status == status)
            if before is not None:
                sort_time, item_id = before
                statement = statement.where(
                    or_(
                        MemoryCandidateRecord.created_at < _utc(sort_time),
                        and_(
                            MemoryCandidateRecord.created_at == _utc(sort_time),
                            MemoryCandidateRecord.id > item_id,
                        ),
                    )
                )
            return list(
                session.scalars(
                    statement.order_by(
                        MemoryCandidateRecord.created_at.desc(), MemoryCandidateRecord.id
                    ).limit(limit)
                ).all()
            )

    def decide(
        self,
        candidate_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
        confirm: bool,
        target_namespace: str | None,
        allowed_namespaces: frozenset[str],
        idempotency_key: str,
        now: datetime | None = None,
    ) -> tuple[MemoryItemRecord | None, bool]:
        at = _utc(now or datetime.now(UTC))
        operation = "memory.confirm" if confirm else "memory.reject"
        payload = {"candidate_id": str(candidate_id), "target_namespace": target_namespace}
        event: EventEnvelope | None = None
        deferred_error: HostStateError | None = None
        item: MemoryItemRecord | None = None
        with self._sessions() as session, session.begin():
            receipt, replay = self._idempotency.claim(
                session,
                user_id=user_id,
                operation=operation,
                raw_key=idempotency_key,
                payload=payload,
                now=at,
            )
            if replay is not None:
                if replay.get("error") == "memory_candidate_expired":
                    raise HostStateError("memory_candidate_expired", status_code=410)
                item_id = replay.get("item_id")
                return (None if item_id is None else session.get(MemoryItemRecord, uuid.UUID(item_id))), True
            candidate = session.scalar(
                select(MemoryCandidateRecord).where(
                    MemoryCandidateRecord.id == candidate_id,
                    MemoryCandidateRecord.user_id == user_id,
                )
            )
            if candidate is None:
                raise HostStateError("memory_candidate_not_found", status_code=404)
            if candidate.status != "pending":
                raise HostStateError("memory_candidate_conflict")
            expected_version = candidate.version_id
            event_status: str | None = None
            if _utc(candidate.expires_at) <= at:
                changed = session.execute(
                    update(MemoryCandidateRecord)
                    .where(
                        MemoryCandidateRecord.id == candidate.id,
                        MemoryCandidateRecord.user_id == user_id,
                        MemoryCandidateRecord.status == "pending",
                        MemoryCandidateRecord.version_id == expected_version,
                    )
                    .values(
                        status="expired",
                        value_json="{}",
                        decided_at=at,
                        version_id=expected_version + 1,
                    )
                    .execution_options(synchronize_session=False)
                )
                if changed.rowcount != 1:
                    raise HostStateError("memory_candidate_conflict")
                self._idempotency.complete(
                    receipt,
                    {"candidate_id": str(candidate.id), "error": "memory_candidate_expired"},
                    at,
                )
                deferred_error = HostStateError("memory_candidate_expired", status_code=410)
                event_status = "expired"
            elif confirm:
                if target_namespace is not None and target_namespace != candidate.target_namespace:
                    raise HostStateError("memory_namespace_forbidden", status_code=403)
                namespace = candidate.target_namespace
                if self._validate_grant is None:
                    raise HostStateError("memory_candidate_conflict")
                self._validate_grant(
                    user_id,
                    candidate.proposed_by_profile_id,
                    candidate.source_namespace,
                    namespace,
                    candidate.kind,
                    "propose",
                    candidate.proposed_by_profile_version,
                )
                if namespace not in allowed_namespaces:
                    raise HostStateError("memory_namespace_forbidden", status_code=403)
                item = MemoryItemRecord(
                    user_id=user_id,
                    namespace=namespace,
                    kind=candidate.kind,
                    value_json=candidate.value_json,
                    tags_json=candidate.tags_json,
                    source_type=candidate.source_type,
                    source_ref_digest=candidate.source_ref_digest,
                    sensitivity=candidate.sensitivity,
                    confirmed_at=at,
                    audit_id=uuid.uuid4(),
                )
                session.add(item)
                session.flush()
                changed = session.execute(
                    update(MemoryCandidateRecord)
                    .where(
                        MemoryCandidateRecord.id == candidate.id,
                        MemoryCandidateRecord.user_id == user_id,
                        MemoryCandidateRecord.status == "pending",
                        MemoryCandidateRecord.version_id == expected_version,
                    )
                    .values(
                        status="confirmed",
                        memory_item_id=item.id,
                        audit_id=item.audit_id,
                        decided_at=at,
                        version_id=expected_version + 1,
                    )
                    .execution_options(synchronize_session=False)
                )
                if changed.rowcount != 1:
                    raise HostStateError("memory_candidate_conflict")
                event_status = "confirmed"
            elif deferred_error is None:
                changed = session.execute(
                    update(MemoryCandidateRecord)
                    .where(
                        MemoryCandidateRecord.id == candidate.id,
                        MemoryCandidateRecord.user_id == user_id,
                        MemoryCandidateRecord.status == "pending",
                        MemoryCandidateRecord.version_id == expected_version,
                    )
                    .values(
                        status="rejected",
                        value_json="{}",
                        audit_id=uuid.uuid4(),
                        decided_at=at,
                        version_id=expected_version + 1,
                    )
                    .execution_options(synchronize_session=False)
                )
                if changed.rowcount != 1:
                    raise HostStateError("memory_candidate_conflict")
                event_status = "rejected"
            if deferred_error is None:
                result = {"candidate_id": str(candidate.id), "item_id": None if item is None else str(item.id)}
                self._idempotency.complete(receipt, result, at)
                event = EventEnvelope(
                    event_id=uuid.uuid4(),
                    event_type="memory.changed@1",
                    occurred_at=at,
                    user_id=user_id,
                    producer_module="host_core",
                    correlation_id=str(uuid.uuid4()),
                    idempotency_digest=receipt.key_digest,
                    sensitivity=candidate.sensitivity,
                    payload={
                        "object_id": str(candidate.id),
                        "namespace": candidate.target_namespace,
                        "status": event_status,
                        "version_id": expected_version + 1,
                    },
                )
        if deferred_error is not None:
            raise deferred_error
        if event is not None:
            self._events.publish(event)
        return item, False

    def retrieve(
        self,
        *,
        user_id: uuid.UUID,
        allowed_namespaces: frozenset[str],
        kinds: frozenset[str] | None = None,
        tags: frozenset[str] = frozenset(),
        profile_limit: int = 8,
        now: datetime | None = None,
    ) -> list[MemoryItemRecord]:
        limit = min(max(profile_limit, 0), 8)
        if limit == 0 or not allowed_namespaces:
            return []
        at = _utc(now or datetime.now(UTC))
        statement = select(MemoryItemRecord).where(
            MemoryItemRecord.user_id == user_id,
            MemoryItemRecord.namespace.in_(allowed_namespaces),
            MemoryItemRecord.status == "active",
            or_(MemoryItemRecord.expires_at.is_(None), MemoryItemRecord.expires_at > at),
        )
        if kinds:
            statement = statement.where(MemoryItemRecord.kind.in_(kinds))
        with self._sessions() as session:
            rows = list(session.scalars(statement).all())
        rows.sort(
            key=lambda row: (
                -len(tags.intersection(json.loads(row.tags_json))),
                -_utc(row.confirmed_at).timestamp(),
                str(row.id),
            )
        )
        return rows[:limit]

    def invalidate(
        self,
        item_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
        expected_version: int,
        idempotency_key: str,
        now: datetime | None = None,
    ) -> tuple[MemoryItemRecord, bool]:
        """Clear and invalidate one active memory under a version CAS."""

        at = _utc(now or datetime.now(UTC))
        event: EventEnvelope | None = None
        with self._sessions() as session, session.begin():
            receipt, replay = self._idempotency.claim(
                session,
                user_id=user_id,
                operation="memory.invalidate",
                raw_key=idempotency_key,
                payload={
                    "item_id": str(item_id),
                    "expected_version": expected_version,
                },
                now=at,
            )
            if replay is not None:
                row = session.get(MemoryItemRecord, item_id)
                if row is None or row.user_id != user_id:
                    raise HostStateError("memory_not_found", status_code=404)
                return row, True
            item = session.scalar(
                select(MemoryItemRecord).where(
                    MemoryItemRecord.id == item_id,
                    MemoryItemRecord.user_id == user_id,
                )
            )
            if item is None:
                raise HostStateError("memory_not_found", status_code=404)
            changed = session.execute(
                update(MemoryItemRecord)
                .where(
                    MemoryItemRecord.id == item_id,
                    MemoryItemRecord.user_id == user_id,
                    MemoryItemRecord.status == "active",
                    MemoryItemRecord.version_id == expected_version,
                )
                .values(
                    value_json="{}",
                    tags_json="[]",
                    status="invalidated",
                    version_id=expected_version + 1,
                )
                .execution_options(synchronize_session=False)
            )
            if changed.rowcount != 1:
                raise HostStateError("memory_version_conflict")
            self._idempotency.complete(
                receipt,
                {
                    "item_id": str(item_id),
                    "status": "invalidated",
                    "version_id": expected_version + 1,
                },
                at,
            )
            session.refresh(item)
            event = EventEnvelope(
                event_id=uuid.uuid4(),
                event_type="memory.changed@1",
                occurred_at=at,
                user_id=user_id,
                producer_module="host_core",
                correlation_id=str(uuid.uuid4()),
                idempotency_digest=receipt.key_digest,
                sensitivity=item.sensitivity,
                payload={
                    "object_id": str(item_id),
                    "namespace": item.namespace,
                    "status": "invalidated",
                    "version_id": expected_version + 1,
                },
            )
        if event is not None:
            self._events.publish(event)
        return item, False

    def delete(
        self,
        item_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
        idempotency_key: str,
        expected_version: int | None = None,
        now: datetime | None = None,
    ) -> bool:
        at = _utc(now or datetime.now(UTC))
        event: EventEnvelope | None = None
        with self._sessions() as session, session.begin():
            receipt, replay = self._idempotency.claim(
                session,
                user_id=user_id,
                operation="memory.delete",
                raw_key=idempotency_key,
                payload={"item_id": str(item_id)},
                now=at,
            )
            if replay is not None:
                return True
            item = session.scalar(
                select(MemoryItemRecord).where(
                    MemoryItemRecord.id == item_id,
                    MemoryItemRecord.user_id == user_id,
                )
            )
            if item is None:
                raise HostStateError("memory_not_found", status_code=404)
            if item.status == "deleted":
                self._idempotency.complete(
                    receipt, {"item_id": str(item_id), "deleted": True}, at
                )
                return True
            version = item.version_id if expected_version is None else expected_version
            changed = session.execute(
                update(MemoryItemRecord)
                .where(
                    MemoryItemRecord.id == item_id,
                    MemoryItemRecord.user_id == user_id,
                    MemoryItemRecord.version_id == version,
                    MemoryItemRecord.status.in_(("active", "superseded", "invalidated")),
                )
                .values(
                    value_json="{}",
                    tags_json="[]",
                    status="deleted",
                    deleted_at=at,
                    version_id=version + 1,
                )
                .execution_options(synchronize_session=False)
            )
            if changed.rowcount != 1:
                raise HostStateError("memory_version_conflict")
            self._idempotency.complete(receipt, {"item_id": str(item_id), "deleted": True}, at)
            event = EventEnvelope(
                event_id=uuid.uuid4(),
                event_type="memory.changed@1",
                occurred_at=at,
                user_id=user_id,
                producer_module="host_core",
                correlation_id=str(uuid.uuid4()),
                idempotency_digest=receipt.key_digest,
                sensitivity=item.sensitivity,
                payload={
                    "object_id": str(item_id),
                    "namespace": item.namespace,
                    "status": "deleted",
                    "version_id": version + 1,
                },
            )
        if event is not None:
            self._events.publish(event)
        return True

    def supersede(
        self,
        item_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
        value: dict[str, Any],
        expected_version: int,
        idempotency_key: str,
        now: datetime | None = None,
    ) -> tuple[MemoryItemRecord, bool]:
        """Atomically replace one active fact and link its tombstone."""

        encoded = self._validate_value(value)
        at = _utc(now or datetime.now(UTC))
        event: EventEnvelope | None = None
        with self._sessions() as session, session.begin():
            receipt, replay = self._idempotency.claim(
                session,
                user_id=user_id,
                operation="memory.supersede",
                raw_key=idempotency_key,
                payload={
                    "item_id": str(item_id),
                    "expected_version": expected_version,
                    "value": value,
                },
                now=at,
            )
            if replay is not None:
                row = session.get(MemoryItemRecord, uuid.UUID(replay["replacement_id"]))
                if row is None or row.user_id != user_id:
                    raise HostStateError("memory_not_found", status_code=404)
                return row, True
            current = session.scalar(
                select(MemoryItemRecord).where(
                    MemoryItemRecord.id == item_id,
                    MemoryItemRecord.user_id == user_id,
                )
            )
            if current is None:
                raise HostStateError("memory_not_found", status_code=404)
            replacement = MemoryItemRecord(
                user_id=user_id,
                namespace=current.namespace,
                kind=current.kind,
                value_json=encoded,
                tags_json=current.tags_json,
                source_type=current.source_type,
                source_ref_digest=current.source_ref_digest,
                sensitivity=current.sensitivity,
                confirmed_at=at,
                expires_at=current.expires_at,
                audit_id=uuid.uuid4(),
            )
            session.add(replacement)
            session.flush()
            changed = session.execute(
                update(MemoryItemRecord)
                .where(
                    MemoryItemRecord.id == item_id,
                    MemoryItemRecord.user_id == user_id,
                    MemoryItemRecord.status == "active",
                    MemoryItemRecord.version_id == expected_version,
                )
                .values(
                    status="superseded",
                    superseded_by_id=replacement.id,
                    version_id=expected_version + 1,
                )
                .execution_options(synchronize_session=False)
            )
            if changed.rowcount != 1:
                raise HostStateError("memory_version_conflict")
            self._idempotency.complete(
                receipt,
                {"replacement_id": str(replacement.id)},
                at,
            )
            event = EventEnvelope(
                event_id=uuid.uuid4(),
                event_type="memory.changed@1",
                occurred_at=at,
                user_id=user_id,
                producer_module="host_core",
                correlation_id=str(uuid.uuid4()),
                idempotency_digest=receipt.key_digest,
                sensitivity=current.sensitivity,
                payload={
                    "object_id": str(item_id),
                    "namespace": current.namespace,
                    "status": "superseded",
                    "version_id": expected_version + 1,
                },
            )
        if event is not None:
            self._events.publish(event)
        return replacement, False


class ModuleSettingService:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        idempotency: HostIdempotency,
        events: InProcessEventBus,
        validate: Callable[[str, str, dict[str, Any], int], None],
    ) -> None:
        self._sessions = sessions
        self._idempotency = idempotency
        self._events = events
        self._validate = validate

    def get(self, *, user_id: uuid.UUID, module_id: str) -> list[ModuleSettingRecord]:
        with self._sessions() as session:
            return list(
                session.scalars(
                    select(ModuleSettingRecord)
                    .where(
                        ModuleSettingRecord.user_id == user_id,
                        ModuleSettingRecord.module_id == module_id,
                    )
                    .order_by(ModuleSettingRecord.key)
                ).all()
            )

    def put(
        self,
        *,
        user_id: uuid.UUID,
        module_id: str,
        key: str,
        value: dict[str, Any],
        schema_version: int,
        expected_version: int | None,
        idempotency_key: str,
        now: datetime | None = None,
    ) -> tuple[ModuleSettingRecord, bool]:
        if not LOCAL_NAME.fullmatch(key):
            raise HostStateError("invalid_request", status_code=422)
        if _setting_contains_secret(value):
            raise HostStateError("setting_secret_forbidden", status_code=422)
        try:
            validated = ModuleSettingValue.model_validate(
                {
                    "module_id": module_id,
                    "key": key,
                    "schema_version": schema_version,
                    "version_id": max(expected_version or 1, 1),
                    "value": value,
                }
            )
            encoded = _canonical(validated.value)
        except (ValidationError, TypeError, ValueError):
            raise HostStateError("invalid_setting", status_code=422) from None
        self._validate(module_id, key, value, schema_version)
        at = _utc(now or datetime.now(UTC))
        event: EventEnvelope | None = None
        payload = {
            "module_id": module_id,
            "key": key,
            "value": value,
            "schema_version": schema_version,
            "expected_version": expected_version,
        }
        with self._sessions() as session, session.begin():
            receipt, replay = self._idempotency.claim(
                session,
                user_id=user_id,
                operation="setting.put",
                raw_key=idempotency_key,
                payload=payload,
                now=at,
            )
            if replay is not None:
                row = session.get(ModuleSettingRecord, uuid.UUID(replay["id"]))
                if row is None or row.user_id != user_id:
                    raise HostStateError("setting_not_found", status_code=404)
                return row, True
            row = session.scalar(
                select(ModuleSettingRecord).where(
                    ModuleSettingRecord.user_id == user_id,
                    ModuleSettingRecord.module_id == module_id,
                    ModuleSettingRecord.key == key,
                )
            )
            if row is None:
                if expected_version not in (None, 0):
                    raise HostStateError("setting_version_conflict")
                row = ModuleSettingRecord(
                    user_id=user_id,
                    module_id=module_id,
                    key=key,
                    value_json=encoded,
                    schema_version=schema_version,
                    version_id=1,
                    updated_at=at,
                )
                session.add(row)
                session.flush()
            else:
                if expected_version != row.version_id:
                    raise HostStateError("setting_version_conflict")
                row.value_json = encoded
                row.schema_version = schema_version
                row.version_id += 1
                row.updated_at = at
            self._idempotency.complete(receipt, {"id": str(row.id)}, at)
            event = EventEnvelope(
                event_id=uuid.uuid4(),
                event_type="module.setting_changed@1",
                occurred_at=at,
                user_id=user_id,
                producer_module="host_core",
                correlation_id=str(uuid.uuid4()),
                idempotency_digest=receipt.key_digest,
                sensitivity="private",
                payload={"module_id": module_id, "key": key, "version_id": row.version_id},
            )
        if event is not None:
            self._events.publish(event)
        return row, False
