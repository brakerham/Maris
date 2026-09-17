"""Provider-neutral messages and structured execution results."""

# 面向对象的知识 就是 对象的设计
from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ToolCall(BaseModel):
    """A model request to invoke one registered tool."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    arguments: dict[str, Any]


class AssistantTurn(BaseModel):
    """One provider response, containing either text or tool calls."""

    model_config = ConfigDict(extra="forbid")

    content: str | None = None
    tool_calls: tuple[ToolCall, ...] = () # 为什么这里用的 是 tuple 而不是 list,因为 这里 不要求数据改变就是 list 会变，但是 这里如果使用了 tuple就 从数据类型 和 静态语法的角度 很他 定下来了



class ConversationMessage(BaseModel):
    """A provider-neutral conversation message."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None
    tool_call_id: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()


class RunStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    PAUSED = "paused"


class ExecutionEvent(BaseModel):
    """A deliberately small event that excludes prompts, secrets, and raw logs."""

    model_config = ConfigDict(extra="forbid")

    sequence: int = Field(ge=1)
    kind: Literal[
        "model_requested",
        "model_responded",
        "tool_started",
        "tool_finished",
        "cache_hit",
        "run_finished",
    ]
    model_turn: int | None = Field(default=None, ge=1)
    tool_name: str | None = None
    tool_call_id: str | None = None
    duration_ms: float | None = Field(default=None, ge=0)
    outcome: str | None = None


class AgentRunResult(BaseModel):
    """Stable result returned by the core and CLI."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    status: RunStatus
    answer: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    pending_action_id: str | None = None
    pause_reason: str | None = None
    result: dict[str, Any] | None = None
    replayed: bool = False
    events: tuple[ExecutionEvent, ...]
