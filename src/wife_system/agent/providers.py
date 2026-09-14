"""Model-provider boundary, deterministic doubles, and DeepSeek adapter."""

from __future__ import annotations

import json
import socket
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib import error, request

from wife_system.agent.types import AssistantTurn, ConversationMessage, ToolCall


class ProviderError(RuntimeError):
    """A model provider failed or returned an unusable response."""

    def __init__(self, message: str, *, code: str = "model_unavailable", retryable: bool = True):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class ProviderTimeoutError(ProviderError):
    """A model provider did not answer within the configured timeout."""

    def __init__(self, message: str = "Model request timed out.") -> None:
        super().__init__(message, code="model_timeout", retryable=True)


class ModelProvider(Protocol):
    def complete(
        self,
        messages: Sequence[ConversationMessage],
        tools: Sequence[dict[str, Any]],
        timeout_seconds: float,
    ) -> AssistantTurn:
        """Return the next provider-neutral assistant turn."""


@dataclass
class ScriptedModelProvider:
    """Deterministic test double whose turns still exercise the real loop."""

    turns: list[AssistantTurn]
    calls: int = 0

    def complete(
        self,
        messages: Sequence[ConversationMessage],
        tools: Sequence[dict[str, Any]],
        timeout_seconds: float,
    ) -> AssistantTurn:
        del messages, tools, timeout_seconds
        self.calls += 1
        if not self.turns:
            raise ProviderError("The scripted provider has no turn left.")
        return self.turns.pop(0)


@dataclass
class DeterministicBudgetProvider:
    """Offline demonstration provider for the virtual budget tool."""

    calls: int = 0

    def complete(
        self,
        messages: Sequence[ConversationMessage],
        tools: Sequence[dict[str, Any]],
        timeout_seconds: float,
    ) -> AssistantTurn:
        del tools, timeout_seconds
        self.calls += 1
        tool_messages = [message for message in messages if message.role == "tool"]
        if not tool_messages:
            return AssistantTurn(
                tool_calls=(
                    ToolCall(
                        id="offline-budget-call",
                        name="query_budget",
                        arguments={"period": "current_month"},
                    ),
                )
            )

        tool_message = tool_messages[-1]
        if tool_message.tool_call_id != "offline-budget-call":
            raise ProviderError(
                "The offline provider did not receive its tool result.",
                code="model_invalid_response",
                retryable=False,
            )
        payload = json.loads(tool_message.content or "{}")
        if payload.get("data_source") != "virtual_phase_0":
            raise ProviderError(
                "The offline provider received an unexpected tool result.",
                code="model_invalid_response",
                retryable=False,
            )
        return AssistantTurn(
            content=(
                "虚拟预算：本月预算 {budget:.2f} 元，已支出 {spent:.2f} 元，"
                "预留 {reserved:.2f} 元，可灵活使用 {available:.2f} 元。"
            ).format(
                budget=payload["total_budget_cents"] / 100,
                spent=payload["spent_cents"] / 100,
                reserved=payload["reserved_cents"] / 100,
                available=payload["available_cents"] / 100,
            )
        )


Transport = Callable[[str, dict[str, str], bytes, float], bytes]


def _urllib_transport(
    url: str, headers: dict[str, str], body: bytes, timeout_seconds: float
) -> bytes:
    http_request = request.Request(url, data=body, headers=headers, method="POST")
    try:
        with request.urlopen(http_request, timeout=timeout_seconds) as response:
            return response.read()
    except (TimeoutError, socket.timeout) as exc:
        raise ProviderTimeoutError("DeepSeek request timed out.") from exc
    except error.HTTPError as exc:
        code, retryable = {
            400: ("model_invalid_request", False),
            401: ("model_auth_failed", False),
            402: ("model_balance_exhausted", False),
            422: ("model_invalid_request", False),
            429: ("model_rate_limited", True),
            500: ("model_unavailable", True),
            503: ("model_unavailable", True),
        }.get(exc.code, ("model_unavailable", True))
        raise ProviderError(
            f"DeepSeek returned HTTP {exc.code}.", code=code, retryable=retryable
        ) from exc
    except error.URLError as exc:
        raise ProviderError(
            "DeepSeek could not be reached.", code="model_unavailable", retryable=True
        ) from exc


@dataclass
class DeepSeekProvider:
    """Thin OpenAI-compatible adapter; the API key never enters run events."""

    api_key: str = field(repr=False)
    model: str = "deepseek-chat"
    base_url: str = "https://api.deepseek.com"
    transport: Transport = field(default=_urllib_transport, repr=False)

    def complete(
        self,
        messages: Sequence[ConversationMessage],
        tools: Sequence[dict[str, Any]],
        timeout_seconds: float,
    ) -> AssistantTurn:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [self._message_payload(message) for message in messages],
            "tools": list(tools),
            "tool_choice": "auto",
            "thinking": {"type": "disabled"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        raw = self.transport(
            f"{self.base_url.rstrip('/')}/chat/completions",
            headers,
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout_seconds,
        )
        try:
            message = json.loads(raw)["choices"][0]["message"]
            calls = tuple(self._parse_tool_call(item) for item in message.get("tool_calls", []))
            return AssistantTurn(content=message.get("content"), tool_calls=calls)
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ProviderError(
                "DeepSeek returned an invalid response.",
                code="model_invalid_response",
                retryable=False,
            ) from exc

    @staticmethod
    def _message_payload(message: ConversationMessage) -> dict[str, Any]:
        result: dict[str, Any] = {"role": message.role, "content": message.content}
        if message.tool_call_id is not None:
            result["tool_call_id"] = message.tool_call_id
        if message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": json.dumps(call.arguments, ensure_ascii=False),
                    },
                }
                for call in message.tool_calls
            ]
        return result

    @staticmethod
    def _parse_tool_call(item: dict[str, Any]) -> ToolCall:
        function = item["function"]
        arguments = json.loads(function["arguments"])
        if not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be an object.")
        return ToolCall(id=item["id"], name=function["name"], arguments=arguments)
