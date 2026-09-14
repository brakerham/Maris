from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from wife_system.agent.loop import AgentRunner
from wife_system.agent.providers import ProviderError, ScriptedModelProvider
from wife_system.agent.types import AssistantTurn, RunStatus, ToolCall
from wife_system.tools import Tool, ToolRegistry, phase_zero_registry


def tool_turn(
    *, name: str = "query_budget", arguments: dict[str, Any] | None = None, call_id: str = "call-1"
) -> AssistantTurn:
    return AssistantTurn(
        tool_calls=(ToolCall(id=call_id, name=name, arguments=arguments or {}),)
    )


def test_runs_real_tool_loop_before_returning_model_text() -> None:
    provider = ScriptedModelProvider([tool_turn(), AssistantTurn(content="budget explained")])
    runner = AgentRunner(provider=provider, tools=phase_zero_registry())

    result = runner.run("show budget", "req-1")

    assert result.status is RunStatus.SUCCESS
    assert result.answer == "budget explained"
    assert provider.calls == 2
    assert [event.kind for event in result.events].count("tool_finished") == 1


@pytest.mark.parametrize(
    ("turn", "expected_code"),
    [
        (tool_turn(name="missing_tool"), "unknown_tool"),
        (tool_turn(arguments={"period": "last_year"}), "invalid_tool_arguments"),
    ],
)
def test_rejects_unknown_tool_and_invalid_arguments(
    turn: AssistantTurn, expected_code: str
) -> None:
    runner = AgentRunner(provider=ScriptedModelProvider([turn]), tools=phase_zero_registry())

    result = runner.run("test", f"req-{expected_code}")

    assert result.status is RunStatus.ERROR
    assert result.error_code == expected_code


def test_stops_identical_repeated_tool_call() -> None:
    provider = ScriptedModelProvider([tool_turn(call_id="one"), tool_turn(call_id="two")])
    runner = AgentRunner(provider=provider, tools=phase_zero_registry())

    result = runner.run("repeat", "req-repeat")

    assert result.error_code == "duplicate_tool_call"
    assert provider.calls == 2


def test_stops_at_configured_model_turn_limit() -> None:
    provider = ScriptedModelProvider([tool_turn()])
    runner = AgentRunner(provider=provider, tools=phase_zero_registry(), max_model_turns=1)

    result = runner.run("loop", "req-limit")

    assert result.error_code == "max_model_turns_exceeded"
    assert provider.calls == 1


class FailingProvider:
    def complete(self, messages: Any, tools: Any, timeout_seconds: float) -> AssistantTurn:
        raise ProviderError("private upstream detail")


class TimeoutProvider:
    def complete(self, messages: Any, tools: Any, timeout_seconds: float) -> AssistantTurn:
        raise TimeoutError("socket detail")


@pytest.mark.parametrize(
    ("provider", "expected_code"),
    [(FailingProvider(), "model_unavailable"), (TimeoutProvider(), "model_timeout")],
)
def test_sanitizes_provider_failures(provider: Any, expected_code: str) -> None:
    runner = AgentRunner(provider=provider, tools=phase_zero_registry())

    result = runner.run("failure", f"req-{expected_code}")

    assert result.error_code == expected_code
    assert "private" not in (result.error_message or "")
    assert "socket" not in (result.error_message or "")


class EmptyArguments(BaseModel):
    pass


def test_sanitizes_tool_exception() -> None:
    def fail(arguments: EmptyArguments) -> None:
        raise RuntimeError("private tool detail")

    registry = ToolRegistry(
        [Tool(name="fail", description="fail", arguments_model=EmptyArguments, handler=fail)]
    )
    runner = AgentRunner(
        provider=ScriptedModelProvider([tool_turn(name="fail")]), tools=registry
    )

    result = runner.run("failure", "req-tool-error")

    assert result.error_code == "tool_error"
    assert "private" not in (result.error_message or "")


def test_same_request_id_returns_cached_result_without_provider_call() -> None:
    provider = ScriptedModelProvider([AssistantTurn(content="once")])
    runner = AgentRunner(provider=provider, tools=phase_zero_registry())

    first = runner.run("same", "stable-id")
    second = runner.run("same", "stable-id")

    assert first.answer == second.answer == "once"
    assert provider.calls == 1
    assert second.events[-1].kind == "cache_hit"


def test_request_id_reuse_with_different_input_is_a_conflict() -> None:
    provider = ScriptedModelProvider([AssistantTurn(content="once")])
    runner = AgentRunner(provider=provider, tools=phase_zero_registry())
    runner.run("first", "stable-id")

    result = runner.run("different", "stable-id")

    assert result.error_code == "duplicate_request_conflict"
    assert provider.calls == 1


def test_empty_model_response_is_an_explicit_error() -> None:
    runner = AgentRunner(
        provider=ScriptedModelProvider([AssistantTurn()]), tools=phase_zero_registry()
    )

    result = runner.run("empty", "req-empty")

    assert result.error_code == "empty_model_response"


def test_offline_provider_uses_actual_tool_result() -> None:
    from wife_system.agent.providers import DeterministicBudgetProvider

    calls = 0

    def changed_budget(arguments: EmptyArguments) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {
            "data_source": "virtual_phase_0",
            "currency": "CNY",
            "total_budget_cents": 90_000,
            "spent_cents": 20_000,
            "reserved_cents": 10_000,
            "available_cents": 60_000,
        }

    registry = ToolRegistry(
        [
            Tool(
                name="query_budget",
                description="changed virtual budget",
                arguments_model=EmptyArguments,
                handler=changed_budget,
            )
        ]
    )
    runner = AgentRunner(provider=DeterministicBudgetProvider(), tools=registry)

    result = runner.run("budget", "req-changed-budget")

    assert result.status is RunStatus.SUCCESS
    assert calls == 1
    assert "600.00" in (result.answer or "")
