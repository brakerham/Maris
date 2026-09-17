from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from wife_system.finance.schemas import (
    ArchiveResource,
    BudgetAllocationInput,
    CreateAccount,
    CreateBudgetPlan,
    CreateCategory,
    LedgerSplitInput,
    PublishBudgetVersion,
    RecordIncome,
    RecordRefund,
    RecordSplitExpense,
)

SHANGHAI = ZoneInfo("Asia/Shanghai")


def test_cumulative_refund_apportionment_converges_for_repeated_cents(service) -> None:
    account = service.create_account(CreateAccount(source_system="r1", source_event_id="account", name="虚拟退款账户")).result_id
    first = service.create_category(CreateCategory(source_system="r1", source_event_id="first", kind="expense", name="虚拟一分甲")).result_id
    second = service.create_category(CreateCategory(source_system="r1", source_event_id="second", kind="expense", name="虚拟一分乙")).result_id
    expense = service.record_split_expense(RecordSplitExpense(
        source_system="r1",
        source_event_id="expense",
        account_id=account,
        occurred_at=datetime(2026, 9, 15, tzinfo=SHANGHAI),
        entries=[
            LedgerSplitInput(category_id=first, amount="0.01"),
            LedgerSplitInput(category_id=second, amount="0.01"),
        ],
    ))
    for index in (1, 2):
        service.record_refund(RecordRefund(
            source_system="r1",
            source_event_id=f"refund-{index}",
            original_transaction_id=expense.result_id,
            destination_account_id=account,
            amount="0.01",
            occurred_at=datetime(2026, 9, 15 + index, tzinfo=SHANGHAI),
        ))
    snapshot = service.monthly_snapshot("2026-09", datetime(2026, 10, 1, tzinfo=SHANGHAI))
    categories = {row.category_id: row for row in snapshot.categories}
    assert categories[first].refund_minor == 1
    assert categories[second].refund_minor == 1
    assert categories[first].net_expense_minor == 0
    assert categories[second].net_expense_minor == 0


def test_cumulative_refund_apportionment_converges_across_multiple_partials(service) -> None:
    account = service.create_account(CreateAccount(source_system="r1-multi", source_event_id="account", name="虚拟多次退款账户")).result_id
    categories = [
        service.create_category(CreateCategory(source_system="r1-multi", source_event_id=f"category-{index}", kind="expense", name=f"虚拟多次分类{index}")).result_id
        for index in range(3)
    ]
    expense = service.record_split_expense(RecordSplitExpense(
        source_system="r1-multi",
        source_event_id="expense",
        account_id=account,
        occurred_at=datetime(2026, 9, 10, tzinfo=SHANGHAI),
        entries=[
            LedgerSplitInput(category_id=categories[0], amount="3.33"),
            LedgerSplitInput(category_id=categories[1], amount="2.22"),
            LedgerSplitInput(category_id=categories[2], amount="4.45"),
        ],
    ))
    for index, amount in enumerate(("1.01", "2.03", "6.96"), start=1):
        service.record_refund(RecordRefund(
            source_system="r1-multi",
            source_event_id=f"refund-{index}",
            original_transaction_id=expense.result_id,
            destination_account_id=account,
            amount=amount,
            occurred_at=datetime(2026, 9, 10 + index, tzinfo=SHANGHAI),
        ))
    snapshot = service.monthly_snapshot("2026-09", datetime(2026, 10, 1, tzinfo=SHANGHAI))
    by_category = {row.category_id: row for row in snapshot.categories}
    assert [by_category[category_id].refund_minor for category_id in categories] == [333, 222, 445]
    assert all(by_category[category_id].net_expense_minor == 0 for category_id in categories)


def test_public_query_timepoints_are_aware_utc_on_sqlite(service) -> None:
    occurred = datetime(2026, 9, 1, 0, 30, tzinfo=SHANGHAI)
    account = service.create_account(CreateAccount(source_system="r1-time", source_event_id="account", name="虚拟时区账户"))
    income_category = service.create_category(CreateCategory(source_system="r1-time", source_event_id="income", kind="income", name="虚拟时区收入"))
    expense_category = service.create_category(CreateCategory(source_system="r1-time", source_event_id="expense", kind="expense", name="虚拟时区支出"))
    transaction = service.record_income(RecordIncome(
        source_system="r1-time",
        source_event_id="transaction",
        account_id=account.result_id,
        category_id=income_category.result_id,
        amount="1.00",
        occurred_at=occurred,
    ))
    plan = service.create_budget_plan(CreateBudgetPlan(source_system="r1-time", source_event_id="plan", name="虚拟时区预算"))
    service.publish_budget_version(PublishBudgetVersion(
        source_system="r1-time",
        source_event_id="budget",
        plan_id=plan.result_id,
        expected_version=1,
        period="2026-09",
        allocations=[BudgetAllocationInput(category_id=expense_category.result_id, limit="1.00")],
        published_at=datetime(2026, 9, 1, 1, tzinfo=SHANGHAI),
    ))
    service.archive_account(ArchiveResource(source_system="r1-time", source_event_id="archive-account", resource_id=account.result_id, expected_version=1, reason="虚拟归档"))
    service.archive_category(ArchiveResource(source_system="r1-time", source_event_id="archive-category", resource_id=income_category.result_id, expected_version=1, reason="虚拟归档"))

    transaction_view = next(row for row in service.list_transactions() if row.id == transaction.result_id)
    assert transaction_view.occurred_at == datetime(2026, 8, 31, 16, 30, tzinfo=UTC)
    assert transaction_view.occurred_at.tzinfo is UTC
    account_view = next(row for row in service.list_accounts(include_archived=True) if row.id == account.result_id)
    category_view = next(row for row in service.list_categories(include_archived=True) if row.id == income_category.result_id)
    budget_view = service.list_budget_versions(plan.result_id, period="2026-09")[0]
    for value in (
        account_view.created_at,
        account_view.archived_at,
        category_view.created_at,
        category_view.archived_at,
        budget_view.published_at,
    ):
        assert value is not None
        assert value.tzinfo is UTC
