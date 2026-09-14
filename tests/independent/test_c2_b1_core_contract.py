from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest
from pydantic import BaseModel, ConfigDict

from wife_system.agent.loop import AgentRunner
from wife_system.agent.providers import DeterministicBudgetProvider, ScriptedModelProvider
from wife_system.agent.types import AssistantTurn, ConversationMessage, RunStatus, ToolCall
from wife_system.tools import QueryBudgetArguments, Tool, ToolRegistry, phase_zero_registry


class MarkerArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    marker: str


class EmptyArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")


def tool_turn(
    *,
    call_id: str = "call-1",
    name: str = "query_budget",
    arguments: dict[str, Any] | None = None,
) -> AssistantTurn:
    return AssistantTurn(
        tool_calls=(ToolCall(id=call_id, name=name, arguments=arguments or {}),)
    )


class ToolResultAwareProvider:
    def __init__(self) -> None:
        self.calls = 0
        self.histories: list[tuple[ConversationMessage, ...]] = []

    def complete(
        self,
        messages: list[ConversationMessage],
        tools: list[dict[str, Any]],
        timeout_seconds: float,
    ) -> AssistantTurn:
        del tools, timeout_seconds
        self.calls += 1
        self.histories.append(tuple(message.model_copy(deep=True) for message in messages))
        if self.calls == 1:
            return tool_turn(call_id="budget-call", arguments={"period": "current_month"})
        tool_message = messages[-1]
        payload = json.loads(tool_message.content or "{}")
        return AssistantTurn(content=f"available={payload['available_cents']}")


def test_a01_normal_loop_uses_the_bound_tool_result() -> None:
    provider = ToolResultAwareProvider()
    runner = AgentRunner(provider=provider, tools=phase_zero_registry())

    result = runner.run("private input that must stay out of events", "c2-a01")

    assert result.status is RunStatus.SUCCESS
    assert result.answer == "available=121350"
    assert provider.calls == 2
    tool_message = provider.histories[1][-1]
    assert tool_message.role == "tool"
    assert tool_message.tool_call_id == "budget-call"
    assert json.loads(tool_message.content or "{}")["data_source"] == "virtual_phase_0"
    assert [event.kind for event in result.events].count("tool_finished") == 1


def test_a03_direct_text_finishes_without_a_tool() -> None:
    provider = ScriptedModelProvider([AssistantTurn(content="direct")])
    result = AgentRunner(provider=provider, tools=phase_zero_registry()).run(
        "hello", "c2-a03"
    )

    assert result.status is RunStatus.SUCCESS
    assert result.answer == "direct"
    assert provider.calls == 1
    assert not any(event.kind.startswith("tool_") for event in result.events)


@pytest.mark.parametrize("available_cents", [12_345, 98_765])
def test_a02_offline_answer_changes_with_actual_tool_output(available_cents: int) -> None:
    def budget(arguments: QueryBudgetArguments) -> dict[str, Any]:
        del arguments
        return {
            "data_source": "virtual_phase_0",
            "currency": "CNY",
            "total_budget_cents": 100_000,
            "spent_cents": 0,
            "reserved_cents": 0,
            "available_cents": available_cents,
        }

    registry = ToolRegistry(
        [Tool("query_budget", "budget", QueryBudgetArguments, budget)]
    )
    result = AgentRunner(
        provider=DeterministicBudgetProvider(), tools=registry
    ).run("budget", f"c2-a02-{available_cents}")

    assert result.status is RunStatus.SUCCESS
    assert f"{available_cents / 100:.2f}" in (result.answer or "")


@pytest.mark.parametrize(
    "arguments",
    [
        {"period": ["current_month"]},
        {"period": "current_month", "unexpected": "value"},
        {"period": "last_year"},
    ],
)
def test_a06_a07_a08_bad_arguments_are_rejected(arguments: dict[str, Any]) -> None:
    runner = AgentRunner(
        provider=ScriptedModelProvider([tool_turn(arguments=arguments)]),
        tools=phase_zero_registry(),
    )

    result = runner.run("bad argument", f"c2-bad-{len(json.dumps(arguments))}")

    assert result.error_code == "invalid_tool_arguments"
    assert not any(event.kind == "tool_finished" for event in result.events)


def test_a09_unknown_tool_is_not_executed() -> None:
    result = AgentRunner(
        provider=ScriptedModelProvider([tool_turn(name="does_not_exist")]),
        tools=phase_zero_registry(),
    ).run("unknown", "c2-a09")

    assert result.error_code == "unknown_tool"
    assert not any(event.kind == "tool_finished" for event in result.events)


@pytest.mark.parametrize(
    "turns",
    [
        [tool_turn(call_id="same"), tool_turn(call_id="same")],
        [
            tool_turn(call_id="first"),
            tool_turn(call_id="second"),
        ],
    ],
)
def test_a10_duplicate_tool_calls_stop_before_second_execution(
    turns: list[AssistantTurn],
) -> None:
    executions = 0

    def handler(arguments: EmptyArguments) -> dict[str, bool]:
        nonlocal executions
        executions += 1
        return {"ok": True}

    registry = ToolRegistry(
        [Tool("query_budget", "counter", EmptyArguments, handler)]
    )
    result = AgentRunner(
        provider=ScriptedModelProvider(turns), tools=registry
    ).run("duplicate", f"c2-a10-{turns[1].tool_calls[0].id}")

    assert result.error_code == "duplicate_tool_call"
    assert executions == 1


def test_a11_model_turn_limit_is_an_exact_upper_bound() -> None:
    provider = ScriptedModelProvider(
        [
            tool_turn(call_id="one", arguments={"marker": "one"}),
            tool_turn(call_id="two", arguments={"marker": "two"}),
        ]
    )
    registry = ToolRegistry(
        [Tool("query_budget", "marker", MarkerArguments, lambda args: args.model_dump())]
    )

    result = AgentRunner(
        provider=provider, tools=registry, max_model_turns=2
    ).run("loop", "c2-a11")

    assert result.error_code == "max_model_turns_exceeded"
    assert provider.calls == 2


def test_a12_empty_model_response_is_not_success() -> None:
    result = AgentRunner(
        provider=ScriptedModelProvider([AssistantTurn()]), tools=phase_zero_registry()
    ).run("empty", "c2-a12")

    assert result.status is RunStatus.ERROR
    assert result.error_code == "empty_model_response"


def test_a13_multiple_tools_run_in_order_and_keep_result_ids() -> None:
    execution_order: list[str] = []
    observed_tool_messages: list[tuple[str | None, str]] = []

    def handler(arguments: MarkerArguments) -> dict[str, str]:
        execution_order.append(arguments.marker)
        return {"marker": arguments.marker}

    class MultiToolProvider:
        calls = 0

        def complete(
            self,
            messages: list[ConversationMessage],
            tools: list[dict[str, Any]],
            timeout_seconds: float,
        ) -> AssistantTurn:
            del tools, timeout_seconds
            self.calls += 1
            if self.calls == 1:
                return AssistantTurn(
                    tool_calls=(
                        ToolCall(id="call-a", name="marker", arguments={"marker": "a"}),
                        ToolCall(id="call-b", name="marker", arguments={"marker": "b"}),
                    )
                )
            observed_tool_messages.extend(
                (message.tool_call_id, message.content or "")
                for message in messages
                if message.role == "tool"
            )
            return AssistantTurn(content="done")

    registry = ToolRegistry([Tool("marker", "marker", MarkerArguments, handler)])
    result = AgentRunner(provider=MultiToolProvider(), tools=registry).run(
        "multi", "c2-a13"
    )

    assert result.status is RunStatus.SUCCESS
    assert execution_order == ["a", "b"]
    assert [item[0] for item in observed_tool_messages] == ["call-a", "call-b"]
    assert [json.loads(item[1])["marker"] for item in observed_tool_messages] == ["a", "b"]


def test_a15_tool_exception_is_sanitized_and_runner_can_handle_another_run() -> None:
    canary = "C2_PRIVATE_TOOL_STACK"

    def fail(arguments: MarkerArguments) -> None:
        raise RuntimeError(canary)

    def succeed(arguments: MarkerArguments) -> dict[str, str]:
        return {"marker": arguments.marker}

    class RoutingProvider:
        def complete(
            self,
            messages: list[ConversationMessage],
            tools: list[dict[str, Any]],
            timeout_seconds: float,
        ) -> AssistantTurn:
            del tools, timeout_seconds
            if messages[-1].role == "tool":
                return AssistantTurn(content="recovered")
            name = "fail" if messages[0].content == "fail" else "succeed"
            return tool_turn(name=name, arguments={"marker": "x"})

    registry = ToolRegistry(
        [
            Tool("fail", "fail", MarkerArguments, fail),
            Tool("succeed", "succeed", MarkerArguments, succeed),
        ]
    )
    runner = AgentRunner(provider=RoutingProvider(), tools=registry)

    failed = runner.run("fail", "c2-a15-fail")
    recovered = runner.run("ok", "c2-a15-ok")

    assert failed.error_code == "tool_error"
    assert canary not in failed.model_dump_json()
    assert recovered.status is RunStatus.SUCCESS


def test_a14_expected_tool_exception_maps_to_the_stable_tool_error() -> None:
    def reject(arguments: EmptyArguments) -> None:
        del arguments
        raise ValueError("C2_PRIVATE_BUSINESS_DETAIL")

    registry = ToolRegistry(
        [Tool("reject", "reject", EmptyArguments, reject)]
    )
    result = AgentRunner(
        provider=ScriptedModelProvider([tool_turn(name="reject")]), tools=registry
    ).run("reject", "c2-a14")

    assert result.error_code == "tool_error"
    assert "C2_PRIVATE_BUSINESS_DETAIL" not in result.model_dump_json()


def test_a17_invalid_tool_output_is_rejected_as_a_structured_error() -> None:
    class NotJsonSerializable:
        pass

    registry = ToolRegistry(
        [
            Tool(
                "bad_output",
                "bad output",
                EmptyArguments,
                lambda arguments: NotJsonSerializable(),
            )
        ]
    )
    runner = AgentRunner(
        provider=ScriptedModelProvider([tool_turn(name="bad_output")]),
        tools=registry,
    )

    result = runner.run("bad output", "c2-a17")

    assert result.status is RunStatus.ERROR
    assert result.error_code == "tool_error"


def test_request_replay_and_conflict_are_process_local_and_stable() -> None:
    provider = ScriptedModelProvider([AssistantTurn(content="once")])
    runner = AgentRunner(provider=provider, tools=phase_zero_registry())

    first = runner.run("same", "c2-replay")
    replay = runner.run("same", "c2-replay")
    conflict = runner.run("different", "c2-replay")

    assert first.answer == replay.answer == "once"
    assert replay.events[-1].kind == "cache_hit"
    assert conflict.error_code == "duplicate_request_conflict"
    assert provider.calls == 1


def test_concurrent_same_request_is_executed_only_once() -> None:
    first_provider_entered = threading.Event()
    second_provider_entered = threading.Event()
    release_provider = threading.Event()
    second_run_started = threading.Event()
    calls_lock = threading.Lock()

    class BlockingProvider:
        def __init__(self) -> None:
            self.calls = 0

        def complete(
            self,
            messages: list[ConversationMessage],
            tools: list[dict[str, Any]],
            timeout_seconds: float,
        ) -> AssistantTurn:
            del messages, tools, timeout_seconds
            with calls_lock:
                self.calls += 1
                if self.calls == 1:
                    first_provider_entered.set()
                else:
                    second_provider_entered.set()
            if not release_provider.wait(timeout=3):
                raise TimeoutError("test provider was not released")
            return AssistantTurn(content="same result")

    provider = BlockingProvider()
    runner = AgentRunner(provider=provider, tools=phase_zero_registry())

    def run_second_request() -> Any:
        second_run_started.set()
        return runner.run("same", "c2-concurrent-request")

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(runner.run, "same", "c2-concurrent-request")
        assert first_provider_entered.wait(timeout=1)
        second = pool.submit(run_second_request)
        assert second_run_started.wait(timeout=1)
        second_provider_entered.wait(timeout=1)
        release_provider.set()
        results = [first.result(timeout=3), second.result(timeout=3)]

    assert all(result.answer == "same result" for result in results)
    assert provider.calls == 1
    assert sum(result.events[-1].kind == "cache_hit" for result in results) == 1


def test_a18_independent_runs_do_not_share_message_history() -> None:
    histories: list[tuple[str | None, ...]] = []

    class HistoryProvider:
        def complete(
            self,
            messages: list[ConversationMessage],
            tools: list[dict[str, Any]],
            timeout_seconds: float,
        ) -> AssistantTurn:
            del tools, timeout_seconds
            histories.append(tuple(message.content for message in messages))
            return AssistantTurn(content=f"answer:{messages[0].content}")

    runner = AgentRunner(provider=HistoryProvider(), tools=phase_zero_registry())
    first = runner.run("first", "c2-isolation-1")
    second = runner.run("second", "c2-isolation-2")

    assert first.answer == "answer:first"
    assert second.answer == "answer:second"
    assert histories == [("first",), ("second",)]


def test_l01_tool_events_identify_the_call_and_include_duration() -> None:
    result = AgentRunner(
        provider=ScriptedModelProvider(
            [tool_turn(call_id="observable-call"), AssistantTurn(content="done")]
        ),
        tools=phase_zero_registry(),
    ).run("observe", "c2-l01")

    tool_events = [
        event.model_dump() for event in result.events if event.kind.startswith("tool_")
    ]
    assert tool_events
    assert all(event.get("tool_call_id") == "observable-call" for event in tool_events)
    assert any(
        event.get("duration_ms") is not None or event.get("elapsed_ms") is not None
        for event in tool_events
    )


def test_l03_events_exclude_user_text_and_raw_finance_snapshot() -> None:
    private_message = "wx-user-C2-private full private message"
    result = AgentRunner(
        provider=ScriptedModelProvider(
            [tool_turn(), AssistantTurn(content="safe summary")]
        ),
        tools=phase_zero_registry(),
    ).run(private_message, "c2-l03")

    serialized_events = json.dumps(
        [event.model_dump(mode="json") for event in result.events], ensure_ascii=False
    )
    assert private_message not in serialized_events
    assert "total_budget_cents" not in serialized_events
    assert "121350" not in serialized_events


def test_l03_unknown_tool_name_cannot_echo_a_private_message() -> None:
    private_message = "wx-user-C2-private full private message"
    result = AgentRunner(
        provider=ScriptedModelProvider([tool_turn(name=private_message)]),
        tools=phase_zero_registry(),
    ).run(private_message, "c2-l03-echo")

    assert result.error_code == "unknown_tool"
    assert private_message not in result.model_dump_json()


def test_l04_invalid_arguments_do_not_leak_raw_values_or_private_paths() -> None:
    canary = "C2_BAD_ARG_CANARY_C:\\private\\path"
    result = AgentRunner(
        provider=ScriptedModelProvider(
            [tool_turn(arguments={"period": "current_month", "secret": canary})]
        ),
        tools=phase_zero_registry(),
    ).run("invalid", "c2-l04")

    assert result.error_code == "invalid_tool_arguments"
    assert canary not in result.model_dump_json()
    assert "Traceback" not in result.model_dump_json()


def test_l05_control_characters_cannot_create_a_forged_json_event() -> None:
    forged_name = 'missing\n{"kind":"forged"}'
    result = AgentRunner(
        provider=ScriptedModelProvider([tool_turn(name=forged_name)]),
        tools=phase_zero_registry(),
    ).run("forged", "c2-l05")

    serialized = result.model_dump_json()
    assert "\n" not in serialized
    assert json.loads(serialized)["error_code"] == "unknown_tool"


def test_l06_concurrent_distinct_runs_keep_separate_result_ids() -> None:
    barrier = threading.Barrier(2)

    class ParallelProvider:
        def complete(
            self,
            messages: list[ConversationMessage],
            tools: list[dict[str, Any]],
            timeout_seconds: float,
        ) -> AssistantTurn:
            del tools, timeout_seconds
            barrier.wait(timeout=3)
            return AssistantTurn(content=f"reply:{messages[0].content}")

    runner = AgentRunner(provider=ParallelProvider(), tools=phase_zero_registry())
    requests = [("alpha", "c2-l06-a"), ("beta", "c2-l06-b")]

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda item: runner.run(*item), requests))

    assert [(result.request_id, result.answer) for result in results] == [
        ("c2-l06-a", "reply:alpha"),
        ("c2-l06-b", "reply:beta"),
    ]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"max_model_turns": 0}, "max_model_turns"),
        ({"provider_timeout_seconds": 0}, "provider_timeout_seconds"),
        ({"provider_timeout_seconds": -1}, "provider_timeout_seconds"),
        ({"provider_timeout_seconds": float("nan")}, "provider_timeout_seconds"),
    ],
)
def test_invalid_runner_limits_are_rejected(kwargs: dict[str, Any], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        AgentRunner(
            provider=ScriptedModelProvider([]),
            tools=phase_zero_registry(),
            **kwargs,
        )
