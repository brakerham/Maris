from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from wife_system.finance.db import Base, make_engine, make_session_factory
from wife_system.host.auth.models import AppUser
from wife_system.host.context import HostRunContext, PrincipalContext
from wife_system.host.cursor import CursorCodec, InvalidCursorError
from wife_system.host.events import EventEnvelope, InProcessEventBus
from wife_system.host.state import (
    ConversationService,
    HostIdempotency,
    HostKeys,
    HostStateError,
    MemoryService,
    ModuleSettingService,
)
from wife_system.host.state_models import MemoryItemRecord


NOW = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)


@pytest.fixture
def state(tmp_path):
    engine = make_engine(f"sqlite:///{(tmp_path / 'host-state.sqlite3').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = make_session_factory(engine)
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    with sessions() as session, session.begin():
        session.add_all(
            [
                AppUser(id=user_a, handle="owner_a", status="active", bootstrap_marker=None),
                AppUser(id=user_b, handle="owner_b", status="active", bootstrap_marker=None),
            ]
        )
    keys = HostKeys({1: b"host-state-test-key" * 2})
    events = InProcessEventBus()
    yield sessions, user_a, user_b, HostIdempotency(keys), events
    engine.dispose()


def test_trusted_context_is_strict_frozen_and_timezone_aware() -> None:
    principal = PrincipalContext(
        user_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        device_id=uuid.uuid4(),
        channel="api_test",
        permissions=frozenset({"finance:read"}),
        authenticated_at=NOW,
    )
    assert principal.authenticated_at == NOW
    with pytest.raises(ValidationError):
        PrincipalContext.model_validate({**principal.model_dump(), "owner_id": str(uuid.uuid4())})
    with pytest.raises(ValidationError):
        HostRunContext(
            **principal.model_dump(),
            agent_run_id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            module_id="daily_finance",
            profile_id="daily_finance.assistant@1",
            source_system="desktop_chat",
            source_event_id=None,
            received_at=datetime(2026, 9, 20, 12, 0),
        )


def test_cursor_is_bound_to_endpoint_and_user() -> None:
    codec = CursorCodec(b"cursor-test-key" * 3)
    owner = uuid.uuid4()
    item = uuid.uuid4()
    value = codec.encode(endpoint="conversations", user_id=owner, sort_time=NOW, item_id=item)
    assert codec.decode(value, endpoint="conversations", user_id=owner) == (NOW, item)
    with pytest.raises(InvalidCursorError, match="invalid_cursor"):
        codec.decode(value, endpoint="memories", user_id=owner)
    with pytest.raises(InvalidCursorError, match="invalid_cursor"):
        codec.decode(value, endpoint="conversations", user_id=uuid.uuid4())


def test_event_bus_preserves_order_and_isolates_handler_failure(caplog) -> None:
    bus = InProcessEventBus()
    seen: list[str] = []

    def first(_: EventEnvelope) -> None:
        seen.append("first")
        raise RuntimeError("private diagnostic")

    bus.subscribe("memory.changed@1", first)
    bus.subscribe("memory.changed@1", lambda _: seen.append("second"))
    bus.publish(
        EventEnvelope(
            event_id=uuid.uuid4(),
            event_type="memory.changed@1",
            occurred_at=NOW,
            user_id=uuid.uuid4(),
            producer_module="daily_finance",
            correlation_id=str(uuid.uuid4()),
            idempotency_digest="a" * 64,
            sensitivity="private",
            payload={"status": "confirmed"},
        )
    )
    assert seen == ["first", "second"]
    assert "private diagnostic" not in caplog.text


def test_conversation_idempotency_scope_and_message_retention(state) -> None:
    sessions, user_a, user_b, idempotency, _ = state
    service = ConversationService(sessions, idempotency)
    conversation, replayed = service.create(
        user_id=user_a,
        channel="api_test",
        module_id="daily_finance",
        profile_id="daily_finance.assistant@1",
        idempotency_key="conversation-1",
        now=NOW,
    )
    replay, was_replayed = service.create(
        user_id=user_a,
        channel="api_test",
        module_id="daily_finance",
        profile_id="daily_finance.assistant@1",
        idempotency_key="conversation-1",
        now=NOW,
    )
    assert not replayed and was_replayed and replay.id == conversation.id
    with pytest.raises(HostStateError, match="idempotency_conflict"):
        service.create(
            user_id=user_a,
            channel="api_test",
            module_id="daily_finance",
            profile_id="daily_finance.other@1",
            idempotency_key="conversation-1",
            now=NOW,
        )
    with pytest.raises(HostStateError, match="conversation_not_found"):
        service.get(conversation.id, user_id=user_b)

    expired = service.add_message(
        conversation.id,
        user_id=user_a,
        role="user",
        content="old private message",
        now=NOW - timedelta(days=90),
    )
    current = service.add_message(
        conversation.id,
        user_id=user_a,
        role="assistant",
        content="current",
        now=NOW - timedelta(days=90) + timedelta(microseconds=1),
    )
    assert [row.id for row in service.messages(conversation.id, user_id=user_a, now=NOW)] == [current.id]
    with sessions() as session:
        tombstone = session.get(type(expired), expired.id)
        assert tombstone is not None and tombstone.content == ""
        assert tombstone.deleted_at is not None and tombstone.deleted_at.replace(tzinfo=UTC) == NOW


def test_memory_confirmation_retrieval_and_tombstone(state) -> None:
    sessions, user_a, user_b, idempotency, events = state
    service = MemoryService(sessions, idempotency, events)
    with pytest.raises(HostStateError, match="memory_fact_forbidden"):
        service.propose(
            user_id=user_a,
            source_namespace="daily_finance.candidates",
            target_namespace="daily_finance.confirmed",
            kind="preference",
            value={"balance": "100.00"},
            tags=[],
            source_type="conversation",
            source_ref_digest="a" * 64,
            sensitivity="private",
            proposed_by_profile_id="daily_finance.assistant@1",
            now=NOW,
        )
    candidate = service.propose(
        user_id=user_a,
        source_namespace="daily_finance.candidates",
        target_namespace="daily_finance.confirmed",
        kind="preference",
        value={"drink": "ice tea"},
        tags=["drink", "daily"],
        source_type="conversation",
        source_ref_digest="b" * 64,
        sensitivity="private",
        proposed_by_profile_id="daily_finance.assistant@1",
        now=NOW,
    )
    item, replayed = service.decide(
        candidate.id,
        user_id=user_a,
        confirm=True,
        target_namespace="shared.confirmed",
        allowed_namespaces=frozenset({"shared.confirmed"}),
        idempotency_key="memory-confirm-1",
        now=NOW,
    )
    assert item is not None and not replayed and item.namespace == "shared.confirmed"
    assert service.retrieve(
        user_id=user_a,
        allowed_namespaces=frozenset({"shared.confirmed"}),
        tags=frozenset({"drink"}),
        profile_limit=8,
        now=NOW,
    )[0].id == item.id
    assert service.retrieve(
        user_id=user_b,
        allowed_namespaces=frozenset({"shared.confirmed"}),
        now=NOW,
    ) == []
    assert service.delete(item.id, user_id=user_a, idempotency_key="memory-delete-1", now=NOW)
    with sessions() as session:
        deleted = session.get(MemoryItemRecord, item.id)
        assert deleted is not None
        assert deleted.value_json == "{}" and deleted.tags_json == "[]"
        assert deleted.status == "deleted" and deleted.audit_id is not None


def test_memory_expiry_at_exact_boundary_and_limit_eight(state) -> None:
    sessions, user_a, _, idempotency, events = state
    service = MemoryService(sessions, idempotency, events)
    expiring = service.propose(
        user_id=user_a,
        source_namespace="daily_finance.candidates",
        target_namespace="daily_finance.confirmed",
        kind="goal",
        value={"description": "practice weekly"},
        tags=[],
        source_type="conversation",
        source_ref_digest="c" * 64,
        sensitivity="private",
        proposed_by_profile_id="daily_finance.assistant@1",
        now=NOW,
    )
    rows = service.candidates(user_id=user_a, now=NOW + timedelta(days=30))
    expired = next(row for row in rows if row.id == expiring.id)
    assert expired.status == "expired" and expired.value_json == "{}"

    with sessions() as session, session.begin():
        for index in range(10):
            session.add(
                MemoryItemRecord(
                    user_id=user_a,
                    namespace="daily_finance.confirmed",
                    kind="goal",
                    value_json=json.dumps({"index": index}),
                    tags_json='["matched"]',
                    source_type="test",
                    source_ref_digest=f"{index:064d}",
                    sensitivity="private",
                    confirmed_at=NOW + timedelta(seconds=index),
                    audit_id=uuid.uuid4(),
                )
            )
    items = service.retrieve(
        user_id=user_a,
        allowed_namespaces=frozenset({"daily_finance.confirmed"}),
        tags=frozenset({"matched"}),
        profile_limit=99,
        now=NOW + timedelta(minutes=1),
    )
    assert len(items) == 8
    assert [json.loads(item.value_json)["index"] for item in items] == list(range(9, 1, -1))


def test_module_setting_schema_cas_idempotency_and_user_scope(state) -> None:
    _, user_a, user_b, idempotency, events = state
    published: list[EventEnvelope] = []
    events.subscribe("module.setting_changed@1", published.append)

    def validate(module_id: str, key: str, value: dict, schema_version: int) -> None:
        if module_id != "daily_finance" or key != "assistant_mode" or schema_version != 1:
            raise HostStateError("invalid_setting", status_code=422)
        if set(value) != {"enabled"} or not isinstance(value["enabled"], bool):
            raise HostStateError("invalid_setting", status_code=422)

    service = ModuleSettingService(state[0], idempotency, events, validate)
    row, replayed = service.put(
        user_id=user_a,
        module_id="daily_finance",
        key="assistant_mode",
        value={"enabled": True},
        schema_version=1,
        expected_version=None,
        idempotency_key="setting-1",
        now=NOW,
    )
    replay, was_replayed = service.put(
        user_id=user_a,
        module_id="daily_finance",
        key="assistant_mode",
        value={"enabled": True},
        schema_version=1,
        expected_version=None,
        idempotency_key="setting-1",
        now=NOW,
    )
    assert not replayed and was_replayed and replay.id == row.id
    assert len(published) == 1
    assert service.get(user_id=user_b, module_id="daily_finance") == []
    with pytest.raises(HostStateError, match="setting_version_conflict"):
        service.put(
            user_id=user_a,
            module_id="daily_finance",
            key="assistant_mode",
            value={"enabled": False},
            schema_version=1,
            expected_version=99,
            idempotency_key="setting-2",
            now=NOW,
        )
