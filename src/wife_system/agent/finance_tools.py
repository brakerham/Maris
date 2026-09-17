"""Strict P2 finance tool contracts and adapters for the P1 service."""

from __future__ import annotations

import uuid
import re
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator
from sqlalchemy.exc import SQLAlchemyError

from wife_system.agent.context import ToolExecutionContext
from wife_system.agent.pending import PendingAction, PendingActionError, PendingActionStore
from wife_system.finance import FinanceError, FinanceService
from wife_system.finance.money import parse_minor
from wife_system.finance.schemas import (
    AccountView,
    CategoryView,
    MonthlySnapshot,
    RecordExpense,
    TransactionView,
)
from wife_system.tools import Tool, ToolRegistry


MoneyText = Annotated[StrictStr, Field(min_length=1, max_length=32)]


class StrictToolModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ListAccountsInput(StrictToolModel):
    pass


class ListCategoriesInput(StrictToolModel):
    kind: Literal["income", "expense"] | None = None


class GetAccountBalanceInput(StrictToolModel):
    account_id: uuid.UUID
    as_of: datetime | None = None

    @field_validator("as_of")
    @classmethod
    def aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("as_of must include a timezone")
        return value


class ListTransactionsInput(StrictToolModel):
    start: datetime | None = None
    end: datetime | None = None
    limit: int = Field(default=20, ge=1, le=50)

    @field_validator("start", "end")
    @classmethod
    def aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("transaction bounds must include a timezone")
        return value


class GetMonthlySnapshotInput(StrictToolModel):
    period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    as_of: datetime | None = None
    account_ids: list[uuid.UUID] = Field(default_factory=list, max_length=20)
    category_ids: list[uuid.UUID] = Field(default_factory=list, max_length=50)

    @field_validator("as_of")
    @classmethod
    def aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("as_of must include a timezone")
        return value


class RecordExpenseToolInput(StrictToolModel):
    amount: MoneyText | None = None
    account_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    occurred_at: datetime | None = None

    @field_validator("occurred_at")
    @classmethod
    def aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("occurred_at must include a timezone")
        return value


class ToolError(StrictToolModel):
    code: str
    message: str
    retryable: bool


class CommittedWrite(StrictToolModel):
    status: Literal["committed"] = "committed"
    result_type: str
    result_id: uuid.UUID
    replayed: bool
    amount_minor: int
    currency: Literal["CNY"] = "CNY"


class NeedsInput(StrictToolModel):
    status: Literal["needs_input"] = "needs_input"
    pending_action_id: uuid.UUID
    missing_fields: list[str]
    question_code: str
    choices: list[dict[str, str]] = Field(default_factory=list)


class NeedsConfirmation(StrictToolModel):
    status: Literal["needs_confirmation"] = "needs_confirmation"
    pending_action_id: uuid.UUID
    confirmation_code: str
    summary: dict[str, str]


class FailedTool(StrictToolModel):
    status: Literal["error"] = "error"
    error: ToolError


WriteToolOutput = Annotated[
    CommittedWrite | NeedsInput | NeedsConfirmation | FailedTool,
    Field(discriminator="status"),
]


class AccountsOutput(StrictToolModel):
    status: Literal["ok"] = "ok"
    items: list[AccountView]
    truncated: bool
    as_of: datetime


class CategoriesOutput(StrictToolModel):
    status: Literal["ok"] = "ok"
    items: list[CategoryView]
    truncated: bool
    as_of: datetime


class AccountBalanceOutput(StrictToolModel):
    status: Literal["ok"] = "ok"
    account_id: uuid.UUID
    balance_minor: int
    currency: Literal["CNY"] = "CNY"
    as_of: datetime


class TransactionsOutput(StrictToolModel):
    status: Literal["ok"] = "ok"
    items: list[TransactionView]
    truncated: bool
    start: datetime
    end: datetime
    as_of: datetime


class MonthlySnapshotOutput(StrictToolModel):
    status: Literal["ok"] = "ok"
    snapshot: MonthlySnapshot


SAFE_MESSAGES = {
    "permission_denied": "This action is not permitted.",
    "source_event_id_unavailable": "A stable source event id is unavailable.",
    "pending_action_not_found": "The pending action was not found.",
    "pending_action_expired": "The pending action has expired.",
    "pending_action_stale": "The pending action must be reviewed again.",
    "database_unavailable": "The finance database is unavailable.",
    "persistence_error": "The request could not be persisted.",
    "not_found": "A referenced finance resource was not found.",
    "archived_resource": "A referenced finance resource is archived.",
    "validation_error": "The finance request is invalid.",
    "invalid_amount_precision": "The amount must have at most two decimal places.",
    "amount_out_of_range": "The amount is outside the supported range.",
    "unsupported_currency": "Only CNY is supported.",
    "duplicate_request_conflict": "The source event was reused with different data.",
    "concurrent_modification": "The finance data changed concurrently.",
    "multiple_expenses_unsupported": "Multiple expenses in one message are not supported.",
}


def failed(code: str, *, retryable: bool = False) -> dict[str, Any]:
    return FailedTool(
        error=ToolError(
            code=code,
            message=SAFE_MESSAGES.get(code, "The finance request could not be completed."),
            retryable=retryable,
        )
    ).model_dump(mode="json")


def format_minor(value: int) -> str:
    sign = "-" if value < 0 else ""
    absolute = abs(value)
    return f"{sign}{absolute // 100}.{absolute % 100:02d}"


class FinanceToolAdapter:
    def __init__(self, finance: FinanceService, pending: PendingActionStore) -> None:
        self.finance = finance
        self.pending = pending

    @staticmethod
    def _allowed(context: ToolExecutionContext, permission: str) -> bool:
        return permission in context.permissions

    def list_accounts(self, _: ListAccountsInput, context: ToolExecutionContext) -> dict[str, Any]:
        if not self._allowed(context, "finance:read"):
            return failed("permission_denied")
        try:
            rows = self.finance.list_accounts()
        except SQLAlchemyError:
            return failed("database_unavailable", retryable=True)
        return AccountsOutput(
            items=rows[:50], truncated=len(rows) > 50, as_of=context.received_at
        ).model_dump(mode="json")

    def list_categories(self, args: ListCategoriesInput, context: ToolExecutionContext) -> dict[str, Any]:
        if not self._allowed(context, "finance:read"):
            return failed("permission_denied")
        try:
            rows = self.finance.list_categories()
        except SQLAlchemyError:
            return failed("database_unavailable", retryable=True)
        if args.kind is not None:
            rows = [row for row in rows if row.kind == args.kind]
        return CategoriesOutput(
            items=rows[:50], truncated=len(rows) > 50, as_of=context.received_at
        ).model_dump(mode="json")

    def account_balance(self, args: GetAccountBalanceInput, context: ToolExecutionContext) -> dict[str, Any]:
        if not self._allowed(context, "finance:read"):
            return failed("permission_denied")
        try:
            as_of = args.as_of or context.received_at
            value = self.finance.account_balance(args.account_id, as_of=as_of)
            return AccountBalanceOutput(
                account_id=args.account_id, balance_minor=value, as_of=as_of.astimezone(UTC)
            ).model_dump(mode="json")
        except FinanceError as exc:
            return failed(exc.code, retryable=exc.retryable)
        except SQLAlchemyError:
            return failed("database_unavailable", retryable=True)

    def list_transactions(self, args: ListTransactionsInput, context: ToolExecutionContext) -> dict[str, Any]:
        if not self._allowed(context, "finance:read"):
            return failed("permission_denied")
        end = args.end or context.received_at
        start = args.start or (end - timedelta(days=31))
        if start >= end:
            return failed("validation_error")
        try:
            rows = self.finance.list_transactions(start=start, end=end)
        except SQLAlchemyError:
            return failed("database_unavailable", retryable=True)
        return TransactionsOutput(
            items=rows[: args.limit],
            truncated=len(rows) > args.limit,
            start=start.astimezone(UTC),
            end=end.astimezone(UTC),
            as_of=context.received_at.astimezone(UTC),
        ).model_dump(mode="json")

    def monthly_snapshot(self, args: GetMonthlySnapshotInput, context: ToolExecutionContext) -> dict[str, Any]:
        if not self._allowed(context, "finance:read"):
            return failed("permission_denied")
        try:
            snapshot = self.finance.monthly_snapshot(
                args.period,
                args.as_of or context.received_at,
                account_ids=args.account_ids,
                category_ids=args.category_ids,
            )
            return MonthlySnapshotOutput(snapshot=snapshot).model_dump(mode="json")
        except FinanceError as exc:
            return failed(exc.code, retryable=exc.retryable)
        except SQLAlchemyError:
            return failed("database_unavailable", retryable=True)

    def _resource_versions(self, args: RecordExpenseToolInput) -> tuple[dict[str, int], str | None, str | None]:
        versions: dict[str, int] = {}
        account_name: str | None = None
        category_name: str | None = None
        if args.account_id is not None:
            account = next((row for row in self.finance.list_accounts() if row.id == args.account_id), None)
            if account is None:
                raise FinanceError("not_found")
            versions[f"account:{account.id}"] = account.version_id
            account_name = account.name
        if args.category_id is not None:
            category = next(
                (row for row in self.finance.list_categories() if row.id == args.category_id and row.kind == "expense"),
                None,
            )
            if category is None:
                raise FinanceError("not_found")
            versions[f"category:{category.id}"] = category.version_id
            category_name = category.name
        return versions, account_name, category_name

    def record_expense(self, args: RecordExpenseToolInput, context: ToolExecutionContext) -> dict[str, Any]:
        if not self._allowed(context, "finance:write"):
            return failed("permission_denied")
        try:
            message = context.user_message or ""
            if len(re.findall(r"\d+(?:\.\d+)?\s*元", message)) > 1:
                return failed("multiple_expenses_unsupported")
            forced_missing: list[str] = []
            if any(
                marker in message
                for marker in ("计划", "准备", "打算", "合适吗", "合理吗", "预计", "如果")
            ):
                forced_missing.append("record_intent")
            if any(marker in message for marker in ("大概", "大约", "左右", "十几")):
                args = args.model_copy(update={"amount": None})
            if any(marker in message for marker in ("上周", "前几天", "最近")):
                args = args.model_copy(update={"occurred_at": None})
                forced_missing.append("occurred_at")
            missing = [
                name
                for name, value in (
                    ("amount", args.amount),
                    ("account_id", args.account_id),
                    ("category_id", args.category_id),
                )
                if value is None
            ]
            missing = list(dict.fromkeys(forced_missing + missing))
            amount_minor = None if args.amount is None else parse_minor(args.amount)
            versions, account_name, category_name = self._resource_versions(args)
            local_received = context.received_at.astimezone(ZoneInfo("Asia/Shanghai"))
            if "昨天" in message:
                occurred_at = local_received - timedelta(days=1)
            elif "今天" in message:
                occurred_at = local_received
            else:
                occurred_at = args.occurred_at or context.received_at
            action = {
                "amount": None if amount_minor is None else format_minor(amount_minor),
                "account_id": None if args.account_id is None else str(args.account_id),
                "category_id": None if args.category_id is None else str(args.category_id),
                "occurred_at": occurred_at.astimezone(UTC).isoformat(),
            }
            choices: list[dict[str, str]] = []
            if missing and missing[0] == "account_id":
                choices = [
                    {"id": str(row.id), "label": row.name}
                    for row in self.finance.list_accounts()[:5]
                ]
            elif missing and missing[0] == "category_id":
                choices = [
                    {"id": str(row.id), "label": row.name}
                    for row in self.finance.list_categories()
                    if row.kind == "expense"
                ][:5]
            pending = self.pending.create(
                run_id=context.agent_run_id,
                actor_id=context.actor_id,
                conversation_id=context.conversation_id,
                source_system=context.source_system,
                action_type="record_expense",
                action=action,
                missing_fields=missing,
                resource_versions=versions,
                now=context.received_at,
            )
            if missing:
                return NeedsInput(
                    pending_action_id=pending.id,
                    missing_fields=missing,
                    question_code=f"ask_{missing[0]}",
                    choices=choices,
                ).model_dump(mode="json")
            return NeedsConfirmation(
                pending_action_id=pending.id,
                confirmation_code=pending.confirmation_code,
                summary=self.summary(
                    pending,
                    account_name=account_name,
                    category_name=category_name,
                ),
            ).model_dump(mode="json")
        except FinanceError as exc:
            return failed(exc.code, retryable=exc.retryable)
        except PendingActionError as exc:
            return failed(exc.code, retryable=exc.retryable)
        except SQLAlchemyError:
            return failed("database_unavailable", retryable=True)

    @staticmethod
    def summary(
        pending: PendingAction,
        *,
        account_name: str | None = None,
        category_name: str | None = None,
    ) -> dict[str, str]:
        return {
            "operation": "record_expense",
            "amount": str(pending.action.get("amount") or ""),
            "currency": "CNY",
            "account": account_name or str(pending.action.get("account_id") or ""),
            "category": category_name or str(pending.action.get("category_id") or ""),
            "occurred_at": str(pending.action.get("occurred_at") or ""),
            "candidate": pending.confirmation_code,
        }

    def validate_versions(self, pending: PendingAction) -> None:
        try:
            args = RecordExpenseToolInput.model_validate(pending.action)
            versions, _, _ = self._resource_versions(args)
            if versions != pending.resource_versions:
                raise PendingActionError("pending_action_stale", retryable=True)
        except FinanceError as exc:
            raise PendingActionError("pending_action_stale", retryable=True) from exc

    def commit(self, pending: PendingAction) -> dict[str, Any]:
        try:
            args = RecordExpenseToolInput.model_validate(pending.action)
            if args.amount is None or args.account_id is None or args.category_id is None or args.occurred_at is None:
                return failed("missing_required_context")
            result = self.finance.record_expense(
                RecordExpense(
                    source_system=pending.source_system,
                    source_event_id=f"pending:{pending.id}:commit",
                    amount=args.amount,
                    account_id=args.account_id,
                    category_id=args.category_id,
                    occurred_at=args.occurred_at,
                )
            )
            return CommittedWrite(
                result_type=result.result_type,
                result_id=result.result_id,
                replayed=result.replayed,
                amount_minor=parse_minor(args.amount),
            ).model_dump(mode="json")
        except FinanceError as exc:
            return failed(exc.code, retryable=exc.retryable)
        except SQLAlchemyError:
            return failed("database_unavailable", retryable=True)
        except Exception:
            return failed("tool_error")


def finance_registry(adapter: FinanceToolAdapter) -> ToolRegistry:
    common = {"requires_context": True, "required_permission": "finance:read"}
    return ToolRegistry(
        [
            Tool("finance_list_accounts", "List active finance accounts.", ListAccountsInput, adapter.list_accounts, **common),
            Tool("finance_list_categories", "List active finance categories.", ListCategoriesInput, adapter.list_categories, **common),
            Tool("finance_get_account_balance", "Get an account balance at a bounded time.", GetAccountBalanceInput, adapter.account_balance, **common),
            Tool("finance_list_transactions", "List transactions in a bounded time range.", ListTransactionsInput, adapter.list_transactions, **common),
            Tool("finance_get_monthly_snapshot", "Get the deterministic monthly finance snapshot.", GetMonthlySnapshotInput, adapter.monthly_snapshot, **common),
            Tool(
                "finance_record_expense",
                "Create a single expense candidate that always requires server confirmation.",
                RecordExpenseToolInput,
                adapter.record_expense,
                requires_context=True,
                is_write=True,
                required_permission="finance:write",
            ),
        ]
    )
