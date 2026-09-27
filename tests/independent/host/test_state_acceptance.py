from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from wife_system.agent.models import AgentRunRecord
from wife_system.host.auth.models import AppUser
from wife_system.host.auth.errors import AuthError
from wife_system.host.auth.models import ChannelBindingCode
from wife_system.host.cursor import CursorCodec, InvalidCursorError
from wife_system.host.state import HostStateError
from wife_system.host.state_models import (
    ConversationRecord,
    HostRequestReceiptRecord,
    MemoryItemRecord,
    ModuleSettingRecord,
)
from wife_system.host.workflows import RunLeaseCoordinator, WorkflowError

from .conftest import owner_headers


NOW = datetime(2026, 9, 26, 15, 0, tzinfo=UTC)


def _owner(runtime) -> uuid.UUID:
    with runtime.sessions() as session:
        return session.scalar(select(AppUser.id).where(AppUser.status == "active"))


def test_c11_conversation_replay_conflict_retention_and_scope(host_stack) -> None:
    client, runtime, _ = host_stack
    owner_headers(client)
    owner = _owner(runtime)
    other = uuid.uuid4()
    with runtime.sessions() as session, session.begin():
        session.add(AppUser(id=other, handle="state_other", status="active"))

    created, replay = runtime.conversations.create(
        user_id=owner,
        channel="api_test",
        module_id="daily_finance",
        profile_id="daily_finance.assistant@1",
        idempotency_key="conversation-key",
        now=NOW,
    )
    same, replayed = runtime.conversations.create(
        user_id=owner,
        channel="api_test",
        module_id="daily_finance",
        profile_id="daily_finance.assistant@1",
        idempotency_key="conversation-key",
        now=NOW,
    )
    assert not replay and replayed and same.id == created.id
    with pytest.raises(HostStateError, match="idempotency_conflict"):
        runtime.conversations.create(
            user_id=owner,
            channel="api_test",
            module_id="daily_finance",
            profile_id="daily_finance.other@1",
            idempotency_key="conversation-key",
            now=NOW,
        )
    with pytest.raises(HostStateError, match="conversation_not_found"):
        runtime.conversations.get(created.id, user_id=other)

    old = runtime.conversations.add_message(
        created.id, user_id=owner, role="user", content="virtual old message", now=NOW - timedelta(days=90)
    )
    current = runtime.conversations.add_message(
        created.id,
        user_id=owner,
        role="assistant",
        content="virtual current message",
        now=NOW - timedelta(days=90) + timedelta(microseconds=1),
    )
    assert [row.id for row in runtime.conversations.messages(created.id, user_id=owner, now=NOW)] == [current.id]
    with runtime.sessions() as session:
        tombstone = session.get(type(old), old.id)
        assert tombstone.content == "" and tombstone.deleted_at is not None


def test_c11_cursor_is_endpoint_and_owner_bound() -> None:
    codec = CursorCodec(b"independent-cursor-key" * 2)
    owner, item = uuid.uuid4(), uuid.uuid4()
    token = codec.encode(endpoint="conversations", user_id=owner, sort_time=NOW, item_id=item)
    assert codec.decode(token, endpoint="conversations", user_id=owner) == (NOW, item)
    for endpoint, user_id in (("memories", owner), ("conversations", uuid.uuid4())):
        with pytest.raises(InvalidCursorError, match="invalid_cursor"):
            codec.decode(token, endpoint=endpoint, user_id=user_id)


def test_c11_memory_requires_confirmation_rechecks_grant_and_tombstones(host_stack) -> None:
    client, runtime, _ = host_stack
    owner_headers(client)
    owner = _owner(runtime)
    with pytest.raises(HostStateError, match="memory_fact_forbidden"):
        runtime.memories.propose(
            user_id=owner,
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
    candidate = runtime.memories.propose(
        user_id=owner,
        source_namespace="daily_finance.candidates",
        target_namespace="daily_finance.confirmed",
        kind="preference",
        value={"drink": "virtual tea"},
        tags=["drink"],
        source_type="conversation",
        source_ref_digest="b" * 64,
        sensitivity="private",
        proposed_by_profile_id="daily_finance.assistant@1",
        now=NOW,
    )
    assert runtime.memories.retrieve(
        user_id=owner,
        allowed_namespaces=frozenset({"daily_finance.confirmed"}),
        now=NOW,
    ) == []
    item, replayed = runtime.memories.decide(
        candidate.id,
        user_id=owner,
        confirm=True,
        target_namespace=None,
        allowed_namespaces=frozenset({"daily_finance.confirmed"}),
        idempotency_key="confirm-memory",
        now=NOW,
    )
    assert item is not None and not replayed
    assert runtime.memories.retrieve(
        user_id=owner,
        allowed_namespaces=frozenset({"daily_finance.confirmed"}),
        tags=frozenset({"drink"}),
        profile_limit=99,
        now=NOW,
    )[0].id == item.id
    assert runtime.memories.delete(item.id, user_id=owner, idempotency_key="delete-memory", now=NOW)
    with runtime.sessions() as session:
        deleted = session.get(MemoryItemRecord, item.id)
        assert deleted.status == "deleted" and deleted.value_json == "{}" and deleted.tags_json == "[]"


def test_c11_setting_secret_rejected_before_write_and_cas_is_idempotent(host_stack) -> None:
    client, runtime, _ = host_stack
    owner_headers(client)
    owner = _owner(runtime)
    with pytest.raises(HostStateError, match="setting_secret_forbidden"):
        runtime.settings.put(
            user_id=owner,
            module_id="daily_finance",
            key="assistant_mode",
            value={"nested": {"refresh_token": "virtual-secret"}},
            schema_version=1,
            expected_version=None,
            idempotency_key="secret-setting",
            now=NOW,
        )
    with runtime.sessions() as session:
        assert session.scalars(select(ModuleSettingRecord)).all() == []
        assert session.scalars(select(HostRequestReceiptRecord).where(HostRequestReceiptRecord.operation == "setting.put")).all() == []

    row, replayed = runtime.settings.put(
        user_id=owner,
        module_id="daily_finance",
        key="assistant_mode",
        value={"enabled": True},
        schema_version=1,
        expected_version=None,
        idempotency_key="safe-setting",
        now=NOW,
    )
    same, was_replayed = runtime.settings.put(
        user_id=owner,
        module_id="daily_finance",
        key="assistant_mode",
        value={"enabled": True},
        schema_version=1,
        expected_version=None,
        idempotency_key="safe-setting",
        now=NOW,
    )
    assert not replayed and was_replayed and same.id == row.id and row.version_id == 1
    with pytest.raises(HostStateError, match="setting_version_conflict"):
        runtime.settings.put(
            user_id=owner,
            module_id="daily_finance",
            key="assistant_mode",
            value={"enabled": False},
            schema_version=1,
            expected_version=99,
            idempotency_key="stale-setting",
            now=NOW,
        )


def test_c11_run_lease_is_owner_scoped_and_attempt_fenced(host_stack) -> None:
    client, runtime, _ = host_stack
    owner_headers(client)
    owner, other, conversation_id, run_id = _owner(runtime), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    with runtime.sessions() as session, session.begin():
        session.add(AppUser(id=other, handle="lease_other", status="active"))
        session.add(ConversationRecord(
            id=conversation_id, user_id=owner, channel="api_test", module_id="daily_finance",
            profile_id="daily_finance.assistant@1", created_at=NOW,
        ))
        session.add(AgentRunRecord(
            id=run_id, user_id=owner, actor_id=owner, conversation_id=conversation_id,
            source_system="desktop_chat", source_event_digest="c" * 64,
            request_fingerprint="d" * 64, status="running", module_id="daily_finance",
            profile_id="daily_finance.assistant@1", attempt_no=1,
            lease_expires_at=NOW + timedelta(seconds=60), created_at=NOW, updated_at=NOW,
        ))
    leases = RunLeaseCoordinator(runtime.sessions)
    with pytest.raises(WorkflowError, match="run_not_found"):
        leases.acquire(run_id, user_id=other, now=NOW + timedelta(seconds=60))
    with pytest.raises(WorkflowError, match="run_lease_active"):
        leases.acquire(run_id, user_id=owner, now=NOW + timedelta(seconds=59, microseconds=999999))
    assert leases.acquire(run_id, user_id=owner, now=NOW + timedelta(seconds=60)).attempt_no == 2
    assert leases.acquire(run_id, user_id=owner, now=NOW + timedelta(seconds=120)).attempt_no == 3
    with pytest.raises(WorkflowError, match="run_attempts_exhausted"):
        leases.acquire(run_id, user_id=owner, now=NOW + timedelta(seconds=180))


def test_c11_sessions_password_boundary_and_binding_attempt_limit(host_stack) -> None:
    client, runtime, _ = host_stack
    owner_headers(client)
    tokens = runtime.auth.login(
        handle="local_owner",
        password="virtual passphrase 123",
        client_fingerprint="independent-auth-boundary",
        device_name="C11 independent",
        platform="api_test",
        now=NOW,
    )
    principal = runtime.auth.authenticate_access(tokens.access_token, now=NOW)
    code = runtime.auth.create_binding_code(principal, channel="virtual_channel", now=NOW)
    for index in range(5):
        with pytest.raises(AuthError, match="binding_code_invalid"):
            runtime.auth.consume_binding_code(
                adapter_token=b"A" * 32,
                code_id=code.code_id,
                channel="virtual_channel",
                provider_account="virtual-provider",
                external_subject=f"virtual-subject-{index}",
                code="ZZZZ-ZZZZ",
                now=NOW + timedelta(seconds=index),
            )
    with runtime.sessions() as session:
        assert session.get(ChannelBindingCode, code.code_id).status == "locked"

    with pytest.raises(AuthError, match="session_expired"):
        runtime.auth.change_password(
            tokens.access_token,
            old_password="virtual passphrase 123",
            new_password="virtual replacement 456",
            now=tokens.access_expires_at,
        )
    replacement = runtime.auth.change_password(
        tokens.access_token,
        old_password="virtual passphrase 123",
        new_password="virtual replacement 456",
        now=tokens.access_expires_at - timedelta(microseconds=1),
    )
    with pytest.raises(AuthError, match="session_revoked"):
        runtime.auth.authenticate_access(tokens.access_token, now=NOW)
    runtime.auth.logout(replacement.access_token, now=NOW)
    with pytest.raises(AuthError, match="session_revoked"):
        runtime.auth.authenticate_access(replacement.access_token, now=NOW)


def test_c11_memory_expiry_limit_and_version_cas(host_stack) -> None:
    client, runtime, _ = host_stack
    owner_headers(client)
    owner = _owner(runtime)
    candidate = runtime.memories.propose(
        user_id=owner,
        source_namespace="daily_finance.candidates",
        target_namespace="daily_finance.confirmed",
        kind="goal",
        value={"description": "virtual weekly goal"},
        tags=[],
        source_type="conversation",
        source_ref_digest="e" * 64,
        sensitivity="private",
        proposed_by_profile_id="daily_finance.assistant@1",
        now=NOW,
    )
    expired = next(row for row in runtime.memories.candidates(user_id=owner, now=NOW + timedelta(days=30)) if row.id == candidate.id)
    assert expired.status == "expired" and expired.value_json == "{}"

    with runtime.sessions() as session, session.begin():
        for index in range(10):
            session.add(MemoryItemRecord(
                user_id=owner,
                namespace="daily_finance.confirmed",
                kind="goal",
                value_json=json.dumps({"index": index}),
                tags_json='["bounded"]',
                source_type="test",
                source_ref_digest=f"{index:064d}",
                sensitivity="private",
                confirmed_at=NOW + timedelta(seconds=index),
                audit_id=uuid.uuid4(),
            ))
    items = runtime.memories.retrieve(
        user_id=owner,
        allowed_namespaces=frozenset({"daily_finance.confirmed"}),
        tags=frozenset({"bounded"}),
        profile_limit=99,
        now=NOW + timedelta(minutes=1),
    )
    assert len(items) == 8
    target = items[0]
    replacement, replayed = runtime.memories.supersede(
        target.id,
        user_id=owner,
        value={"index": "replacement"},
        expected_version=1,
        idempotency_key="memory-supersede",
        now=NOW + timedelta(minutes=2),
    )
    assert not replayed and replacement.status == "active"
    with pytest.raises(HostStateError, match="memory_version_conflict"):
        runtime.memories.invalidate(
            target.id,
            user_id=owner,
            expected_version=1,
            idempotency_key="memory-stale-invalidate",
            now=NOW + timedelta(minutes=2),
        )


def test_c11_events_publish_after_commit_and_handler_failure_is_isolated(host_stack, caplog) -> None:
    client, runtime, _ = host_stack
    owner_headers(client)
    owner = _owner(runtime)
    seen = []
    runtime.events.subscribe("module.setting_changed@1", seen.append)
    runtime.events.subscribe(
        "module.setting_changed@1",
        lambda _event: (_ for _ in ()).throw(RuntimeError("virtual private handler detail")),
    )
    row, replayed = runtime.settings.put(
        user_id=owner,
        module_id="daily_finance",
        key="assistant_mode",
        value={"enabled": True},
        schema_version=1,
        expected_version=None,
        idempotency_key="event-setting",
        now=NOW,
    )
    assert not replayed and len(seen) == 1
    with runtime.sessions() as session:
        assert session.get(ModuleSettingRecord, row.id) is not None
    assert "host_event_handler_failed" in caplog.text
    assert "virtual private handler detail" not in caplog.text
