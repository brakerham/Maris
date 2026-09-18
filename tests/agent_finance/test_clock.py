"""Executor regressions for virtual time; no production clock or TTL changes."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from wife_system.agent.application import AgentApplicationError
from wife_system.agent.providers import ScriptedModelProvider
from wife_system.api.agent_routes import AgentIdentity
from wife_system.api.app import create_app
from wife_system.finance.models import CommandReceipt

from .conftest import ACTOR_ID, CONVERSATION_ID, RECEIVED_AT, AgentHarness, AgentTestClock
from .test_vertical_slice import expense_turn, start_candidate


@pytest.mark.parametrize(
    ("elapsed", "can_confirm"),
    [
        pytest.param(timedelta(hours=24) - timedelta(microseconds=1), True, id="before-24h"),
        pytest.param(timedelta(hours=24), False, id="exactly-24h"),
        pytest.param(timedelta(hours=24, microseconds=1), False, id="after-24h"),
    ],
)
def test_confirmation_boundary_uses_one_clock_after_restart(
    harness: AgentHarness,
    agent_clock: AgentTestClock,
    elapsed: timedelta,
    can_confirm: bool,
) -> None:
    # Each parameter gets a fresh clock, database and candidate.
    assert agent_clock.now() == RECEIVED_AT
    _, _, candidate = start_candidate(harness)
    assert candidate.result is not None
    pending = harness.pending.active_for_run(candidate.run_id)
    assert pending is not None
    assert pending.created_at == RECEIVED_AT
    assert pending.expires_at == RECEIVED_AT + timedelta(hours=24)

    agent_clock.advance(elapsed)
    restarted = harness.application(ScriptedModelProvider([]))
    status = restarted.get(
        candidate.run_id, actor_id=ACTOR_ID, conversation_id=CONVERSATION_ID
    )
    arguments = {
        "actor_id": ACTOR_ID,
        "conversation_id": CONVERSATION_ID,
        "action": "confirm",
        "permissions": frozenset({"finance:write"}),
        "confirmation_code": candidate.result["confirmation_code"],
    }
    # No explicit now: default resume and its indirect get must agree.
    if can_confirm:
        assert status.pause_reason == "needs_confirmation"
        committed = restarted.resume(candidate.run_id, **arguments)
        assert committed.result is not None
        assert committed.result["status"] == "committed"
        assert committed.result["amount_minor"] == 1800
        assert committed.result["replayed"] is False
    else:
        assert status.pause_reason == "expired"
        assert status.error_code == "pending_action_expired"
        with pytest.raises(AgentApplicationError) as captured:
            restarted.resume(candidate.run_id, **arguments)
        assert captured.value.code == "pending_action_expired"

    expected_count = 1 if can_confirm else 0
    expenses = [row for row in harness.finance.list_transactions() if row.kind == "expense"]
    assert len(expenses) == expected_count
    assert harness.finance.account_balance(harness.account_id) == 100_000 - 1800 * expected_count
    with harness.sessions() as session:
        assert session.scalar(
            select(func.count()).select_from(CommandReceipt).where(
                CommandReceipt.command_name == "record_expense"
            )
        ) == expected_count


def test_http_default_time_follows_clock_in_worker_threads(
    harness: AgentHarness, agent_clock: AgentTestClock
) -> None:
    assert agent_clock.now() == RECEIVED_AT
    application = harness.application(ScriptedModelProvider([expense_turn(harness)]))
    app = create_app(
        agent_application=application,
        agent_identity=AgentIdentity(
            actor_id=ACTOR_ID, permissions=frozenset({"finance:read", "finance:write"})
        ),
    )
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/agent/runs",
            json={
                "client_event_id": str(uuid.uuid4()),
                "conversation_id": str(CONVERSATION_ID),
                "message": "午饭 18 元",
            },
        )
        assert created.status_code == 200
        body = created.json()
        assert datetime.fromisoformat(body["created_at"]) == RECEIVED_AT
        assert datetime.fromisoformat(body["updated_at"]) == RECEIVED_AT
        assert datetime.fromisoformat(body["result"]["summary"]["occurred_at"]) == RECEIVED_AT

        agent_clock.advance(timedelta(minutes=10))
        status = client.get(
            f"/api/v1/agent/runs/{body['run_id']}",
            params={"conversation_id": str(CONVERSATION_ID)},
        )
        assert status.status_code == 200
        assert status.json()["pause_reason"] == "needs_confirmation"
        confirmed = client.post(
            f"/api/v1/agent/runs/{body['run_id']}/resume",
            json={
                "conversation_id": str(CONVERSATION_ID),
                "action": "confirm",
                "confirmation_code": body["result"]["confirmation_code"],
            },
        )
        assert confirmed.status_code == 200
        result = confirmed.json()
        assert result["result"]["status"] == "committed"
        assert result["result"]["amount_minor"] == 1800
        assert datetime.fromisoformat(result["updated_at"]) == agent_clock.now()
    assert harness.finance.account_balance(harness.account_id) == 98_200


def test_cancel_after_restart_uses_virtual_time_without_posting(
    harness: AgentHarness, agent_clock: AgentTestClock
) -> None:
    assert agent_clock.now() == RECEIVED_AT
    _, _, candidate = start_candidate(harness)
    agent_clock.advance(timedelta(hours=1))
    restarted = harness.application(ScriptedModelProvider([]))
    cancelled = restarted.resume(
        candidate.run_id,
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        action="cancel",
        permissions=frozenset({"finance:write"}),
    )
    assert cancelled.result == {"status": "cancelled"}
    assert cancelled.updated_at == agent_clock.now()
    loaded = restarted.get(
        candidate.run_id, actor_id=ACTOR_ID, conversation_id=CONVERSATION_ID
    )
    assert loaded.result == {"status": "cancelled"}
    assert not [row for row in harness.finance.list_transactions() if row.kind == "expense"]
    assert harness.finance.account_balance(harness.account_id) == 100_000
