from __future__ import annotations

import uuid

import pytest
from pydantic import BaseModel, ConfigDict

from wife_system.agent.application import AgentApplicationError
from wife_system.agent.context import RunContext
from wife_system.agent.loop import AgentRunner
from wife_system.agent.providers import ProviderError, ScriptedModelProvider
from wife_system.agent.types import AssistantTurn, ToolCall
from wife_system.finance import FinanceError
from wife_system.finance.schemas import ArchiveResource
from wife_system.tools import Tool, ToolRegistry

from .conftest import ACTOR_ID, CONVERSATION_ID, RECEIVED_AT, AgentHarness
from .test_vertical_slice import expense_turn, start_candidate


class EmptyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


def run_context() -> RunContext:
    return RunContext(
        agent_run_id=uuid.uuid4(),
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        source_system="desktop_chat",
        source_event_id=str(uuid.uuid4()),
        received_at=RECEIVED_AT,
        permissions=frozenset({"finance:read"}),
    )


def test_write_tool_is_hidden_without_permission_and_direct_guess_is_denied(harness: AgentHarness) -> None:
    registry = __import__("wife_system.agent.finance_tools", fromlist=["finance_registry"]).finance_registry(harness.adapter)
    ctx = run_context()
    names = {schema["function"]["name"] for schema in registry.schemas(ctx)}
    assert "finance_record_expense" not in names

    result = AgentRunner(
        provider=ScriptedModelProvider([expense_turn(harness)]),
        tools=registry,
    ).run("private", context=ctx)
    assert result.error_code == "permission_denied"


def test_second_write_and_total_tool_limits_stop_deterministically() -> None:
    registry = ToolRegistry(
        [
            Tool(
                "write_marker",
                "write marker",
                EmptyInput,
                lambda _: {"status": "ok"},
                is_write=True,
            )
        ]
    )
    result = AgentRunner(
        provider=ScriptedModelProvider(
            [
                AssistantTurn(
                    tool_calls=(
                        ToolCall(id="one", name="write_marker", arguments={}),
                        ToolCall(id="two", name="write_marker", arguments={"x": 1}),
                    )
                )
            ]
        ),
        tools=registry,
    ).run("two writes", "two-writes")
    assert result.error_code in {"invalid_tool_arguments", "write_limit_exceeded"}


def test_plan_or_question_can_finish_without_finance_write(harness: AgentHarness) -> None:
    application = harness.application(
        ScriptedModelProvider([AssistantTurn(content="这只是一个计划，不会记账。")])
    )
    result = application.start(
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        client_event_id=uuid.uuid4(),
        message="明天午饭大概 18 元合适吗",
        permissions=frozenset({"finance:read", "finance:write"}),
        received_at=RECEIVED_AT,
    )
    assert result.status == "success"
    assert not [row for row in harness.finance.list_transactions() if row.kind == "expense"]


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("午饭大约十几元", "ask_amount"),
        ("明天计划午饭 18 元", "ask_record_intent"),
    ],
)
def test_policy_overrides_model_guess_for_approximate_or_planned_expense(
    harness: AgentHarness, message: str, expected: str
) -> None:
    provider = ScriptedModelProvider([expense_turn(harness)])
    application = harness.application(provider)
    result = application.start(
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        client_event_id=uuid.uuid4(),
        message=message,
        permissions=frozenset({"finance:write"}),
        received_at=RECEIVED_AT,
    )
    assert result.pause_reason == "needs_input"
    assert result.result is not None and result.result["question_code"] == expected
    assert not [row for row in harness.finance.list_transactions() if row.kind == "expense"]


def test_relative_date_uses_trusted_received_time_not_model_guess(harness: AgentHarness) -> None:
    provider = ScriptedModelProvider(
        [
            AssistantTurn(
                tool_calls=(
                    ToolCall(
                        id="relative",
                        name="finance_record_expense",
                        arguments={
                            "amount": "18.00",
                            "account_id": str(harness.account_id),
                            "category_id": str(harness.category_id),
                            "occurred_at": "2030-01-01T00:00:00Z",
                        },
                    ),
                )
            )
        ]
    )
    result = harness.application(provider).start(
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        client_event_id=uuid.uuid4(),
        message="昨天午饭 18 元",
        permissions=frozenset({"finance:write"}),
        received_at=RECEIVED_AT,
    )
    assert result.result is not None
    assert result.result["summary"]["occurred_at"] == "2026-09-15T12:00:00+00:00"


def test_multiple_expenses_in_one_message_are_rejected_before_candidate(harness: AgentHarness) -> None:
    provider = ScriptedModelProvider([expense_turn(harness)])
    result = harness.application(provider).start(
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        client_event_id=uuid.uuid4(),
        message="午饭 18 元，打车 12 元",
        permissions=frozenset({"finance:write"}),
        received_at=RECEIVED_AT,
    )
    assert result.status == "error"
    assert result.error_code == "multiple_expenses_unsupported"
    assert harness.pending.active_for_run(result.run_id) is None


def test_resource_change_makes_candidate_stale(harness: AgentHarness) -> None:
    application, _, candidate = start_candidate(harness)
    harness.finance.archive_category(
        ArchiveResource(
            source_system="test",
            source_event_id="archive-category",
            resource_id=harness.category_id,
            expected_version=1,
            reason="virtual stale test",
        )
    )
    with pytest.raises(AgentApplicationError) as captured:
        application.resume(
            candidate.run_id,
            actor_id=ACTOR_ID,
            conversation_id=CONVERSATION_ID,
            action="confirm",
            permissions=frozenset({"finance:write"}),
            confirmation_code=candidate.result["confirmation_code"],
            now=RECEIVED_AT,
        )
    assert captured.value.code == "pending_action_stale"


def test_database_failure_never_returns_false_success_and_can_recover(
    harness: AgentHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    application, _, candidate = start_candidate(harness)
    original = harness.finance.record_expense

    def unavailable(command):
        raise FinanceError("database_unavailable")

    monkeypatch.setattr(harness.finance, "record_expense", unavailable)
    failed = application.resume(
        candidate.run_id,
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        action="confirm",
        permissions=frozenset({"finance:write"}),
        confirmation_code=candidate.result["confirmation_code"],
        now=RECEIVED_AT,
    )
    assert failed.status == "paused"
    assert failed.error_code == "database_unavailable"
    assert not [row for row in harness.finance.list_transactions() if row.kind == "expense"]

    monkeypatch.setattr(harness.finance, "record_expense", original)
    recovered = application.resume(
        candidate.run_id,
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        action="confirm",
        permissions=frozenset({"finance:write"}),
        confirmation_code=candidate.result["confirmation_code"],
        now=RECEIVED_AT,
    )
    assert recovered.result is not None and recovered.result["status"] == "committed"


def test_retryable_model_failure_gets_one_bounded_retry(harness: AgentHarness) -> None:
    class FailOnce:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, messages, tools, timeout_seconds):
            self.calls += 1
            if self.calls == 1:
                raise ProviderError("private transient", retryable=True)
            return expense_turn(harness)

    provider = FailOnce()
    application = harness.application(provider)
    result = application.start(
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        client_event_id=uuid.uuid4(),
        message="午饭 18 元",
        permissions=frozenset({"finance:write"}),
        received_at=RECEIVED_AT,
    )
    assert provider.calls == 2
    assert result.pause_reason == "needs_confirmation"
