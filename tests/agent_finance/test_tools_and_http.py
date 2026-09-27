from __future__ import annotations

import json
import logging
import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from wife_system.agent.application import AgentApplicationError
from wife_system.agent.context import RunContext
from wife_system.agent.models import AgentRunRecord
from wife_system.agent.providers import ScriptedModelProvider
from wife_system.agent.types import AssistantTurn, ToolCall
from wife_system.api.agent_routes import AgentIdentity
from wife_system.api.app import create_app
from wife_system.tools import ToolArgumentsError

from .conftest import ACTOR_ID, CONVERSATION_ID, RECEIVED_AT, AgentHarness
from .test_vertical_slice import expense_turn


def context(*, source_system: str = "desktop_chat", source_event_id: str | None = "event") -> RunContext:
    return RunContext(
        agent_run_id=uuid.uuid4(),
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        source_system=source_system,
        source_event_id=source_event_id,
        received_at=RECEIVED_AT,
        permissions=frozenset({"finance:read", "finance:write"}),
    )


def test_five_read_tools_are_bounded_and_use_deterministic_finance_values(harness: AgentHarness) -> None:
    registry = __import__("wife_system.agent.finance_tools", fromlist=["finance_registry"]).finance_registry(harness.adapter)
    ctx = context()
    accounts = registry.invoke("finance_list_accounts", {}, ctx)
    categories = registry.invoke("finance_list_categories", {"kind": "expense"}, ctx)
    balance = registry.invoke(
        "finance_get_account_balance", {"account_id": str(harness.account_id)}, ctx
    )
    transactions = registry.invoke("finance_list_transactions", {"limit": 1}, ctx)
    snapshot = registry.invoke(
        "finance_get_monthly_snapshot", {"period": "2026-09"}, ctx
    )

    assert accounts["items"][0]["id"] == str(harness.account_id)
    assert categories["items"][0]["id"] == str(harness.category_id)
    assert balance["balance_minor"] == 100_000
    assert transactions["truncated"] is False
    assert snapshot["snapshot"]["currency"] == "CNY"


def test_model_schemas_exclude_trusted_context_and_reject_confirmation_override(
    harness: AgentHarness,
) -> None:
    registry = __import__("wife_system.agent.finance_tools", fromlist=["finance_registry"]).finance_registry(harness.adapter)
    ctx = context()
    encoded = json.dumps(registry.schemas(ctx), sort_keys=True)
    for forbidden in (
        "agent_run_id",
        "actor_id",
        "conversation_id",
        "source_system",
        "source_event_id",
        "received_at",
        "permissions",
        "approval_grant_id",
        "pending_action_id",
    ):
        assert forbidden not in encoded
    with pytest.raises(ToolArgumentsError):
        registry.invoke(
            "finance_record_expense",
            {
                "amount": "18.00",
                "account_id": str(harness.account_id),
                "category_id": str(harness.category_id),
                "confirmed": True,
            },
            ctx,
        )


def test_wechat_without_stable_event_can_only_create_candidate(harness: AgentHarness) -> None:
    ctx = context(source_system="wechat_openclaw", source_event_id=None)
    with harness.sessions() as session, session.begin():
        session.add(
            AgentRunRecord(
                id=ctx.agent_run_id,
                user_id=ctx.user_id,
                actor_id=ctx.actor_id,
                conversation_id=ctx.conversation_id,
                source_system="wechat_openclaw",
                source_event_digest="0" * 64,
                request_fingerprint="1" * 64,
                status="running",
                created_at=RECEIVED_AT,
                updated_at=RECEIVED_AT,
            )
        )
    output = harness.adapter.record_expense(
        __import__("wife_system.agent.finance_tools", fromlist=["RecordExpenseToolInput"]).RecordExpenseToolInput(
            amount="18.00", account_id=harness.account_id, category_id=harness.category_id
        ),
        ctx,
    )
    assert output["status"] == "needs_confirmation"
    assert not [row for row in harness.finance.list_transactions() if row.kind == "expense"]


def test_expired_candidate_and_wrong_identity_do_not_commit(harness: AgentHarness) -> None:
    provider = ScriptedModelProvider([expense_turn(harness)])
    application = harness.application(provider)
    candidate = application.start(
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        client_event_id=uuid.uuid4(),
        message="午饭 18 元",
        permissions=frozenset({"finance:write"}),
        received_at=RECEIVED_AT - timedelta(hours=25),
    )
    with pytest.raises(AgentApplicationError) as expired:
        application.resume(
            candidate.run_id,
            actor_id=ACTOR_ID,
            conversation_id=CONVERSATION_ID,
            action="confirm",
            permissions=frozenset({"finance:write"}),
            confirmation_code=candidate.result["confirmation_code"],
            now=RECEIVED_AT,
        )
    assert expired.value.code == "pending_action_expired"

    with pytest.raises(AgentApplicationError) as hidden:
        application.get(
            candidate.run_id,
            actor_id=uuid.uuid4(),
            conversation_id=CONVERSATION_ID,
        )
    assert hidden.value.code == "pending_action_not_found"


def test_http_run_resume_status_and_strict_schema(harness: AgentHarness) -> None:
    application = harness.application(ScriptedModelProvider([expense_turn(harness)]))
    app = create_app(
        agent_application=application,
        agent_identity=AgentIdentity(
            actor_id=ACTOR_ID,
            permissions=frozenset({"finance:read", "finance:write"}),
        ),
    )
    client = TestClient(app, raise_server_exceptions=False)
    event_id = uuid.uuid4()
    created = client.post(
        "/api/v1/agent/runs",
        json={
            "client_event_id": str(event_id),
            "conversation_id": str(CONVERSATION_ID),
            "message": "午饭 18 元",
        },
    )
    assert created.status_code == 200
    body = created.json()
    assert body["status"] == "paused"
    assert "message" not in json.dumps(body)

    status = client.get(
        f"/api/v1/agent/runs/{body['run_id']}",
        params={"conversation_id": str(CONVERSATION_ID)},
    )
    assert status.status_code == 200
    code = body["result"]["confirmation_code"]
    committed = client.post(
        f"/api/v1/agent/runs/{body['run_id']}/resume",
        json={
            "conversation_id": str(CONVERSATION_ID),
            "action": "confirm",
            "confirmation_code": code,
        },
    )
    assert committed.status_code == 200
    assert committed.json()["result"]["status"] == "committed"

    invalid = client.post(
        "/api/v1/agent/runs",
        json={
            "client_event_id": str(uuid.uuid4()),
            "conversation_id": str(CONVERSATION_ID),
            "message": "x",
            "unexpected": True,
        },
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "invalid_request"


def test_persistent_rows_store_digests_not_private_input(harness: AgentHarness) -> None:
    private_message = "PRIVATE-CANARY 午饭 18 元"
    private_event = uuid.uuid4()
    application = harness.application(ScriptedModelProvider([expense_turn(harness)]))
    application.start(
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        client_event_id=private_event,
        message=private_message,
        permissions=frozenset({"finance:write"}),
        received_at=RECEIVED_AT,
    )
    with harness.sessions() as session:
        row = session.scalar(select(AgentRunRecord))
        assert row is not None
        encoded = " ".join(str(value) for value in row.__dict__.values())
    assert private_message not in encoded
    assert str(private_event) not in encoded


def test_execution_logs_are_structured_and_do_not_include_private_input(
    harness: AgentHarness, caplog: pytest.LogCaptureFixture
) -> None:
    private_message = "PRIVATE-LOG-CANARY 午饭 18 元"
    private_event = uuid.uuid4()
    application = harness.application(ScriptedModelProvider([expense_turn(harness)]))
    with caplog.at_level(logging.INFO, logger="wife_system.agent"):
        application.start(
            actor_id=ACTOR_ID,
            conversation_id=CONVERSATION_ID,
            client_event_id=private_event,
            message=private_message,
            permissions=frozenset({"finance:write"}),
            received_at=RECEIVED_AT,
        )
    payloads = [json.loads(record.message) for record in caplog.records]
    assert payloads and all(payload["event"] == "agent_execution" for payload in payloads)
    encoded = "\n".join(record.message for record in caplog.records)
    assert private_message not in encoded
    assert str(private_event) not in encoded
