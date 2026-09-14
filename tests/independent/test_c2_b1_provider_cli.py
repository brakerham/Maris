from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from typing import Any
from urllib import error

import pytest

from wife_system import cli
from wife_system.agent.loop import AgentRunner
from wife_system.agent.providers import (
    DeepSeekProvider,
    ProviderError,
    ProviderTimeoutError,
    _urllib_transport,
)
from wife_system.agent.types import AssistantTurn, ConversationMessage, RunStatus
from wife_system.tools import phase_zero_registry


@pytest.mark.parametrize(
    ("status", "code", "retryable"),
    [
        (400, "model_invalid_request", False),
        (401, "model_auth_failed", False),
        (402, "model_balance_exhausted", False),
        (422, "model_invalid_request", False),
        (429, "model_rate_limited", True),
        (500, "model_unavailable", True),
        (503, "model_unavailable", True),
    ],
)
def test_m02_to_m05_http_failures_map_without_network(
    monkeypatch: pytest.MonkeyPatch, status: int, code: str, retryable: bool
) -> None:
    def fail(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise error.HTTPError(
            url="https://invalid.local",
            code=status,
            msg="private upstream text",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr("wife_system.agent.providers.request.urlopen", fail)

    with pytest.raises(ProviderError) as captured:
        _urllib_transport("https://invalid.local", {}, b"{}", 1.0)

    assert captured.value.code == code
    assert captured.value.retryable is retryable
    assert "private upstream text" not in str(captured.value)


def test_m01_socket_timeout_maps_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise socket.timeout("private socket text")

    monkeypatch.setattr("wife_system.agent.providers.request.urlopen", timeout)

    with pytest.raises(ProviderTimeoutError) as captured:
        _urllib_transport("https://invalid.local", {}, b"{}", 1.0)

    assert captured.value.code == "model_timeout"
    assert "private socket text" not in str(captured.value)


def test_m01_timeout_is_mapped_by_the_agent_without_tool_execution() -> None:
    class TimeoutProvider:
        def complete(self, *args: Any, **kwargs: Any) -> None:
            del args, kwargs
            raise ProviderTimeoutError("C2_PRIVATE_TIMEOUT_DETAIL")

    result = AgentRunner(provider=TimeoutProvider(), tools=phase_zero_registry()).run(
        "timeout", "c2-m01"
    )

    assert result.error_code == "model_timeout"
    assert "C2_PRIVATE_TIMEOUT_DETAIL" not in result.model_dump_json()
    assert not any(event.kind.startswith("tool_") for event in result.events)


@pytest.mark.parametrize(
    "raw",
    [
        b"not-json",
        b'{"choices":[]}',
        b'{"choices":[{"message":{"tool_calls":[{"function":{"name":"x","arguments":"{}"}}]}}]}',
        b'{"choices":[{"message":{"tool_calls":[{"id":"x","function":{"name":"x","arguments":"[1]"}}]}}]}',
        b'{"choices":[{"message":{"content":[]}}]}',
    ],
)
def test_m06_invalid_deepseek_responses_map_to_stable_error(raw: bytes) -> None:
    provider = DeepSeekProvider(api_key="C2_CANARY_KEY", transport=lambda *_: raw)

    with pytest.raises(ProviderError) as captured:
        provider.complete([ConversationMessage(role="user", content="x")], [], 1.0)

    assert captured.value.code == "model_invalid_response"
    assert captured.value.retryable is False
    assert "C2_CANARY_KEY" not in str(captured.value)


def test_a04_malformed_provider_tool_json_never_reaches_the_tool() -> None:
    raw = (
        b'{"choices":[{"message":{"tool_calls":[{"id":"bad-json",'
        b'"function":{"name":"query_budget","arguments":"{truncated"}}]}}]}'
    )
    provider = DeepSeekProvider(api_key="C2_CANARY_KEY", transport=lambda *_: raw)

    result = AgentRunner(provider=provider, tools=phase_zero_registry()).run(
        "bad json", "c2-a04"
    )

    assert result.error_code == "model_invalid_response"
    assert not any(event.kind.startswith("tool_") for event in result.events)


def test_deepseek_boundary_serializes_neutral_messages_and_tool_schema() -> None:
    captured: dict[str, Any] = {}

    def transport(url: str, headers: dict[str, str], body: bytes, timeout: float) -> bytes:
        captured.update(url=url, headers=headers, body=json.loads(body), timeout=timeout)
        return b'{"choices":[{"message":{"content":"ok"}}]}'

    provider = DeepSeekProvider(api_key="C2_CANARY_KEY", transport=transport)
    turn = provider.complete(
        [ConversationMessage(role="user", content="budget")],
        phase_zero_registry().schemas(),
        2.5,
    )

    assert turn.content == "ok"
    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["timeout"] == 2.5
    assert captured["body"]["tools"][0]["function"]["name"] == "query_budget"
    assert captured["body"]["messages"] == [{"role": "user", "content": "budget"}]
    assert "C2_CANARY_KEY" not in json.dumps(captured["body"])
    assert "C2_CANARY_KEY" not in repr(provider)


def test_provider_error_code_is_preserved_and_private_detail_is_sanitized() -> None:
    class FailedProvider:
        def complete(self, *args: Any, **kwargs: Any) -> None:
            del args, kwargs
            raise ProviderError(
                "Bearer C2_SECRET upstream body",
                code="model_rate_limited",
                retryable=True,
            )

    result = AgentRunner(provider=FailedProvider(), tools=phase_zero_registry()).run(
        "message", "c2-provider-error"
    )

    assert result.error_code == "model_rate_limited"
    assert "C2_SECRET" not in result.model_dump_json()
    assert "upstream body" not in result.model_dump_json()


def test_m05_runner_recovers_after_a_provider_failure() -> None:
    class RecoveringProvider:
        calls = 0

        def complete(self, *args: Any, **kwargs: Any) -> AssistantTurn:
            del args, kwargs
            self.calls += 1
            if self.calls == 1:
                raise ProviderError("private", code="model_unavailable", retryable=True)
            return AssistantTurn(content="recovered")

    provider = RecoveringProvider()
    runner = AgentRunner(provider=provider, tools=phase_zero_registry())

    failed = runner.run("first", "c2-m05-first")
    recovered = runner.run("second", "c2-m05-second")

    assert failed.error_code == "model_unavailable"
    assert recovered.status is RunStatus.SUCCESS
    assert recovered.answer == "recovered"


def test_m07_offline_cli_does_not_open_a_network_connection(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def forbidden_network(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise AssertionError("network access attempted")

    monkeypatch.setattr("wife_system.agent.providers.request.urlopen", forbidden_network)
    monkeypatch.setattr(
        sys,
        "argv",
        ["wife-agent", "offline budget", "--provider", "offline", "--request-id", "c2-cli"],
    )

    assert cli.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "success"
    assert payload["request_id"] == "c2-cli"


def test_m08_deepseek_cli_without_key_fails_before_network() -> None:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"DEEPSEEK_API_KEY", "DEEPSEEK_MODEL"}
    }

    completed = subprocess.run(
        [sys.executable, "-m", "wife_system.cli", "x", "--provider", "deepseek"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
        timeout=10,
        check=False,
    )

    assert completed.returncode != 0
    assert "DEEPSEEK_API_KEY is required" in completed.stderr
    assert "Traceback" not in completed.stderr


def test_cli_rejects_zero_timeout_without_internal_traceback() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "wife_system.cli",
            "x",
            "--provider",
            "offline",
            "--timeout",
            "0",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
        check=False,
    )

    assert completed.returncode != 0
    assert "Traceback" not in completed.stderr


def test_virtual_tool_schema_and_result_use_strict_integer_cents() -> None:
    registry = phase_zero_registry()
    schema = registry.schemas()[0]["function"]["parameters"]
    result = registry.invoke("query_budget", {"period": "current_month"})

    assert schema["additionalProperties"] is False
    assert result["currency"] == "CNY"
    assert all(
        isinstance(result[key], int)
        for key in (
            "total_budget_cents",
            "spent_cents",
            "reserved_cents",
            "available_cents",
        )
    )
    assert result["available_cents"] == 121_350
