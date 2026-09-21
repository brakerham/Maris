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
from wife_system.agent.context import RunContext
from wife_system.agent.prompts import FINANCE_SYSTEM_PROMPT_V1
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
    max_tool_calls: int = 8
    max_write_calls: int = 1
    provider_timeout_seconds: float = 15.0
    tool_timeout_seconds: float = 10.0
    max_provider_retries: int = 1
    _completed: dict[str, tuple[str, AgentRunResult]] = field(default_factory=dict, init=False)
    _in_flight: dict[str, tuple[str, threading.Event]] = field(default_factory=dict, init=False)
    _request_lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def __post_init__(self) -> None:
        if self.max_model_turns < 1:
            raise ValueError("max_model_turns must be at least 1.")
        if self.max_tool_calls < 1 or self.max_tool_calls > 8:
            raise ValueError("max_tool_calls must be between 1 and 8.")
        if self.max_write_calls < 0 or self.max_write_calls > 1:
            raise ValueError("max_write_calls must be between 0 and 1.")
        if self.max_model_turns > 4:
            raise ValueError("max_model_turns cannot exceed 4.")
        if (
            not math.isfinite(self.provider_timeout_seconds)
            or not 0 < self.provider_timeout_seconds <= 15
        ):
            raise ValueError("provider_timeout_seconds must be finite and between 0 and 15.")
        if not math.isfinite(self.tool_timeout_seconds) or not 0 < self.tool_timeout_seconds <= 10:
            raise ValueError("tool_timeout_seconds must be finite and between 0 and 10.")
        if self.max_provider_retries not in {0, 1}:
            raise ValueError("max_provider_retries must be 0 or 1.")

    def run(
        self,
        user_message: str,
        request_id: str | None = None,
        *,
        context: RunContext | None = None,
    ) -> AgentRunResult:
        request_id = request_id or (str(context.agent_run_id) if context is not None else "")
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
            result = self._run_uncached(user_message, request_id, context)
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

    def _run_uncached(
        self, user_message: str, request_id: str, context: RunContext | None
    ) -> AgentRunResult:
        events: list[ExecutionEvent] = []
        messages = []
        if context is not None:
            messages.append(ConversationMessage(role="system", content=FINANCE_SYSTEM_PROMPT_V1))
        messages.append(ConversationMessage(role="user", content=user_message))
        executed_call_ids: set[str] = set()
        executed_calls: set[str] = set()
        total_tool_calls = 0
        total_write_calls = 0

        for model_turn in range(1, self.max_model_turns + 1):
            self._event(events, "model_requested", model_turn=model_turn)
            turn = None
            provider_attempts = 1 + (self.max_provider_retries if context is not None else 0)
            for attempt in range(provider_attempts):
                try:
                    turn = self.provider.complete(
                        messages,
                        self.tools.schemas(context),
                        self.provider_timeout_seconds,
                    )
                    break
                except ProviderTimeoutError as exc:
                    if attempt + 1 < provider_attempts and exc.retryable:
                        continue
                    return self._finish_error(
                        request_id, events, exc.code, "Model request timed out."
                    )
                except ProviderError as exc:
                    if attempt + 1 < provider_attempts and exc.retryable:
                        continue
                    return self._finish_error(
                        request_id, events, exc.code, "Model provider failed."
                    )
                except TimeoutError:
                    if attempt + 1 < provider_attempts:
                        continue
                    return self._finish_error(
                        request_id, events, "model_timeout", "Model request timed out."
                    )
            if turn is None:  # pragma: no cover - defensive guard
                return self._finish_error(
                    request_id, events, "model_unavailable", "Model provider failed."
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
                    total_tool_calls += 1
                    if total_tool_calls > self.max_tool_calls:
                        return self._finish_error(
                            request_id,
                            events,
                            "tool_limit_exceeded",
                            "The agent reached its tool-call limit.",
                        )
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
                    if self.tools.is_write(call.name):
                        total_write_calls += 1
                        if total_write_calls > self.max_write_calls:
                            return self._finish_error(
                                request_id,
                                events,
                                "write_limit_exceeded",
                                "The agent reached its finance-write limit.",
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
                        output = self.tools.invoke(call.name, call.arguments, context)
                        duration_seconds = time.perf_counter() - started_at
                        if duration_seconds > self.tool_timeout_seconds and not self.tools.is_write(call.name):
                            return self._finish_error(
                                request_id,
                                events,
                                "tool_timeout",
                                "The tool exceeded its cooperative deadline.",
                            )
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
                        duration_ms=duration_seconds * 1000,
                        outcome="success",
                    )
                    if isinstance(output, dict) and output.get("status") in {
                        "needs_input",
                        "needs_confirmation",
                    }:
                        pending_action_id = output.get("pending_action_id")
                        pause_reason = str(output["status"])
                        self._event(
                            events,
                            "run_finished",
                            model_turn=model_turn,
                            outcome=pause_reason,
                        )
                        return AgentRunResult(
                            request_id=request_id,
                            status=RunStatus.PAUSED,
                            pending_action_id=str(pending_action_id),
                            pause_reason=pause_reason,
                            result=output,
                            events=tuple(events),
                        )
                    if isinstance(output, dict) and output.get("status") == "error":
                        safe_error = output.get("error")
                        code = (
                            safe_error.get("code", "tool_error")
                            if isinstance(safe_error, dict)
                            else "tool_error"
                        )
                        retryable = (
                            bool(safe_error.get("retryable", False))
                            if isinstance(safe_error, dict)
                            else False
                        )
                        message = (
                            str(safe_error.get("message", "The tool failed."))
                            if isinstance(safe_error, dict)
                            else "The tool failed."
                        )
                        return self._finish_error(
                            request_id,
                            events,
                            code,
                            message if not retryable else message,
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
