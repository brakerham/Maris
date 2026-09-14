"""Provider-neutral, bounded tool-calling loop."""

from __future__ import annotations

import hashlib
import json
import math
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from wife_system.agent.providers import ModelProvider, ProviderError, ProviderTimeoutError
from wife_system.agent.types import (
    AgentRunResult,
    ConversationMessage,
    ExecutionEvent,
    RunStatus,
)
from wife_system.tools import ToolArgumentsError, ToolNotFoundError, ToolRegistry


@dataclass
class AgentRunner:
    provider: ModelProvider
    tools: ToolRegistry
    max_model_turns: int = 4
    provider_timeout_seconds: float = 15.0
    _completed: dict[str, tuple[str, AgentRunResult]] = field(default_factory=dict, init=False)
    _in_flight: dict[str, tuple[str, threading.Event]] = field(default_factory=dict, init=False)
    _request_lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def __post_init__(self) -> None:
        if self.max_model_turns < 1:
            raise ValueError("max_model_turns must be at least 1.")
        if (
            not math.isfinite(self.provider_timeout_seconds)
            or self.provider_timeout_seconds <= 0
        ):
            raise ValueError("provider_timeout_seconds must be finite and positive.")

    def run(self, user_message: str, request_id: str) -> AgentRunResult:
        if not request_id.strip():
            raise ValueError("request_id must not be blank.")
        fingerprint = hashlib.sha256(user_message.encode("utf-8")).hexdigest()
        while True:
            with self._request_lock:
                cached = self._completed.get(request_id)
                if cached is not None:
                    old_fingerprint, old_result = cached
                    if old_fingerprint != fingerprint:
                        return self._duplicate_request_conflict(request_id)
                    return self._replay(old_result)

                in_flight = self._in_flight.get(request_id)
                if in_flight is None:
                    completion = threading.Event()
                    self._in_flight[request_id] = (fingerprint, completion)
                    break

                active_fingerprint, completion = in_flight
                if active_fingerprint != fingerprint:
                    return self._duplicate_request_conflict(request_id)
            completion.wait()

        try:
            result = self._run_uncached(user_message, request_id)
        except BaseException:
            with self._request_lock:
                self._in_flight.pop(request_id, None)
                completion.set()
            raise

        with self._request_lock:
            self._completed[request_id] = (fingerprint, result)
            self._in_flight.pop(request_id, None)
            completion.set()
        return result

    def _run_uncached(self, user_message: str, request_id: str) -> AgentRunResult:
        events: list[ExecutionEvent] = []
        messages = [ConversationMessage(role="user", content=user_message)]
        executed_call_ids: set[str] = set()
        executed_calls: set[str] = set()

        for model_turn in range(1, self.max_model_turns + 1):
            self._event(events, "model_requested", model_turn=model_turn)
            try:
                turn = self.provider.complete(
                    messages,
                    self.tools.schemas(),
                    self.provider_timeout_seconds,
                )
            except ProviderTimeoutError as exc:
                return self._finish_error(
                    request_id, events, exc.code, "Model request timed out."
                )
            except ProviderError as exc:
                return self._finish_error(
                    request_id, events, exc.code, "Model provider failed."
                )
            except TimeoutError:
                return self._finish_error(
                    request_id, events, "model_timeout", "Model request timed out."
                )

            self._event(
                events,
                "model_responded",
                model_turn=model_turn,
                outcome="tool_calls" if turn.tool_calls else "text",
            )

            if turn.tool_calls:
                messages.append(
                    ConversationMessage(
                        role="assistant", content=turn.content, tool_calls=turn.tool_calls
                    )
                )
                for call in turn.tool_calls:
                    if call.id in executed_call_ids:
                        return self._finish_error(
                            request_id,
                            events,
                            "duplicate_tool_call",
                            "The model repeated a tool call id.",
                        )
                    executed_call_ids.add(call.id)
                    signature = self._call_signature(call.name, call.arguments)
                    if signature in executed_calls:
                        return self._finish_error(
                            request_id,
                            events,
                            "duplicate_tool_call",
                            "The model repeated an identical tool call.",
                        )
                    executed_calls.add(signature)
                    if not self.tools.contains(call.name):
                        return self._finish_error(
                            request_id,
                            events,
                            "unknown_tool",
                            "The model requested an unknown tool.",
                        )
                    self._event(
                        events,
                        "tool_started",
                        model_turn=model_turn,
                        tool_name=call.name,
                        tool_call_id=call.id,
                    )
                    started_at = time.perf_counter()
                    try:
                        output = self.tools.invoke(call.name, call.arguments)
                        serialized_output = json.dumps(
                            output,
                            ensure_ascii=False,
                            allow_nan=False,
                            separators=(",", ":"),
                        )
                    except ToolNotFoundError:
                        return self._finish_error(
                            request_id,
                            events,
                            "unknown_tool",
                            "The model requested an unknown tool.",
                        )
                    except ToolArgumentsError:
                        return self._finish_error(
                            request_id,
                            events,
                            "invalid_tool_arguments",
                            f"Arguments for {call.name} failed validation.",
                        )
                    except Exception:
                        return self._finish_error(
                            request_id,
                            events,
                            "tool_error",
                            f"Tool {call.name} failed.",
                        )
                    self._event(
                        events,
                        "tool_finished",
                        model_turn=model_turn,
                        tool_name=call.name,
                        tool_call_id=call.id,
                        duration_ms=(time.perf_counter() - started_at) * 1000,
                        outcome="success",
                    )
                    messages.append(
                        ConversationMessage(
                            role="tool",
                            tool_call_id=call.id,
                            content=serialized_output,
                        )
                    )
                continue

            if turn.content:
                self._event(events, "run_finished", model_turn=model_turn, outcome="success")
                result = AgentRunResult(
                    request_id=request_id,
                    status=RunStatus.SUCCESS,
                    answer=turn.content,
                    events=tuple(events),
                )
                return result

            return self._finish_error(
                request_id,
                events,
                "empty_model_response",
                "The model returned neither text nor a tool call.",
            )

        return self._finish_error(
            request_id,
            events,
            "max_model_turns_exceeded",
            "The agent reached its model-turn limit.",
        )

    @staticmethod
    def _call_signature(name: str, arguments: dict[str, Any]) -> str:
        canonical = json.dumps(arguments, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return f"{name}:{canonical}"

    @staticmethod
    def _event(events: list[ExecutionEvent], kind: Any, **values: Any) -> None:
        events.append(ExecutionEvent(sequence=len(events) + 1, kind=kind, **values))

    def _finish_error(
        self,
        request_id: str,
        events: list[ExecutionEvent],
        code: str,
        message: str,
    ) -> AgentRunResult:
        return self._error(request_id, events, code, message)

    @staticmethod
    def _replay(result: AgentRunResult) -> AgentRunResult:
        return result.model_copy(
            update={
                "events": result.events
                + (
                    ExecutionEvent(
                        sequence=len(result.events) + 1,
                        kind="cache_hit",
                        outcome="same_request",
                    ),
                )
            }
        )

    @classmethod
    def _duplicate_request_conflict(cls, request_id: str) -> AgentRunResult:
        return cls._error(
            request_id,
            [],
            "duplicate_request_conflict",
            "The request id was already used for different input.",
        )

    @staticmethod
    def _error(
        request_id: str,
        events: list[ExecutionEvent],
        code: str,
        message: str,
    ) -> AgentRunResult:
        finished = list(events)
        finished.append(
            ExecutionEvent(
                sequence=len(finished) + 1,
                kind="run_finished",
                outcome=code,
            )
        )
        return AgentRunResult(
            request_id=request_id,
            status=RunStatus.ERROR,
            error_code=code,
            error_message=message,
            events=tuple(finished),
        )
