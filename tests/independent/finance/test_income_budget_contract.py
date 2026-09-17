from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from threading import Barrier

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from wife_system.finance.errors import FinanceError
from wife_system.finance.models import (
    BudgetAllocation,
    BudgetVersion,
    FinancialTransaction,
    IncomeExpectation,
    IncomeExpectationMatch,
    IncomeScheduleVersion,
    TransactionEntry,
)
from wife_system.finance.schemas import (
    BudgetAllocationInput,
    CreateBudgetPlan,
    CreateIncomeSchedule,
    GenerateIncomeExpectation,
    MatchIncomeExpectation,
    PublishBudgetVersion,
    RecordIncome,
    ReviseIncomeSchedule,
)

from conftest import TZ, WHEN


def _income_entry(service, transaction_id: uuid.UUID) -> uuid.UUID:
    with service._sessions() as session:
        value = session.scalar(
            select(TransactionEntry.id).where(
                TransactionEntry.transaction_id == transaction_id,
                TransactionEntry.entry_role == "income",
            )
        )
    assert value is not None
    return value


@pytest.mark.c3("INC-01", "SNP-07")
def test_income_schedule_and_expectation_do_not_change_cash_or_actual_income(service, virtual) -> None:
    schedule = service.create_income_schedule(
        CreateIncomeSchedule(
            **virtual.source(), amount="1200.00", effective_from=date(2026, 9, 1), due_day=30
        )
    )
    service.generate_income_expectation(
        GenerateIncomeExpectation(
            **virtual.source(), schedule_id=schedule.result_id, period="2026-09"
        )
    )
    snapshot = service.monthly_snapshot("2026-09", datetime(2026, 10, 1, tzinfo=TZ))
    assert snapshot.expected_income_minor == 120_000
    assert snapshot.received_against_expectation_minor == 0
    assert snapshot.income_minor == 0
    assert not service.list_transactions()


@pytest.mark.c3("INC-02", "INC-03")
def test_actual_income_is_separate_and_future_schedule_version_preserves_history(service, virtual) -> None:
    account = virtual.account()
    category = virtual.category("income", "虚拟实习收入")
    schedule = service.create_income_schedule(
        CreateIncomeSchedule(
            **virtual.source(), amount="1200.00", effective_from=date(2026, 4, 1), due_day=10
        )
    )
    april_expectation = service.generate_income_expectation(
        GenerateIncomeExpectation(
            **virtual.source(), schedule_id=schedule.result_id, period="2026-04"
        )
    )
    income = service.record_income(
        RecordIncome(
            **virtual.source(),
            account_id=account,
            category_id=category,
            amount="1200.00",
            occurred_at=datetime(2026, 4, 10, tzinfo=TZ),
        )
    )
    service.match_income_expectation(
        MatchIncomeExpectation(
            **virtual.source(),
            expectation_id=april_expectation.result_id,
            income_entry_id=_income_entry(service, income.result_id),
            amount="1200.00",
        )
    )
    evidence_as_of = datetime(2026, 10, 1, tzinfo=TZ)
    before = service.monthly_snapshot("2026-04", evidence_as_of)
    service.revise_income_schedule(
        ReviseIncomeSchedule(
            **virtual.source(),
            schedule_id=schedule.result_id,
            expected_version=1,
            amount="1500.00",
            effective_from=date(2026, 6, 1),
            due_day=15,
        )
    )
    after = service.monthly_snapshot("2026-04", evidence_as_of)
    june = service.generate_income_expectation(
        GenerateIncomeExpectation(
            **virtual.source(), schedule_id=schedule.result_id, period="2026-06"
        )
    )
    assert before.model_dump(exclude={"as_of"}) == after.model_dump(exclude={"as_of"})
    assert (after.income_minor, after.expected_income_minor, after.received_against_expectation_minor) == (
        120_000,
        120_000,
        120_000,
    )
    with service._sessions() as session:
        generated = session.get(IncomeExpectation, june.result_id)
        assert generated is not None
        assert generated.expected_minor == 150_000


@pytest.mark.c3("INC-04", "INC-06")
def test_income_schedule_rejects_invalid_range_day_and_amount_without_rows(service, virtual) -> None:
    invalid_payloads = [
        {"amount": "0", "effective_from": date(2026, 9, 1), "due_day": 1},
        {"amount": "-1.00", "effective_from": date(2026, 9, 1), "due_day": 1},
        {"amount": "10000000000.00", "effective_from": date(2026, 9, 1), "due_day": 1},
    ]
    for payload in invalid_payloads:
        with pytest.raises(FinanceError):
            service.create_income_schedule(CreateIncomeSchedule(**virtual.source(), **payload))

    with pytest.raises(ValidationError):
        CreateIncomeSchedule(
            **virtual.source(),
            amount="1.00",
            effective_from=date(2026, 9, 2),
            effective_to=date(2026, 9, 1),
            due_day=1,
        )
    with pytest.raises(ValidationError):
        CreateIncomeSchedule(
            **virtual.source(), amount="1.00", effective_from=date(2026, 9, 1), due_day=32
        )
    with service._sessions() as session:
        assert session.scalar(select(func.count()).select_from(IncomeScheduleVersion)) == 0


@pytest.mark.c3("INC-01", "INC-04")
def test_month_end_due_day_clamps_and_duplicate_generation_is_rejected(service, virtual) -> None:
    schedule = service.create_income_schedule(
        CreateIncomeSchedule(
            **virtual.source(), amount="1.00", effective_from=date(2026, 1, 1), due_day=31
        )
    )
    expectation = service.generate_income_expectation(
        GenerateIncomeExpectation(
            **virtual.source(), schedule_id=schedule.result_id, period="2026-02"
        )
    )
    with service._sessions() as session:
        row = session.get(IncomeExpectation, expectation.result_id)
        assert row is not None
        assert row.due_date == date(2026, 2, 28)
    with pytest.raises(FinanceError) as raised:
        service.generate_income_expectation(
            GenerateIncomeExpectation(
                **virtual.source(), schedule_id=schedule.result_id, period="2026-02"
            )
        )
    assert raised.value.code == "validation_error"


@pytest.mark.c3("INC-02", "ERR-04")
def test_expectation_supports_multiple_income_entries_and_enforces_both_caps(service, virtual) -> None:
    account = virtual.account()
    category = virtual.category("income", "虚拟分批到账")
    schedule = service.create_income_schedule(
        CreateIncomeSchedule(
            **virtual.source(), amount="10.00", effective_from=date(2026, 9, 1), due_day=15
        )
    )
    expectation = service.generate_income_expectation(
        GenerateIncomeExpectation(
            **virtual.source(), schedule_id=schedule.result_id, period="2026-09"
        )
    )
    incomes = [
        service.record_income(
            RecordIncome(
                **virtual.source(),
                account_id=account,
                category_id=category,
                amount=amount,
                occurred_at=WHEN,
            )
        )
        for amount in ("4.00", "6.00", "1.00")
    ]
    service.match_income_expectation(
        MatchIncomeExpectation(
            **virtual.source(),
            expectation_id=expectation.result_id,
            income_entry_id=_income_entry(service, incomes[0].result_id),
            amount="4.00",
        )
    )
    service.match_income_expectation(
        MatchIncomeExpectation(
            **virtual.source(),
            expectation_id=expectation.result_id,
            income_entry_id=_income_entry(service, incomes[1].result_id),
            amount="6.00",
        )
    )
    with service._sessions() as session:
        row = session.get(IncomeExpectation, expectation.result_id)
        assert row is not None and row.status == "matched"
        assert session.scalar(
            select(func.sum(IncomeExpectationMatch.matched_minor)).where(
                IncomeExpectationMatch.expectation_id == expectation.result_id
            )
        ) == 1000
    with pytest.raises(FinanceError) as raised:
        service.match_income_expectation(
            MatchIncomeExpectation(
                **virtual.source(),
                expectation_id=expectation.result_id,
                income_entry_id=_income_entry(service, incomes[2].result_id),
                amount="0.01",
            )
        )
    assert raised.value.code == "expectation_match_exceeds_amount"


@pytest.mark.c3("BUD-01", "BUD-05", "BUD-06", "SNP-06")
def test_budget_versions_are_immutable_traceable_and_selected_by_as_of(service, virtual) -> None:
    food = virtual.category("expense", "虚拟餐食预算")
    travel = virtual.category("expense", "虚拟交通预算")
    plan = service.create_budget_plan(CreateBudgetPlan(**virtual.source(), name="虚拟月度预算"))
    first = service.publish_budget_version(
        PublishBudgetVersion(
            **virtual.source(),
            plan_id=plan.result_id,
            expected_version=1,
            period="2026-09",
            allocations=[
                BudgetAllocationInput(category_id=food, limit="600.00"),
                BudgetAllocationInput(category_id=travel, limit="200.00"),
            ],
            published_at=datetime(2026, 9, 1, tzinfo=TZ),
        )
    )
    with pytest.raises(FinanceError) as raised:
        service.publish_budget_version(
            PublishBudgetVersion(
                **virtual.source(),
                plan_id=plan.result_id,
                expected_version=2,
                period="2026-09",
                allocations=[BudgetAllocationInput(category_id=food, limit="550.00")],
                adjustment_reason="   ",
                published_at=datetime(2026, 9, 10, tzinfo=TZ),
            )
        )
    assert raised.value.code == "validation_error"

    second = service.publish_budget_version(
        PublishBudgetVersion(
            **virtual.source(),
            plan_id=plan.result_id,
            expected_version=2,
            period="2026-09",
            allocations=[
                BudgetAllocationInput(category_id=food, limit="550.00"),
                BudgetAllocationInput(category_id=travel, limit="250.00"),
            ],
            adjustment_reason="虚拟月中调整",
            published_at=datetime(2026, 9, 10, tzinfo=TZ),
        )
    )
    versions = service.list_budget_versions(plan.result_id, period="2026-09")
    assert [row.version_no for row in versions] == [1, 2]
    assert versions[0].id == first.result_id and versions[1].id == second.result_id
    assert versions[0].allocations[0].limit_minor in {20_000, 60_000}
    early = service.monthly_snapshot("2026-09", datetime(2026, 9, 5, tzinfo=TZ))
    late = service.monthly_snapshot("2026-09", datetime(2026, 9, 15, tzinfo=TZ))
    assert early.budget_version_id == first.result_id
    assert late.budget_version_id == second.result_id


@pytest.mark.c3("BUD-02", "BUD-03", "BUD-04", "ERR-02")
def test_budget_rejects_duplicate_missing_wrong_kind_and_closed_period_atomically(service, virtual) -> None:
    expense = virtual.category("expense", "虚拟预算支出")
    income = virtual.category("income", "虚拟预算收入")
    plan = service.create_budget_plan(CreateBudgetPlan(**virtual.source(), name="虚拟预算约束"))
    cases = [
        (
            [
                BudgetAllocationInput(category_id=expense, limit="1.00"),
                BudgetAllocationInput(category_id=expense, limit="2.00"),
            ],
            "validation_error",
        ),
        ([BudgetAllocationInput(category_id=uuid.uuid4(), limit="1.00")], "not_found"),
        ([BudgetAllocationInput(category_id=income, limit="1.00")], "validation_error"),
    ]
    for allocations, code in cases:
        with pytest.raises(FinanceError) as raised:
            service.publish_budget_version(
                PublishBudgetVersion(
                    **virtual.source(),
                    plan_id=plan.result_id,
                    expected_version=1,
                    period="2026-09",
                    allocations=allocations,
                    published_at=WHEN,
                )
            )
        assert raised.value.code == code
    with pytest.raises(FinanceError) as raised:
        service.publish_budget_version(
            PublishBudgetVersion(
                **virtual.source(),
                plan_id=plan.result_id,
                expected_version=1,
                period="2026-08",
                allocations=[BudgetAllocationInput(category_id=expense, limit="1.00")],
                published_at=WHEN,
            )
        )
    assert raised.value.code == "budget_period_closed"
    with service._sessions() as session:
        assert session.scalar(select(func.count()).select_from(BudgetVersion)) == 0
        assert session.scalar(select(func.count()).select_from(BudgetAllocation)) == 0


@pytest.mark.c3("BUD-05", "ERR-04")
def test_budget_expected_version_conflict_preserves_existing_chain(service, virtual) -> None:
    category = virtual.category("expense", "虚拟版本分类")
    plan = service.create_budget_plan(CreateBudgetPlan(**virtual.source(), name="虚拟版本预算"))
    service.publish_budget_version(
        PublishBudgetVersion(
            **virtual.source(),
            plan_id=plan.result_id,
            expected_version=1,
            period="2026-09",
            allocations=[BudgetAllocationInput(category_id=category, limit="1.00")],
            published_at=WHEN,
        )
    )
    with pytest.raises(FinanceError) as raised:
        service.publish_budget_version(
            PublishBudgetVersion(
                **virtual.source(),
                plan_id=plan.result_id,
                expected_version=1,
                period="2026-09",
                allocations=[BudgetAllocationInput(category_id=category, limit="2.00")],
                adjustment_reason="虚拟过期版本",
                published_at=WHEN.replace(day=16),
            )
        )
    assert raised.value.code == "concurrent_modification"
    assert [row.version_no for row in service.list_budget_versions(plan.result_id)] == [1]


@pytest.mark.c3("BUD-07", "MIG-09")
def test_sqlite_concurrent_budget_publish_has_one_winner_or_safe_lock_error(service, virtual) -> None:
    category = virtual.category("expense", "虚拟 SQLite 并发预算")
    plan = service.create_budget_plan(CreateBudgetPlan(**virtual.source(), name="虚拟 SQLite 预算计划"))
    barrier = Barrier(2)

    def publish(index: int):
        barrier.wait(timeout=5)
        try:
            return service.publish_budget_version(
                PublishBudgetVersion(
                    source_system="p1-c4",
                    source_event_id=f"virtual-sqlite-budget-{index}",
                    plan_id=plan.result_id,
                    expected_version=1,
                    period="2026-09",
                    allocations=[BudgetAllocationInput(category_id=category, limit=f"{index}.00")],
                    published_at=datetime(2026, 9, index, tzinfo=TZ),
                )
            )
        except FinanceError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = [future.result(timeout=10) for future in [pool.submit(publish, 1), pool.submit(publish, 2)]]
    successes = [row for row in outcomes if not isinstance(row, FinanceError)]
    errors = [row for row in outcomes if isinstance(row, FinanceError)]
    assert len(successes) == 1
    assert len(errors) == 1
    assert errors[0].code in {"concurrent_modification", "database_unavailable"}
    versions = service.list_budget_versions(plan.result_id)
    assert [row.version_no for row in versions] == [1]
