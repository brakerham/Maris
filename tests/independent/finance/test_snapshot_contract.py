from __future__ import annotations

import json
from datetime import date, datetime

import pytest
from sqlalchemy import select

from wife_system.finance.models import TransactionEntry
from wife_system.finance.schemas import (
    AllocateActivityExpense,
    BudgetAllocationInput,
    CreateActivityTemplate,
    CreateBudgetPlan,
    CreateIncomeSchedule,
    GenerateIncomeExpectation,
    PublishBudgetVersion,
    RecordActivityOccurrence,
    RecordExpense,
    RecordIncome,
    RecordOpeningBalance,
    RecordRefund,
    RecordTransfer,
)

from conftest import TZ


@pytest.mark.c3("SNP-01", "SNP-02", "SNP-03", "SNP-04", "SNP-05")
def test_monthly_snapshot_reconciles_income_expense_transfer_refund_categories_and_accounts(
    service, virtual
) -> None:
    wallet = virtual.account("虚拟钱包")
    bank = virtual.account("虚拟银行卡")
    income_category = virtual.category("income", "虚拟收入")
    food = virtual.category("expense", "虚拟餐食")
    fixed = virtual.category("expense", "虚拟固定支出")
    service.record_opening_balance(
        RecordOpeningBalance(
            **virtual.source(),
            account_id=wallet,
            amount="500.00",
            occurred_at=datetime(2026, 2, 28, 12, tzinfo=TZ),
        )
    )
    service.record_income(
        RecordIncome(
            **virtual.source(),
            account_id=bank,
            category_id=income_category,
            amount="1500.00",
            occurred_at=datetime(2026, 3, 1, 9, tzinfo=TZ),
        )
    )
    food_expense = service.record_expense(
        RecordExpense(
            **virtual.source(),
            account_id=wallet,
            category_id=food,
            amount="18.00",
            occurred_at=datetime(2026, 3, 5, 12, tzinfo=TZ),
        )
    )
    service.record_expense(
        RecordExpense(
            **virtual.source(),
            account_id=bank,
            category_id=fixed,
            amount="30.00",
            occurred_at=datetime(2026, 3, 6, 12, tzinfo=TZ),
        )
    )
    service.record_transfer(
        RecordTransfer(
            **virtual.source(),
            source_account_id=wallet,
            destination_account_id=bank,
            amount="100.00",
            occurred_at=datetime(2026, 3, 7, 12, tzinfo=TZ),
        )
    )
    service.record_refund(
        RecordRefund(
            **virtual.source(),
            original_transaction_id=food_expense.result_id,
            destination_account_id=wallet,
            amount="6.00",
            occurred_at=datetime(2026, 3, 8, 12, tzinfo=TZ),
        )
    )
    plan = service.create_budget_plan(CreateBudgetPlan(**virtual.source(), name="虚拟三月预算"))
    budget = service.publish_budget_version(
        PublishBudgetVersion(
            **virtual.source(),
            plan_id=plan.result_id,
            expected_version=1,
            period="2026-03",
            allocations=[
                BudgetAllocationInput(category_id=food, limit="60.00"),
                BudgetAllocationInput(category_id=fixed, limit="100.00"),
            ],
            published_at=datetime(2026, 3, 1, tzinfo=TZ),
        )
    )

    snapshot = service.monthly_snapshot("2026-03", datetime(2026, 10, 1, tzinfo=TZ))
    assert snapshot.budget_version_id == budget.result_id
    assert (
        snapshot.income_minor,
        snapshot.gross_expense_minor,
        snapshot.refund_minor,
        snapshot.net_expense_minor,
    ) == (150_000, 4_800, 600, 4_200)
    assert (snapshot.transfer_in_minor, snapshot.transfer_out_minor) == (10_000, 10_000)
    categories = {row.category_id: row for row in snapshot.categories}
    assert (
        categories[food].gross_expense_minor,
        categories[food].refund_minor,
        categories[food].net_expense_minor,
        categories[food].remaining_minor,
    ) == (1800, 600, 1200, 4800)
    assert (
        categories[fixed].gross_expense_minor,
        categories[fixed].refund_minor,
        categories[fixed].net_expense_minor,
        categories[fixed].remaining_minor,
    ) == (3000, 0, 3000, 7000)
    accounts = {row.account_id: row for row in snapshot.accounts}
    assert (
        accounts[wallet].opening_balance_minor,
        accounts[wallet].inflow_minor,
        accounts[wallet].outflow_minor,
        accounts[wallet].closing_balance_minor,
    ) == (50_000, 600, 11_800, 38_800)
    assert (
        accounts[bank].opening_balance_minor,
        accounts[bank].inflow_minor,
        accounts[bank].outflow_minor,
        accounts[bank].closing_balance_minor,
    ) == (0, 160_000, 3_000, 157_000)
    assert sum(row.closing_balance_minor for row in snapshot.accounts) == 195_800


@pytest.mark.c3("SNP-07", "ACT-01", "INC-01")
def test_templates_and_expectations_only_affect_prediction_fields(service, virtual) -> None:
    template = service.create_activity_template(
        CreateActivityTemplate(**virtual.source(), name="虚拟预测活动", reference_amount="88.00")
    )
    service.record_activity_occurrence(
        RecordActivityOccurrence(
            **virtual.source(),
            template_id=template.result_id,
            occurred_at=datetime(2026, 3, 10, tzinfo=TZ),
        )
    )
    schedule = service.create_income_schedule(
        CreateIncomeSchedule(
            **virtual.source(), amount="1200.00", effective_from=date(2026, 3, 1), due_day=15
        )
    )
    service.generate_income_expectation(
        GenerateIncomeExpectation(
            **virtual.source(), schedule_id=schedule.result_id, period="2026-03"
        )
    )
    snapshot = service.monthly_snapshot("2026-03", datetime(2026, 10, 1, tzinfo=TZ))
    assert snapshot.expected_income_minor == 120_000
    assert snapshot.received_against_expectation_minor == 0
    assert snapshot.income_minor == 0
    assert snapshot.gross_expense_minor == 0
    assert snapshot.accounts == []
    assert service.list_transactions() == []


@pytest.mark.c3("SNP-08", "MIG-08")
def test_shanghai_month_boundary_and_cross_month_refund_are_assigned_to_occurrence_month(
    service, virtual
) -> None:
    account = virtual.account()
    category = virtual.category("expense", "虚拟跨月分类")
    march_expense = service.record_expense(
        RecordExpense(
            **virtual.source(),
            account_id=account,
            category_id=category,
            amount="18.00",
            occurred_at=datetime(2026, 3, 31, 23, 59, 59, tzinfo=TZ),
        )
    )
    service.record_expense(
        RecordExpense(
            **virtual.source(),
            account_id=account,
            category_id=category,
            amount="1.00",
            occurred_at=datetime(2026, 4, 1, 0, 0, 0, tzinfo=TZ),
        )
    )
    service.record_refund(
        RecordRefund(
            **virtual.source(),
            original_transaction_id=march_expense.result_id,
            destination_account_id=account,
            amount="6.00",
            occurred_at=datetime(2026, 4, 2, tzinfo=TZ),
        )
    )
    march = service.monthly_snapshot("2026-03", datetime(2026, 5, 1, tzinfo=TZ))
    april = service.monthly_snapshot("2026-04", datetime(2026, 5, 1, tzinfo=TZ))
    assert (march.gross_expense_minor, march.refund_minor, march.net_expense_minor) == (1800, 0, 1800)
    assert (april.gross_expense_minor, april.refund_minor, april.net_expense_minor) == (100, 600, -500)
    assert march.accounts[0].closing_balance_minor == -1800
    assert april.accounts[0].opening_balance_minor == -1800
    assert april.accounts[0].closing_balance_minor == -1300


@pytest.mark.c3("SNP-09", "ACT-03")
def test_snapshot_sorting_and_totals_are_stable_without_join_duplication(service, virtual) -> None:
    account = virtual.account()
    categories = [
        virtual.category("expense", "虚拟稳定分类乙"),
        virtual.category("expense", "虚拟稳定分类甲"),
    ]
    expenses = [
        service.record_expense(
            RecordExpense(
                **virtual.source(),
                account_id=account,
                category_id=category,
                amount="10.00",
                occurred_at=datetime(2026, 3, day, tzinfo=TZ),
            )
        )
        for category, day in zip(categories, (2, 1), strict=True)
    ]
    template = service.create_activity_template(CreateActivityTemplate(**virtual.source(), name="虚拟稳定活动"))
    occurrence = service.record_activity_occurrence(
        RecordActivityOccurrence(
            **virtual.source(), template_id=template.result_id, occurred_at=datetime(2026, 3, 3, tzinfo=TZ)
        )
    )
    with service._sessions() as session:
        entries = list(
            session.scalars(
                select(TransactionEntry.id).where(
                    TransactionEntry.transaction_id.in_([row.result_id for row in expenses]),
                    TransactionEntry.entry_role == "expense",
                )
            ).all()
        )
    for entry in entries:
        service.allocate_activity_expense(
            AllocateActivityExpense(
                **virtual.source(), occurrence_id=occurrence.result_id, expense_entry_id=entry, amount="5.00"
            )
        )
    snapshots = [
        service.monthly_snapshot("2026-03", datetime(2026, 4, 1, tzinfo=TZ)) for _ in range(3)
    ]
    serialized = [json.dumps(row.model_dump(mode="json"), sort_keys=True) for row in snapshots]
    assert len(set(serialized)) == 1
    assert snapshots[0].gross_expense_minor == 2000
    assert snapshots[0].net_expense_minor == 2000
    assert [row.category_id for row in snapshots[0].categories] == sorted(categories, key=str)
    assert [row.account_id for row in snapshots[0].accounts] == [account]
