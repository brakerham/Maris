"""Typed tool registry and the phase-0 virtual finance tool."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, ValidationError


class ToolNotFoundError(LookupError):
    pass


class ToolArgumentsError(ValueError):
    pass


ArgumentsT = TypeVar("ArgumentsT", bound=BaseModel)


@dataclass(frozen=True)
class Tool(Generic[ArgumentsT]):
    name: str
    description: str
    arguments_model: type[ArgumentsT]
    handler: Any

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.arguments_model.model_json_schema(),
            },
        }

    def invoke(self, arguments: dict[str, Any]) -> Any:
        try:
            validated = self.arguments_model.model_validate(arguments)
        except ValidationError as exc:
            raise ToolArgumentsError("Tool arguments failed validation.") from exc
        return self.handler(validated)


class ToolRegistry:
    def __init__(self, tools: list[Tool[Any]]) -> None:
        self._tools = {tool.name: tool for tool in tools}
        if len(self._tools) != len(tools):
            raise ValueError("Tool names must be unique.")

    def schemas(self) -> tuple[dict[str, Any], ...]:
        return tuple(tool.schema() for tool in self._tools.values())

    def contains(self, name: str) -> bool:
        """Return whether a model-provided name matches a trusted registered tool."""

        return name in self._tools

    def invoke(self, name: str, arguments: dict[str, Any]) -> Any:
        try:
            tool = self._tools[name]
        except KeyError as exc:
            raise ToolNotFoundError(f"Unknown tool: {name}") from exc
        return tool.invoke(arguments)


class QueryBudgetArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period: Literal["current_month"] = "current_month"


class VirtualBudgetSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    currency: Literal["CNY"] = "CNY"
    total_budget_cents: int
    spent_cents: int
    reserved_cents: int

    @property
    def available_cents(self) -> int:
        return self.total_budget_cents - self.spent_cents - self.reserved_cents


VIRTUAL_BUDGET = VirtualBudgetSnapshot(
    total_budget_cents=300_000,
    spent_cents=128_650,
    reserved_cents=50_000,
)


def query_budget(arguments: QueryBudgetArguments) -> dict[str, Any]:
    """Return explicit virtual data; this is not a production budget algorithm."""

    return {
        "data_source": "virtual_phase_0",
        "period": arguments.period,
        "currency": VIRTUAL_BUDGET.currency,
        "total_budget_cents": VIRTUAL_BUDGET.total_budget_cents,
        "spent_cents": VIRTUAL_BUDGET.spent_cents,
        "reserved_cents": VIRTUAL_BUDGET.reserved_cents,
        "available_cents": VIRTUAL_BUDGET.available_cents,
    }


def phase_zero_registry() -> ToolRegistry:
    return ToolRegistry(
        [
            Tool(
                name="query_budget",
                description="Query the current month's virtual CNY budget snapshot.",
                arguments_model=QueryBudgetArguments,
                handler=query_budget,
            )
        ]
    )
