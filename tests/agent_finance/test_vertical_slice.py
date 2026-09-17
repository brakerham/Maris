from __future__ import annotations

import uuid
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import select

from wife_system.agent.application import AgentApplicationError
from wife_system.agent.providers import ScriptedModelProvider
from wife_system.agent.types import AssistantTurn, ToolCall
from wife_system.finance.models import CommandReceipt

from .conftest import ACTOR_ID, CONVERSATION_ID, RECEIVED_AT, AgentHarness


def expense_turn(harness: AgentHarness, *, amount: str = "18.00") -> AssistantTurn:
    return AssistantTurn(
        tool_calls=(
            ToolCall(
                id="expense-call",
                name="finance_record_expense",
                arguments={
                    "amount": amount,
                    "account_id": str(harness.account_id),
                    "category_id": str(harness.category_id),
                },
            ),
        )
    )


def start_candidate(harness: AgentHarness, event_id: uuid.UUID | None = None):
    provider = ScriptedModelProvider([expense_turn(harness)])
    application = harness.application(provider)
    result = application.start(
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        client_event_id=event_id or uuid.uuid4(),
        message="午饭 18 元",
        permissions=frozenset({"finance:read", "finance:write"}),
        received_at=RECEIVED_AT,
    )
    return application, provider, result


def test_complete_candidate_confirm_and_duplicate_confirmation(harness: AgentHarness) -> None:
    application, provider, candidate = start_candidate(harness)

    assert candidate.status == "paused"
    assert candidate.pause_reason == "needs_confirmation"
    assert candidate.result is not None
    assert candidate.result["summary"]["amount"] == "18.00"
    code = candidate.result["confirmation_code"]

    committed = application.resume(
        candidate.run_id,
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        action="confirm",
        permissions=frozenset({"finance:write"}),
        confirmation_code=code,
        now=RECEIVED_AT,
    )
    replay = application.resume(
        candidate.run_id,
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        action="confirm",
        permissions=frozenset({"finance:write"}),
        confirmation_code=code,
        now=RECEIVED_AT,
    )

    assert provider.calls == 1
    assert committed.result is not None and committed.result["replayed"] is False
    assert replay.result is not None and replay.result["replayed"] is True
    assert replay.result["result_id"] == committed.result["result_id"]
    expenses = [row for row in harness.finance.list_transactions() if row.kind == "expense"]
    assert len(expenses) == 1
    with harness.sessions() as session:
        receipt = session.scalar(
            select(CommandReceipt).where(CommandReceipt.result_id == expenses[0].id)
        )
        assert receipt is not None and receipt.source_system == "desktop_chat"


def test_same_desktop_event_replays_and_conflicting_payload_is_rejected(harness: AgentHarness) -> None:
    event_id = uuid.uuid4()
    application, provider, first = start_candidate(harness, event_id)
    second = application.start(
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        client_event_id=event_id,
        message="午饭 18 元",
        permissions=frozenset({"finance:read", "finance:write"}),
        received_at=RECEIVED_AT,
    )
    assert second.run_id == first.run_id
    assert second.replayed is True
    assert provider.calls == 1

    with pytest.raises(AgentApplicationError) as captured:
        application.start(
            actor_id=ACTOR_ID,
            conversation_id=CONVERSATION_ID,
            client_event_id=event_id,
            message="午饭 19 元",
            permissions=frozenset({"finance:read", "finance:write"}),
            received_at=RECEIVED_AT,
        )
    assert captured.value.code == "duplicate_request_conflict"


def test_missing_fields_resume_to_confirmation(harness: AgentHarness) -> None:
    provider = ScriptedModelProvider(
        [
            AssistantTurn(
                tool_calls=(
                    ToolCall(
                        id="missing-call",
                        name="finance_record_expense",
                        arguments={"amount": "18.00"},
                    ),
                )
            )
        ]
    )
    application = harness.application(provider)
    first = application.start(
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        client_event_id=uuid.uuid4(),
        message="午饭 18 元",
        permissions=frozenset({"finance:write"}),
        received_at=RECEIVED_AT,
    )
    assert first.pause_reason == "needs_input"
    assert first.result is not None
    assert first.result["question_code"] == "ask_account_id"

    updated = application.resume(
        first.run_id,
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        action="provide_input",
        permissions=frozenset({"finance:write"}),
        values={
            "account_id": str(harness.account_id),
            "category_id": str(harness.category_id),
        },
        now=RECEIVED_AT,
    )
    assert updated.pause_reason == "needs_confirmation"
    assert updated.result is not None and updated.result["missing_fields"] == []
    assert harness.finance.list_transactions()[-1].kind == "opening_balance"


def test_concurrent_confirmation_and_restart_recovery(harness: AgentHarness) -> None:
    application, _, candidate = start_candidate(harness)
    assert candidate.result is not None
    code = candidate.result["confirmation_code"]

    restarted = harness.application(ScriptedModelProvider([]))
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(
                restarted.resume,
                candidate.run_id,
                actor_id=ACTOR_ID,
                conversation_id=CONVERSATION_ID,
                action="confirm",
                permissions=frozenset({"finance:write"}),
                confirmation_code=code,
                now=RECEIVED_AT,
            )
            for _ in range(2)
        ]
        results = [future.result(timeout=5) for future in futures]

    ids = {result.result["result_id"] for result in results if result.result}
    assert len(ids) == 1
    assert sorted(result.result["replayed"] for result in results if result.result) == [False, True]
    assert len([row for row in harness.finance.list_transactions() if row.kind == "expense"]) == 1


def test_concurrent_same_source_event_runs_model_once(harness: AgentHarness) -> None:
    entered = threading.Event()
    release = threading.Event()

    class BlockingProvider:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, messages, tools, timeout_seconds):
            self.calls += 1
            entered.set()
            assert release.wait(timeout=5)
            return expense_turn(harness)

    provider = BlockingProvider()
    application = harness.application(provider)
    event_id = uuid.uuid4()

    def submit():
        return application.start(
            actor_id=ACTOR_ID,
            conversation_id=CONVERSATION_ID,
            client_event_id=event_id,
            message="午饭 18 元",
            permissions=frozenset({"finance:write"}),
            received_at=RECEIVED_AT,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(submit)
        assert entered.wait(timeout=5)
        second = pool.submit(submit)
        release.set()
        results = [first.result(timeout=5), second.result(timeout=5)]

    assert provider.calls == 1
    assert results[0].run_id == results[1].run_id
    assert sum(result.replayed for result in results) == 1
