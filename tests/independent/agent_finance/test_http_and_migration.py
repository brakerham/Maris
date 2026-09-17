from __future__ import annotations

import logging
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text

from wife_system.agent.providers import ScriptedModelProvider
from wife_system.agent.types import AssistantTurn, ToolCall
from wife_system.api.agent_routes import AgentIdentity
from wife_system.api.app import create_app

from conftest import ACTOR, CONVERSATION, IndependentHarness
from test_tools_and_lifecycle import expense_count, expense_turn


def client_for(ih: IndependentHarness, turns, *, actor_id=ACTOR, permissions=None) -> TestClient:
    identity = AgentIdentity(
        actor_id=actor_id,
        permissions=frozenset({"finance:read", "finance:write"}) if permissions is None else permissions,
    )
    return TestClient(create_app(agent_application=ih.app(ScriptedModelProvider(list(turns))), agent_identity=identity))


def test_http_run_resume_status_and_replay(ih: IndependentHarness) -> None:
    """HTTP-01, HTTP-04, HTTP-06, IDM-01, IDM-05."""
    client = client_for(ih, [expense_turn(ih)])
    event = str(uuid.uuid4())
    payload = {"client_event_id": event, "conversation_id": str(CONVERSATION), "message": "虚拟午饭 18 元"}
    first = client.post("/api/v1/agent/runs", json=payload)
    assert first.status_code == 200
    body = first.json()
    assert body["status"] == "paused" and body["pause_reason"] == "needs_confirmation"
    assert expense_count(ih) == 0
    replay = client.post("/api/v1/agent/runs", json=payload)
    assert replay.status_code == 200 and replay.json()["run_id"] == body["run_id"]
    assert replay.json()["replayed"] is True

    resume_payload = {
        "conversation_id": str(CONVERSATION), "action": "confirm",
        "confirmation_code": body["result"]["confirmation_code"],
    }
    committed = client.post(f"/api/v1/agent/runs/{body['run_id']}/resume", json=resume_payload)
    repeated = client.post(f"/api/v1/agent/runs/{body['run_id']}/resume", json=resume_payload)
    assert committed.status_code == repeated.status_code == 200
    assert repeated.json()["result"]["result_id"] == committed.json()["result"]["result_id"]
    assert expense_count(ih) == 1
    status = client.get(f"/api/v1/agent/runs/{body['run_id']}", params={"conversation_id": str(CONVERSATION)})
    assert status.status_code == 200 and status.json()["status"] == "success"
    for hidden in ("message", "prompt", "events", "source_event", "approval_grant"):
        assert hidden not in status.text.lower()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"client_event_id": "bad", "conversation_id": str(CONVERSATION), "message": "x"},
        {"client_event_id": str(uuid.uuid4()), "conversation_id": str(CONVERSATION), "message": "   "},
        {"client_event_id": str(uuid.uuid4()), "conversation_id": str(CONVERSATION), "message": "x", "actor_id": str(uuid.uuid4())},
        {"client_event_id": str(uuid.uuid4()), "conversation_id": str(CONVERSATION), "message": "x", "api_key": "PRIVATE"},
    ],
)
def test_http_strict_run_validation_never_starts_agent(ih: IndependentHarness, payload: dict) -> None:
    """CTX-03, HTTP-02."""
    client = client_for(ih, [AssistantTurn(content="must not run")])
    response = client.post("/api/v1/agent/runs", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
    assert "PRIVATE" not in response.text


def test_http_missing_input_cancel_and_later_confirm_is_safe(ih: IndependentHarness) -> None:
    """HTTP-03, HTTP-05, ACT-11, ACT-12."""
    turn = expense_turn(ih, amount=None, account_id=None, category_id=None)
    client = client_for(ih, [turn])
    created = client.post(
        "/api/v1/agent/runs",
        json={"client_event_id": str(uuid.uuid4()), "conversation_id": str(CONVERSATION), "message": "虚拟午饭"},
    ).json()
    supplied = client.post(
        f"/api/v1/agent/runs/{created['run_id']}/resume",
        json={
            "conversation_id": str(CONVERSATION), "action": "provide_input",
            "values": {"amount": "18.00", "account_id": str(ih.account_id), "category_id": str(ih.category_id)},
        },
    )
    assert supplied.status_code == 200 and supplied.json()["pause_reason"] == "needs_confirmation"
    code = supplied.json()["result"]["confirmation_code"]
    cancelled = client.post(
        f"/api/v1/agent/runs/{created['run_id']}/resume",
        json={"conversation_id": str(CONVERSATION), "action": "cancel"},
    )
    assert cancelled.status_code == 200 and cancelled.json()["result"]["status"] == "cancelled"
    rejected = client.post(
        f"/api/v1/agent/runs/{created['run_id']}/resume",
        json={"conversation_id": str(CONVERSATION), "action": "confirm", "confirmation_code": code},
    )
    assert rejected.status_code in {404, 409} and expense_count(ih) == 0


def test_http_identity_not_found_and_agent_unavailable_share_safe_envelope(ih: IndependentHarness) -> None:
    """ACT-16, HTTP-07, HTTP-08, PRV-05."""
    owner = client_for(ih, [expense_turn(ih)])
    created = owner.post(
        "/api/v1/agent/runs",
        json={"client_event_id": str(uuid.uuid4()), "conversation_id": str(CONVERSATION), "message": "虚拟午饭 18 元"},
    ).json()
    intruder = client_for(ih, [], actor_id=uuid.uuid4())
    hidden = intruder.get(
        f"/api/v1/agent/runs/{created['run_id']}", params={"conversation_id": str(CONVERSATION)}
    )
    missing = owner.get(
        f"/api/v1/agent/runs/{uuid.uuid4()}", params={"conversation_id": str(CONVERSATION)}
    )
    assert hidden.status_code == missing.status_code == 404
    assert hidden.json()["error"]["code"] == missing.json()["error"]["code"] == "pending_action_not_found"
    unavailable = TestClient(create_app()).post(
        "/api/v1/agent/runs",
        json={"client_event_id": str(uuid.uuid4()), "conversation_id": str(CONVERSATION), "message": "x"},
    )
    assert unavailable.status_code == 503 and unavailable.json()["error"]["code"] == "agent_unavailable"


def test_http_error_logs_do_not_echo_payload_canary(ih: IndependentHarness, caplog) -> None:
    """PRV-01, PRV-02, PRV-04, PRV-05."""
    caplog.set_level(logging.INFO)
    canary = "PRIVATE_HTTP_CANARY"
    response = client_for(ih, []).post(
        "/api/v1/agent/runs",
        json={"client_event_id": "bad", "conversation_id": str(CONVERSATION), "message": canary},
    )
    assert response.status_code == 422
    corpus = response.text + "\n".join(record.getMessage() for record in caplog.records)
    assert canary not in corpus


def test_p2_migration_chain_tables_constraints_and_round_trip(tmp_path: Path) -> None:
    """CTX-05, IDM-09, PRV-03; P2 persistence migration gate."""
    target = tmp_path / "p2-c6.sqlite3"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{target.as_posix()}")
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{target.as_posix()}")
    inspector = inspect(engine)
    assert engine.connect().scalar(text("SELECT version_num FROM alembic_version")) == "7f3e2d1c9a4b"
    assert {"agent_run", "pending_action"}.issubset(inspector.get_table_names())
    assert {"uq_agent_run_actor_source_event"}.issubset(
        {item["name"] for item in inspector.get_unique_constraints("agent_run")}
    )
    assert {"uq_pending_action_run_id", "uq_pending_action_confirmation_code"}.issubset(
        {item["name"] for item in inspector.get_unique_constraints("pending_action")}
    )
    engine.dispose()
    command.downgrade(config, "1377551283d0")
    engine = create_engine(f"sqlite:///{target.as_posix()}")
    assert "agent_run" not in inspect(engine).get_table_names()
    engine.dispose()
    command.upgrade(config, "head")
