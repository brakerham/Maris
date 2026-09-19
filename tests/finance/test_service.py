from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from wife_system.finance.errors import FinanceError
from wife_system.finance.models import (
    ActivityTemplate,
    ActivityTemplateRevision,
    CommandReceipt,
    FinancialTransaction,
    IncomeExpectation,
    TransactionEntry,
)
from wife_system.finance.schemas import (
    AllocateActivityExpense,
    ArchiveResource,
    BudgetAllocationInput,
    CancelActivityOccurrence,
    CreateAccount,
    CreateActivityTemplate,
    CreateBudgetPlan,
    CreateCategory,
    CreateIncomeSchedule,
    GenerateIncomeExpectation,
    MatchIncomeExpectation,
    LedgerSplitInput,
    PublishBudgetVersion,
    RecordActivityOccurrence,
    RecordExpense,
    RecordIncome,
    RecordOpeningBalance,
    RecordRefund,
    RecordReversal,
    RecordSplitExpense,
    RecordTransfer,
    ReviseIncomeSchedule,
)

TZ = ZoneInfo("Asia/Shanghai")
WHEN = datetime(2026, 9, 5, 12, tzinfo=TZ)


class Fixture:
    def __init__(self, service):
        self.service = service
        self.n = 0

    def event(self) -> str:
        self.n += 1
        return f"virtual-{self.n}"

    def account(self, name: str = "虚拟账户"):
        return self.service.create_account(CreateAccount(source_system="test", source_event_id=self.event(), name=name)).result_id

    def category(self, kind: str, name: str):
        return self.service.create_category(CreateCategory(source_system="test", source_event_id=self.event(), kind=kind, name=name)).result_id


def test_vertical_ledger_snapshot_and_idempotency(service) -> None:
    fx = Fixture(service)
    wallet, bank = fx.account("虚拟钱包"), fx.account("虚拟银行卡")
    income_cat, food = fx.category("income", "虚拟收入"), fx.category("expense", "虚拟餐食")
    service.record_opening_balance(RecordOpeningBalance(source_system="test", source_event_id=fx.event(), account_id=wallet, amount="500.00", occurred_at=WHEN))
    income = service.record_income(RecordIncome(source_system="test", source_event_id="same-income", account_id=bank, category_id=income_cat, amount="1500.00", occurred_at=WHEN))
    replay = service.record_income(RecordIncome(source_system="test", source_event_id="same-income", account_id=bank, category_id=income_cat, amount="1500.0", occurred_at=WHEN))
    assert replay.result_id == income.result_id and replay.replayed
    expense = service.record_expense(RecordExpense(source_system="test", source_event_id=fx.event(), account_id=wallet, category_id=food, amount="18.00", occurred_at=WHEN))
    service.record_transfer(RecordTransfer(source_system="test", source_event_id=fx.event(), source_account_id=wallet, destination_account_id=bank, amount="100.00", occurred_at=WHEN))
    service.record_refund(RecordRefund(source_system="test", source_event_id=fx.event(), original_transaction_id=expense.result_id, destination_account_id=wallet, amount="6.00", occurred_at=WHEN))
    snapshot = service.monthly_snapshot("2026-09", datetime(2026, 10, 1, tzinfo=TZ))
    assert (snapshot.income_minor, snapshot.gross_expense_minor, snapshot.refund_minor, snapshot.net_expense_minor) == (150000, 1800, 600, 1200)
    assert (snapshot.transfer_in_minor, snapshot.transfer_out_minor) == (10000, 10000)
    assert service.account_balance(wallet) == 38800
    assert service.account_balance(bank) == 160000
    account_names = [row.name for row in service.list_accounts()]
    assert set(account_names) == {"虚拟银行卡", "虚拟钱包"}
    assert account_names == [row.name for row in service.list_accounts()]
    transactions = service.list_transactions()
    assert all(len(row.entries) >= 2 for row in transactions)
    assert [row.occurred_at for row in transactions] == sorted(row.occurred_at for row in transactions)


def test_same_key_different_payload_conflicts_without_side_effect(service) -> None:
    fx = Fixture(service)
    account = fx.account()
    category = fx.category("expense", "虚拟分类")
    command = RecordExpense(source_system="test", source_event_id="conflict", account_id=account, category_id=category, amount="1.00", occurred_at=WHEN)
    service.record_expense(command)
    with pytest.raises(FinanceError) as raised:
        service.record_expense(command.model_copy(update={"amount": "2.00"}))
    assert raised.value.code == "duplicate_request_conflict"
    assert service.account_balance(account) == -100
    with service._sessions() as session:
        receipt = session.scalar(select(CommandReceipt).where(CommandReceipt.command_name == "record_expense"))
        stored = "|".join([receipt.key_digest, receipt.request_fingerprint, receipt.result_json or ""])
        assert "conflict" not in stored


def test_float_is_rejected_at_dto_boundary() -> None:
    with pytest.raises(ValidationError):
        RecordExpense(source_system="test", source_event_id="float", account_id=uuid.uuid4(), category_id=uuid.uuid4(), amount=1.1, occurred_at=WHEN)  # type: ignore[arg-type]


def test_non_cny_has_stable_error(service) -> None:
    command = CreateAccount(source_system="test", source_event_id="currency", name="虚拟账户", currency="USD")
    with pytest.raises(FinanceError) as raised:
        service.create_account(command)
    assert raised.value.code == "unsupported_currency"


def test_archived_resource_and_version_conflict(service) -> None:
    fx = Fixture(service)
    account = fx.account()
    service.archive_account(ArchiveResource(source_system="test", source_event_id=fx.event(), resource_id=account, expected_version=1, reason="虚拟归档"))
    with pytest.raises(FinanceError) as raised:
        service.record_opening_balance(RecordOpeningBalance(source_system="test", source_event_id=fx.event(), account_id=account, amount="1.00", occurred_at=WHEN))
    assert raised.value.code == "archived_resource"
    with pytest.raises(FinanceError) as raised:
        service.archive_account(ArchiveResource(source_system="test", source_event_id=fx.event(), resource_id=account, expected_version=1, reason="再次归档"))
    assert raised.value.code == "concurrent_modification"


def test_refund_limit_and_reversal(service) -> None:
    fx = Fixture(service)
    account = fx.account()
    category = fx.category("expense", "虚拟餐食")
    expense = service.record_expense(RecordExpense(source_system="test", source_event_id=fx.event(), account_id=account, category_id=category, amount="10.00", occurred_at=WHEN))
    service.record_refund(RecordRefund(source_system="test", source_event_id=fx.event(), original_transaction_id=expense.result_id, destination_account_id=account, amount="4.00", occurred_at=WHEN))
    with pytest.raises(FinanceError) as raised:
        service.record_refund(RecordRefund(source_system="test", source_event_id=fx.event(), original_transaction_id=expense.result_id, destination_account_id=account, amount="7.00", occurred_at=WHEN))
    assert raised.value.code == "refund_exceeds_original"
    reversal = service.record_reversal(RecordReversal(source_system="test", source_event_id=fx.event(), original_transaction_id=expense.result_id, occurred_at=WHEN, reason="虚拟纠错"))
    assert reversal.result_type == "financial_transaction"


def test_split_expense_refund_preserves_category_proportions(service) -> None:
    fx = Fixture(service)
    account = fx.account()
    food = fx.category("expense", "虚拟餐食")
    travel = fx.category("expense", "虚拟交通")
    expense = service.record_split_expense(RecordSplitExpense(
        source_system="test",
        source_event_id=fx.event(),
        account_id=account,
        occurred_at=WHEN,
        entries=[
            LedgerSplitInput(category_id=food, amount="7.00"),
            LedgerSplitInput(category_id=travel, amount="3.00"),
        ],
    ))
    service.record_refund(RecordRefund(source_system="test", source_event_id=fx.event(), original_transaction_id=expense.result_id, destination_account_id=account, amount="5.00", occurred_at=WHEN))
    snapshot = service.monthly_snapshot("2026-09", datetime(2026, 10, 1, tzinfo=TZ))
    by_id = {row.category_id: row for row in snapshot.categories}
    assert (by_id[food].refund_minor, by_id[travel].refund_minor) == (350, 150)


def test_activity_allocation_and_cancellation(service) -> None:
    fx = Fixture(service)
    account = fx.account(); category = fx.category("expense", "虚拟活动")
    expense = service.record_expense(RecordExpense(source_system="test", source_event_id=fx.event(), account_id=account, category_id=category, amount="20.00", occurred_at=WHEN))
    with service._sessions() as session:
        entry_id = session.scalar(select(TransactionEntry.id).where(TransactionEntry.transaction_id == expense.result_id, TransactionEntry.entry_role == "expense"))
    template = service.create_activity_template(CreateActivityTemplate(source_system="test", source_event_id=fx.event(), name="虚拟跑步", reference_amount="20.00"))
    with service._sessions() as session:
        template_row = session.get(ActivityTemplate, template.result_id)
        revision = session.get(ActivityTemplateRevision, template_row.current_revision_id)
        assert template_row.name_normalized == "虚拟跑步"
        assert (revision.reference_minor, revision.reference_min_minor, revision.reference_max_minor) == (2000, 2000, 2000)
    occurrence = service.record_activity_occurrence(RecordActivityOccurrence(source_system="test", source_event_id=fx.event(), template_id=template.result_id, occurred_at=WHEN))
    service.allocate_activity_expense(AllocateActivityExpense(source_system="test", source_event_id=fx.event(), occurrence_id=occurrence.result_id, expense_entry_id=entry_id, amount="12.00"))
    with pytest.raises(FinanceError) as raised:
        service.allocate_activity_expense(AllocateActivityExpense(source_system="test", source_event_id=fx.event(), occurrence_id=occurrence.result_id, expense_entry_id=entry_id, amount="9.00"))
    assert raised.value.code == "allocation_exceeds_expense"
    cancelled = service.cancel_activity_occurrence(CancelActivityOccurrence(source_system="test", source_event_id=fx.event(), occurrence_id=occurrence.result_id, expected_version=1, reason="虚拟取消"))
    assert cancelled.version_id == 2


def test_income_schedule_history_and_matching(service) -> None:
    fx = Fixture(service)
    account = fx.account(); category = fx.category("income", "虚拟实习")
    schedule = service.create_income_schedule(CreateIncomeSchedule(source_system="test", source_event_id=fx.event(), amount="1000.00", effective_from="2026-09-01", due_day=30))
    expectation = service.generate_income_expectation(GenerateIncomeExpectation(source_system="test", source_event_id=fx.event(), schedule_id=schedule.result_id, period="2026-09"))
    income = service.record_income(RecordIncome(source_system="test", source_event_id=fx.event(), account_id=account, category_id=category, amount="1000.00", occurred_at=WHEN))
    with service._sessions() as session:
        entry_id = session.scalar(select(TransactionEntry.id).where(TransactionEntry.transaction_id == income.result_id, TransactionEntry.entry_role == "income"))
    service.match_income_expectation(MatchIncomeExpectation(source_system="test", source_event_id=fx.event(), expectation_id=expectation.result_id, income_entry_id=entry_id, amount="1000.00"))
    revised = service.revise_income_schedule(ReviseIncomeSchedule(source_system="test", source_event_id=fx.event(), schedule_id=schedule.result_id, expected_version=1, amount="1200.00", effective_from="2026-10-01", due_day=31))
    assert revised.version_id == 2
    snapshot = service.monthly_snapshot("2026-09", datetime(2026, 10, 1, tzinfo=TZ))
    assert snapshot.expected_income_minor == 100000
    assert snapshot.received_against_expectation_minor == 100000
    assert snapshot.income_minor == 100000


def test_budget_versions_and_snapshot(service) -> None:
    fx = Fixture(service)
    food = fx.category("expense", "虚拟餐食")
    plan = service.create_budget_plan(CreateBudgetPlan(source_system="test", source_event_id=fx.event(), name="虚拟预算"))
    first = service.publish_budget_version(PublishBudgetVersion(source_system="test", source_event_id=fx.event(), plan_id=plan.result_id, expected_version=1, period="2026-09", allocations=[BudgetAllocationInput(category_id=food, limit="500.00")], published_at=datetime(2026, 9, 1, tzinfo=TZ)))
    second = service.publish_budget_version(PublishBudgetVersion(source_system="test", source_event_id=fx.event(), plan_id=plan.result_id, expected_version=2, period="2026-09", allocations=[BudgetAllocationInput(category_id=food, limit="450.00")], adjustment_reason="虚拟调整", published_at=datetime(2026, 9, 10, tzinfo=TZ)))
    assert (first.version_id, second.version_id) == (2, 3)
    snapshot = service.monthly_snapshot("2026-09", datetime(2026, 9, 15, tzinfo=TZ))
    assert snapshot.budget_version_id == second.result_id
    assert snapshot.categories[0].limit_minor == 45000
    history = service.list_budget_versions(plan.result_id, period="2026-09")
    assert [row.version_no for row in history] == [1, 2]


def test_failed_business_command_rolls_back_receipt(service) -> None:
    fx = Fixture(service)
    account = fx.account()
    bad = RecordExpense(source_system="test", source_event_id="will-fail", account_id=account, category_id=uuid.uuid4(), amount="1.00", occurred_at=WHEN)
    with pytest.raises(FinanceError):
        service.record_expense(bad)
    with service._sessions() as session:
        assert session.scalar(select(func.count()).select_from(CommandReceipt).where(CommandReceipt.source_system == "test", CommandReceipt.command_name == "record_expense")) == 0
        assert session.scalar(select(func.count()).select_from(FinancialTransaction)) == 0


def test_database_failure_is_retryable_and_log_is_private(service, caplog) -> None:
    service._sessions.kw["bind"].dispose()
    with caplog.at_level(logging.ERROR, logger="wife_system.finance"):
        with pytest.raises(FinanceError) as raised:
            service.create_account(CreateAccount(
                source_system="test",
                source_event_id="PRIVATE_PAYLOAD_CANARY",
                name="虚拟敏感标记",
            ))
    assert raised.value.code == "database_unavailable"
    assert raised.value.retryable
    assert "PRIVATE_PAYLOAD_CANARY" not in caplog.text
    event = json.loads(caplog.records[-1].message)
    assert set(event) == {"event", "code", "command", "correlation_id"}
