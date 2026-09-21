from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from wife_system.agent.models import AgentRunRecord
from wife_system.finance.db import Base, make_engine, make_session_factory
from wife_system.host.auth.models import AppUser
from wife_system.host.state_models import ConversationRecord
from wife_system.host.workflows import ActionHandlerRegistry, RunLeaseCoordinator, WorkflowError


NOW = datetime(2026, 9, 21, 0, 0, tzinfo=UTC)


def test_run_lease_is_user_scoped_sixty_seconds_and_three_attempts(tmp_path) -> None:
    engine = make_engine(f"sqlite:///{(tmp_path / 'lease.sqlite3').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = make_session_factory(engine)
    user_id, other_id, conversation_id, run_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    with sessions() as session, session.begin():
        session.add_all(
            [
                AppUser(id=user_id, handle="lease_owner", status="active"),
                AppUser(id=other_id, handle="other_owner", status="active"),
                ConversationRecord(
                    id=conversation_id,
                    user_id=user_id,
                    channel="api_test",
                    module_id="daily_finance",
                    profile_id="daily_finance.assistant@1",
                    created_at=NOW,
                ),
                AgentRunRecord(
                    id=run_id,
                    user_id=user_id,
                    actor_id=user_id,
                    conversation_id=conversation_id,
                    source_system="desktop_chat",
                    source_event_digest="a" * 64,
                    request_fingerprint="b" * 64,
                    status="running",
                    module_id="daily_finance",
                    profile_id="daily_finance.assistant@1",
                    attempt_no=1,
                    lease_expires_at=NOW + timedelta(seconds=60),
                    created_at=NOW,
                    updated_at=NOW,
                ),
            ]
        )
    coordinator = RunLeaseCoordinator(sessions)
    with pytest.raises(WorkflowError, match="run_not_found"):
        coordinator.acquire(run_id, user_id=other_id, now=NOW + timedelta(seconds=60))
    with pytest.raises(WorkflowError, match="run_lease_active"):
        coordinator.acquire(run_id, user_id=user_id, now=NOW + timedelta(seconds=59, microseconds=999999))
    acquired = coordinator.acquire(run_id, user_id=user_id, now=NOW + timedelta(seconds=60))
    assert acquired.attempt_no == 2
    acquired.lease_expires_at = NOW + timedelta(seconds=120)
    second = coordinator.acquire(run_id, user_id=user_id, now=NOW + timedelta(seconds=120))
    assert second.attempt_no == 3
    with pytest.raises(WorkflowError, match="run_attempts_exhausted"):
        coordinator.acquire(run_id, user_id=user_id, now=NOW + timedelta(seconds=180))
    engine.dispose()


def test_action_handler_registry_rejects_duplicate_and_unknown_schema() -> None:
    class Handler:
        action_type = "daily_finance.record_expense"
        action_schema_version = 1

    registry = ActionHandlerRegistry()
    registry.register(Handler())
    assert registry.resolve("daily_finance.record_expense", 1).action_type == Handler.action_type
    with pytest.raises(WorkflowError, match="duplicate_action_handler"):
        registry.register(Handler())
    with pytest.raises(WorkflowError, match="action_handler_not_found"):
        registry.resolve("daily_finance.record_expense", 2)
