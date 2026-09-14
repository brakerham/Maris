from __future__ import annotations

import json

import pytest

from wife_system.agent.providers import DeepSeekProvider, ProviderError
from wife_system.agent.types import ConversationMessage
from wife_system.tools import phase_zero_registry


def test_deepseek_adapter_maps_tool_call_without_executing_it() -> None:
    captured: dict[str, object] = {}

    def transport(url: str, headers: dict[str, str], body: bytes, timeout: float) -> bytes:
        captured.update(url=url, headers=headers, body=json.loads(body), timeout=timeout)
        return json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call-7",
                                    "type": "function",
                                    "function": {
                                        "name": "query_budget",
                                        "arguments": '{"period":"current_month"}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        ).encode()

    provider = DeepSeekProvider(api_key="secret-value", transport=transport)
    turn = provider.complete(
        [ConversationMessage(role="user", content="budget")],
        phase_zero_registry().schemas(),
        3.0,
    )

    assert turn.tool_calls[0].name == "query_budget"
    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["timeout"] == 3.0
    assert captured["headers"] == {
        "Authorization": "Bearer secret-value",
        "Content-Type": "application/json",
    }
    assert captured["body"]["tools"][0]["function"]["name"] == "query_budget"
    assert captured["body"]["thinking"] == {"type": "disabled"}


def test_deepseek_adapter_rejects_invalid_response() -> None:
    provider = DeepSeekProvider(
        api_key="secret-value", transport=lambda *_: b'{"choices": []}'
    )

    with pytest.raises(ProviderError, match="invalid response"):
        provider.complete([ConversationMessage(role="user", content="x")], [], 1.0)


def test_api_key_is_hidden_from_repr() -> None:
    provider = DeepSeekProvider(api_key="secret-value")

    assert "secret-value" not in repr(provider)
