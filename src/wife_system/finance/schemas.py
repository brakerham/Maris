from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator, model_validator

MoneyText = Annotated[StrictStr, Field(min_length=1, max_length=32)]
NameText = Annotated[StrictStr, Field(min_length=1, max_length=120)]
SourceText = Annotated[StrictStr, Field(min_length=1, max_length=128)]


class FinanceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WriteCommand(FinanceModel):
    source_system: Annotated[StrictStr, Field(min_length=1, max_length=80)]
    source_event_id: SourceText
    currency: Annotated[StrictStr, Field(min_length=3, max_length=3)] = "CNY"

    @field_validator("source_system", "source_event_id")
    @classmethod
    def source_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source identifiers cannot be blank")
        return value


class CreateAccount(WriteCommand):
    name: NameText


class CreateCategory(WriteCommand):
    kind: Literal["income", "expense"]
    name: NameText


class ArchiveResource(WriteCommand):
    resource_id: uuid.UUID
    expected_version: Annotated[int, Field(ge=1)]
    reason: Annotated[StrictStr, Field(min_length=1, max_length=240)]


class LedgerCommand(WriteCommand):
    amount: MoneyText
    occurred_at: datetime

    @field_validator("occurred_at")
    @classmethod
    def aware_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone")
        return value


class RecordOpeningBalance(LedgerCommand):
    account_id: uuid.UUID


class RecordIncome(LedgerCommand):
    account_id: uuid.UUID
    category_id: uuid.UUID


class RecordExpense(LedgerCommand):
    account_id: uuid.UUID
    category_id: uuid.UUID


class LedgerSplitInput(FinanceModel):
    category_id: uuid.UUID
    amount: MoneyText


class SplitLedgerCommand(WriteCommand):
    account_id: uuid.UUID
    occurred_at: datetime
    entries: Annotated[list[LedgerSplitInput], Field(min_length=2)]

    @field_validator("occurred_at")
    @classmethod
    def aware_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone")
        return value


class RecordSplitIncome(SplitLedgerCommand):
    pass


class RecordSplitExpense(SplitLedgerCommand):
    pass


class RecordTransfer(LedgerCommand):
    source_account_id: uuid.UUID
    destination_account_id: uuid.UUID

    @model_validator(mode="after")
    def distinct_accounts(self) -> "RecordTransfer":
        if self.source_account_id == self.destination_account_id:
            raise ValueError("source and destination must differ")
        return self


class RecordRefund(LedgerCommand):
    original_transaction_id: uuid.UUID
    destination_account_id: uuid.UUID


class RecordReversal(WriteCommand):
    original_transaction_id: uuid.UUID
    occurred_at: datetime
    reason: Annotated[StrictStr, Field(min_length=1, max_length=240)]

    @field_validator("occurred_at")
    @classmethod
    def aware_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone")
        return value


class CreateActivityTemplate(WriteCommand):
    name: NameText
    reference_amount: MoneyText | None = None


class ReviseActivityTemplate(WriteCommand):
    template_id: uuid.UUID
    expected_version: Annotated[int, Field(ge=1)]
    name: NameText
    reference_amount: MoneyText | None = None


class RecordActivityOccurrence(WriteCommand):
    template_id: uuid.UUID
    occurred_at: datetime

    @field_validator("occurred_at")
    @classmethod
    def aware_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone")
        return value


class CancelActivityOccurrence(WriteCommand):
    occurrence_id: uuid.UUID
    expected_version: Annotated[int, Field(ge=1)]
    reason: Annotated[StrictStr, Field(min_length=1, max_length=240)]


class AllocateActivityExpense(WriteCommand):
    occurrence_id: uuid.UUID
    expense_entry_id: uuid.UUID
    amount: MoneyText


class CreateIncomeSchedule(WriteCommand):
    amount: MoneyText
    effective_from: date
    effective_to: date | None = None
    due_day: Annotated[int, Field(ge=1, le=31)]

    @model_validator(mode="after")
    def valid_range(self) -> "CreateIncomeSchedule":
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to precedes effective_from")
        return self


class ReviseIncomeSchedule(CreateIncomeSchedule):
    schedule_id: uuid.UUID
    expected_version: Annotated[int, Field(ge=1)]


class GenerateIncomeExpectation(WriteCommand):
    schedule_id: uuid.UUID
    period: Annotated[StrictStr, Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]


class MatchIncomeExpectation(WriteCommand):
    expectation_id: uuid.UUID
    income_entry_id: uuid.UUID
    amount: MoneyText


class CreateBudgetPlan(WriteCommand):
    name: NameText


class BudgetAllocationInput(FinanceModel):
    category_id: uuid.UUID
    limit: MoneyText


class PublishBudgetVersion(WriteCommand):
    plan_id: uuid.UUID
    expected_version: Annotated[int, Field(ge=1)]
    period: Annotated[StrictStr, Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]
    allocations: Annotated[list[BudgetAllocationInput], Field(min_length=1)]
    adjustment_reason: Annotated[StrictStr, Field(min_length=1, max_length=240)] | None = None
    published_at: datetime

    @field_validator("published_at")
    @classmethod
    def aware_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("published_at must include a timezone")
        return value


class CommandResult(FinanceModel):
    result_type: str
    result_id: uuid.UUID
    replayed: bool = False
    version_id: int | None = None


class AccountView(FinanceModel):
    id: uuid.UUID
    name: str
    currency: Literal["CNY"]
    version_id: int
    archived_at: datetime | None
    created_at: datetime


class CategoryView(FinanceModel):
    id: uuid.UUID
    kind: Literal["income", "expense"]
    name: str
    version_id: int
    archived_at: datetime | None
    created_at: datetime


class TransactionEntryView(FinanceModel):
    id: uuid.UUID
    line_no: int
    entry_role: Literal["account", "expense", "income", "opening_equity"]
    amount_minor: int
    account_id: uuid.UUID | None
    category_id: uuid.UUID | None


class TransactionView(FinanceModel):
    id: uuid.UUID
    kind: Literal["opening_balance", "income", "expense", "transfer", "refund", "reversal"]
    occurred_at: datetime
    currency: Literal["CNY"]
    related_transaction_id: uuid.UUID | None
    relation_kind: str | None
    entries: list[TransactionEntryView]


class BudgetAllocationView(FinanceModel):
    category_id: uuid.UUID
    limit_minor: int


class BudgetVersionView(FinanceModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    period: date
    version_no: int
    adjustment_reason: str | None
    published_at: datetime
    allocations: list[BudgetAllocationView]


class CategorySnapshot(FinanceModel):
    category_id: uuid.UUID
    gross_expense_minor: int
    refund_minor: int
    net_expense_minor: int
    limit_minor: int | None
    remaining_minor: int | None


class AccountSnapshot(FinanceModel):
    account_id: uuid.UUID
    opening_balance_minor: int
    inflow_minor: int
    outflow_minor: int
    closing_balance_minor: int


class MonthlySnapshot(FinanceModel):
    period: str
    as_of: datetime
    currency: Literal["CNY"] = "CNY"
    budget_version_id: uuid.UUID | None
    income_minor: int
    gross_expense_minor: int
    refund_minor: int
    net_expense_minor: int
    transfer_in_minor: int
    transfer_out_minor: int
    expected_income_minor: int
    received_against_expectation_minor: int
    categories: list[CategorySnapshot]
    accounts: list[AccountSnapshot]
