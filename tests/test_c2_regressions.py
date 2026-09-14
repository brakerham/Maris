from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest
from pydantic import BaseModel, ConfigDict

from wife_system import cli
from wife_system.agent.loop import AgentRunner
from wife_system.agent.providers import ScriptedModelProvider
from wife_system.agent.types import AssistantTurn, ConversationMessage, RunStatus, ToolCall
from wife_system.tools import Tool, ToolRegistry, phase_zero_registry


class EmptyArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")


def tool_turn(*, name: str = "query_budget", call_id: str = "call-1") -> AssistantTurn:
    return AssistantTurn(tool_calls=(ToolCall(id=call_id, name=name, arguments={}),))


@pytest.mark.parametrize("invalid_output", [object(), {"value": float("nan")}])
def test_invalid_tool_output_returns_structured_tool_error(invalid_output: Any) -> None:
    registry = ToolRegistry(
        [
            Tool(
                "bad_output",
                "Return an invalid output",
                EmptyArguments,
                lambda arguments: invalid_output,
            )
        ]
    )
    result = AgentRunner(
        provider=ScriptedModelProvider([tool_turn(name="bad_output")]),
        tools=registry,
    ).run("bad output", "regression-invalid-output")

    assert result.status is RunStatus.ERROR
    assert result.error_code == "tool_error"


def test_concurrent_identical_requests_execute_once_and_replay() -> None:
    provider_entered = threading.Event()
    release_provider = threading.Event()

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
            self.calls += 1
            provider_entered.set()
            assert release_provider.wait(timeout=3)
            return AssistantTurn(content="same result")

    provider = BlockingProvider()
    runner = AgentRunner(provider=provider, tools=phase_zero_registry())
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(runner.run, "same", "regression-concurrent")
        assert provider_entered.wait(timeout=3)
        second = pool.submit(runner.run, "same", "regression-concurrent")
        release_provider.set()
        results = [first.result(timeout=3), second.result(timeout=3)]

    assert provider.calls == 1
    assert all(result.answer == "same result" for result in results)
    assert sum(result.events[-1].kind == "cache_hit" for result in results) == 1


def test_tool_events_include_call_id_and_duration() -> None:
    result = AgentRunner(
        provider=ScriptedModelProvider(
            [tool_turn(call_id="observable-call"), AssistantTurn(content="done")]
        ),
        tools=phase_zero_registry(),
    ).run("observe", "regression-events")

    events = [event for event in result.events if event.kind.startswith("tool_")]
    assert events
    assert all(event.tool_call_id == "observable-call" for event in events)
    assert any(event.duration_ms is not None for event in events)


def test_unknown_tool_does_not_echo_model_controlled_name() -> None:
    private_name = "private user message copied by model"
    result = AgentRunner(
        provider=ScriptedModelProvider([tool_turn(name=private_name)]),
        tools=phase_zero_registry(),
    ).run(private_name, "regression-private-tool-name")

    assert result.error_code == "unknown_tool"
    assert private_name not in result.model_dump_json()


@pytest.mark.parametrize("timeout", [float("nan"), float("inf"), -float("inf")])
def test_runner_rejects_non_finite_timeout(timeout: float) -> None:
    with pytest.raises(ValueError, match="provider_timeout_seconds"):
        AgentRunner(
            provider=ScriptedModelProvider([]),
            tools=phase_zero_registry(),
            provider_timeout_seconds=timeout,
        )


@pytest.mark.parametrize("timeout", ["0", "nan", "inf"])
def test_cli_rejects_invalid_timeout_without_traceback(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    timeout: str,
) -> None:
    monkeypatch.setattr(
        "sys.argv", ["wife-agent", "x", "--provider", "offline", "--timeout", timeout]
    )

    with pytest.raises(SystemExit) as captured:
        cli.main()

    stderr = capsys.readouterr().err
    assert captured.value.code != 0
    assert "Traceback" not in stderr
