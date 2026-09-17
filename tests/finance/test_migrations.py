from __future__ import annotations

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from wife_system.finance.db import make_session_factory
from wife_system.finance.schemas import (
    AllocateActivityExpense,
    BudgetAllocationInput,
    CreateAccount,
    CreateActivityTemplate,
    CreateBudgetPlan,
    CreateCategory,
    CreateIncomeSchedule,
    GenerateIncomeExpectation,
    MatchIncomeExpectation,
    PublishBudgetVersion,
    RecordActivityOccurrence,
    RecordExpense,
    RecordIncome,
)
from wife_system.finance.service import FinanceService, IdempotencyKeys


EXPECTED_TABLES = {
    "account",
    "activity_entry_allocation",
    "activity_occurrence",
    "activity_template",
    "activity_template_revision",
    "audit_event",
    "budget_allocation",
    "budget_plan",
    "budget_version",
    "category",
    "command_receipt",
    "financial_transaction",
    "income_expectation",
    "income_expectation_match",
    "income_schedule",
    "income_schedule_version",
    "transaction_entry",
}
FIRST_REVISION = "bfc163b9b8e9"
P1_HEAD_REVISION = "1377551283d0"
MINOR_COLUMNS = {
    "transaction_entry": ("amount_minor",),
    "activity_template_revision": ("reference_minor",),
    "activity_entry_allocation": ("allocated_minor",),
    "income_schedule_version": ("amount_minor",),
    "income_expectation": ("expected_minor",),
    "income_expectation_match": ("matched_minor",),
    "budget_allocation": ("limit_minor",),
}


def migration_config(database_url: str) -> Config:
    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def test_sqlite_base_head_repeat_and_rebuild(tmp_path: Path) -> None:
    path = tmp_path / "finance-migration.db"
    url = f"sqlite:///{path.as_posix()}"
    config = migration_config(url)
    command.upgrade(config, P1_HEAD_REVISION)
    command.upgrade(config, P1_HEAD_REVISION)
    engine = create_engine(url)
    assert set(inspect(engine).get_table_names()) == EXPECTED_TABLES | {"alembic_version"}
    service = FinanceService(make_session_factory(engine), IdempotencyKeys({1: b"virtual-migration-secret"}))
    account = service.create_account(CreateAccount(source_system="migration-test", source_event_id="account", name="虚拟迁移账户"))
    category = service.create_category(CreateCategory(source_system="migration-test", source_event_id="category", kind="income", name="虚拟迁移收入"))
    service.record_income(RecordIncome(
        source_system="migration-test",
        source_event_id="income",
        account_id=account.result_id,
        category_id=category.result_id,
        amount="12.34",
        occurred_at=datetime(2026, 9, 1, tzinfo=ZoneInfo("Asia/Shanghai")),
    ))
    assert service.account_balance(account.result_id) == 1234
    engine.dispose()
    command.downgrade(config, "base")
    command.upgrade(config, P1_HEAD_REVISION)
    engine = create_engine(url)
    assert set(inspect(engine).get_table_names()) == EXPECTED_TABLES | {"alembic_version"}
    engine.dispose()


def test_postgresql_offline_ddl_contains_deferred_balance_trigger(tmp_path: Path) -> None:
    config = migration_config("postgresql+psycopg://wife_test:wife_test_only@127.0.0.1:55432/wife_finance_test")
    output = tmp_path / "postgres.sql"
    with output.open("w", encoding="utf-8") as stream:
        config.output_buffer = stream
        command.upgrade(config, P1_HEAD_REVISION, sql=True)
    ddl = output.read_text(encoding="utf-8")
    assert "DEFERRABLE INITIALLY DEFERRED" in ddl
    assert "finance_check_transaction_balance" in ddl
    assert "typeof(" not in ddl.lower()


def test_previous_revision_with_data_upgrades_to_strict_minor_head(tmp_path: Path) -> None:
    path = tmp_path / "finance-r1-upgrade.db"
    url = f"sqlite:///{path.as_posix()}"
    config = migration_config(url)
    command.upgrade(config, FIRST_REVISION)
    engine = create_engine(url)
    service = FinanceService(make_session_factory(engine), IdempotencyKeys({1: b"virtual-r1-migration-secret"}))
    account = service.create_account(CreateAccount(source_system="r1-migration", source_event_id="account", name="虚拟升级账户"))
    income = service.create_category(CreateCategory(source_system="r1-migration", source_event_id="income", kind="income", name="虚拟升级收入"))
    expense = service.create_category(CreateCategory(source_system="r1-migration", source_event_id="expense", kind="expense", name="虚拟升级支出"))
    transaction = service.record_income(RecordIncome(
        source_system="r1-migration",
        source_event_id="transaction",
        account_id=account.result_id,
        category_id=income.result_id,
        amount="12.34",
        occurred_at=datetime(2026, 9, 1, tzinfo=ZoneInfo("Asia/Shanghai")),
    ))
    expense_transaction = service.record_expense(RecordExpense(
        source_system="r1-migration",
        source_event_id="expense-transaction",
        account_id=account.result_id,
        category_id=expense.result_id,
        amount="2.00",
        occurred_at=datetime(2026, 9, 2, tzinfo=ZoneInfo("Asia/Shanghai")),
    ))
    activity = service.create_activity_template(CreateActivityTemplate(
        source_system="r1-migration", source_event_id="activity", name="虚拟升级活动", reference_amount="1.00"
    ))
    occurrence = service.record_activity_occurrence(RecordActivityOccurrence(
        source_system="r1-migration",
        source_event_id="occurrence",
        template_id=activity.result_id,
        occurred_at=datetime(2026, 9, 2, tzinfo=ZoneInfo("Asia/Shanghai")),
    ))
    schedule = service.create_income_schedule(CreateIncomeSchedule(
        source_system="r1-migration",
        source_event_id="schedule",
        amount="3.00",
        effective_from="2026-09-01",
        due_day=30,
    ))
    expectation = service.generate_income_expectation(GenerateIncomeExpectation(
        source_system="r1-migration", source_event_id="expectation", schedule_id=schedule.result_id, period="2026-09"
    ))
    with service._sessions() as session:
        expense_entry_id = session.scalar(text(
            "SELECT id FROM transaction_entry WHERE transaction_id=:id AND entry_role='expense'"
        ), {"id": expense_transaction.result_id.hex})
        income_entry_id = session.scalar(text(
            "SELECT id FROM transaction_entry WHERE transaction_id=:id AND entry_role='income'"
        ), {"id": transaction.result_id.hex})
    service.allocate_activity_expense(AllocateActivityExpense(
        source_system="r1-migration",
        source_event_id="allocation",
        occurrence_id=occurrence.result_id,
        expense_entry_id=expense_entry_id,
        amount="1.00",
    ))
    service.match_income_expectation(MatchIncomeExpectation(
        source_system="r1-migration",
        source_event_id="match",
        expectation_id=expectation.result_id,
        income_entry_id=income_entry_id,
        amount="1.00",
    ))
    plan = service.create_budget_plan(CreateBudgetPlan(source_system="r1-migration", source_event_id="plan", name="虚拟升级预算"))
    budget = service.publish_budget_version(PublishBudgetVersion(
        source_system="r1-migration",
        source_event_id="budget",
        plan_id=plan.result_id,
        expected_version=1,
        period="2026-09",
        allocations=[BudgetAllocationInput(category_id=expense.result_id, limit="1.00")],
        published_at=datetime(2026, 9, 1, tzinfo=ZoneInfo("Asia/Shanghai")),
    ))
    engine.dispose()

    command.upgrade(config, P1_HEAD_REVISION)
    engine = create_engine(url)
    with engine.begin() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) != FIRST_REVISION
        assert connection.scalar(text("SELECT amount_minor FROM transaction_entry WHERE transaction_id = :id AND entry_role = 'account'"), {"id": transaction.result_id.hex}) == 1234
        assert connection.scalar(text("SELECT limit_minor FROM budget_allocation WHERE budget_version_id = :id"), {"id": budget.result_id.hex}) == 100
        for table, columns in MINOR_COLUMNS.items():
            ddl = connection.scalar(text("SELECT sql FROM sqlite_master WHERE type='table' AND name=:name"), {"name": table}).lower()
            for column in columns:
                assert f"typeof({column})" in ddl.replace(" ", "")
    engine.dispose()

    for table, columns in MINOR_COLUMNS.items():
        for column in columns:
            for invalid in ("PRIVATE_NON_INTEGER_AMOUNT", 1.5):
                with pytest.raises(IntegrityError):
                    with create_engine(url).begin() as connection:
                        connection.execute(text(
                            f"UPDATE {table} SET {column}=:amount WHERE rowid=(SELECT min(rowid) FROM {table})"
                        ), {"amount": invalid})
