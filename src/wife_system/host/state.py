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
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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


class HostCommandService:
    """Persist replayable results for Host commands whose domain service owns its transaction."""

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
        command: Callable[[], dict[str, Any]],
        now: datetime | None = None,
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
            receipt_id = receipt.id
        if replay is not None:
            return replay, True
        try:
            result = command()
        except Exception:
            with self._sessions() as session, session.begin():
                incomplete = session.get(HostRequestReceiptRecord, receipt_id)
                if incomplete is not None and incomplete.result_json is None:
                    session.delete(incomplete)
            raise
        with self._sessions() as session, session.begin():
            stored = session.get(HostRequestReceiptRecord, receipt_id)
            if stored is None:
                raise HostStateError("persistence_error", status_code=503, retryable=True)
            self._idempotency.complete(stored, result, at)
        return result, False


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
        if not 1 <= limit <= 100:
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
        if not 1 <= limit <= 100:
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
    ) -> None:
        self._sessions = sessions
        self._idempotency = idempotency
        self._events = events

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
        if kind not in MEMORY_KINDS or target_namespace == "shared.confirmed":
            raise HostStateError("invalid_request", status_code=422)
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
            created_at=at,
            expires_at=at + timedelta(days=30),
        )
        with self._sessions() as session, session.begin():
            session.add(row)
        return row

    def candidates(
        self, *, user_id: uuid.UUID, now: datetime | None = None
    ) -> list[MemoryCandidateRecord]:
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
            return list(
                session.scalars(
                    select(MemoryCandidateRecord)
                    .where(MemoryCandidateRecord.user_id == user_id)
                    .order_by(MemoryCandidateRecord.created_at.desc(), MemoryCandidateRecord.id)
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
            if _utc(candidate.expires_at) <= at:
                candidate.status = "expired"
                candidate.value_json = "{}"
                candidate.decided_at = at
                candidate.version_id += 1
                self._idempotency.complete(
                    receipt,
                    {"candidate_id": str(candidate.id), "error": "memory_candidate_expired"},
                    at,
                )
                deferred_error = HostStateError("memory_candidate_expired", status_code=410)
            elif confirm:
                namespace = target_namespace or candidate.target_namespace
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
                candidate.status = "confirmed"
                candidate.memory_item_id = item.id
                candidate.audit_id = item.audit_id
            elif deferred_error is None:
                candidate.status = "rejected"
                candidate.value_json = "{}"
                candidate.audit_id = uuid.uuid4()
            if deferred_error is None:
                candidate.decided_at = at
                candidate.version_id += 1
                result = {"candidate_id": str(candidate.id), "item_id": None if item is None else str(item.id)}
                self._idempotency.complete(receipt, result, at)
                event = EventEnvelope(
                    event_id=uuid.uuid4(),
                    event_type="memory.changed@1",
                    occurred_at=at,
                    user_id=user_id,
                    producer_module=candidate.source_namespace.split(".", 1)[0],
                    correlation_id=str(uuid.uuid4()),
                    idempotency_digest=receipt.key_digest,
                    sensitivity=candidate.sensitivity,
                    payload={"candidate_id": str(candidate.id), "status": candidate.status},
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

    def delete(
        self,
        item_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
        idempotency_key: str,
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
            item.value_json = "{}"
            item.tags_json = "[]"
            item.status = "deleted"
            item.deleted_at = at
            item.version_id += 1
            self._idempotency.complete(receipt, {"item_id": str(item_id), "deleted": True}, at)
            event = EventEnvelope(
                event_id=uuid.uuid4(),
                event_type="memory.changed@1",
                occurred_at=at,
                user_id=user_id,
                producer_module=item.namespace.split(".", 1)[0],
                correlation_id=str(uuid.uuid4()),
                idempotency_digest=receipt.key_digest,
                sensitivity=item.sensitivity,
                payload={"item_id": str(item_id), "status": "deleted"},
            )
        if event is not None:
            self._events.publish(event)
        return True


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
        encoded = _canonical(value)
        if len(encoded.encode("utf-8")) > 8192:
            raise HostStateError("invalid_request", status_code=422)
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
                producer_module=module_id,
                correlation_id=str(uuid.uuid4()),
                idempotency_digest=receipt.key_digest,
                sensitivity="private",
                payload={"module_id": module_id, "key": key, "version_id": row.version_id},
            )
        if event is not None:
            self._events.publish(event)
        return row, False
