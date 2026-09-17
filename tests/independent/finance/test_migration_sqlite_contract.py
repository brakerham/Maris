from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.exc import IntegrityError, OperationalError

from wife_system.finance.db import make_engine, make_session_factory
from wife_system.finance.models import TransactionEntry
from wife_system.finance.schemas import (
    AllocateActivityExpense,
    ArchiveResource,
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

from conftest import EXPECTED_TABLES, TZ, migration_config


FIRST_REVISION = "bfc163b9b8e9"
HEAD_REVISION = "1377551283d0"
MINOR_COLUMNS = {
    "transaction_entry": "amount_minor",
    "activity_template_revision": "reference_minor",
    "activity_entry_allocation": "allocated_minor",
    "income_schedule_version": "amount_minor",
    "income_expectation": "expected_minor",
    "income_expectation_match": "matched_minor",
    "budget_allocation": "limit_minor",
}


@pytest.mark.c3("MIG-01", "MIG-05")
def test_sqlite_empty_base_to_head_repeat_has_expected_schema_and_head(tmp_path: Path) -> None:
    url = f"sqlite:///{(tmp_path / 'empty.sqlite3').as_posix()}"
    config = migration_config(url)
    command.upgrade(config, HEAD_REVISION)
    command.upgrade(config, HEAD_REVISION)
    engine = make_engine(url)
    inspector = inspect(engine)
    assert set(inspector.get_table_names()) == EXPECTED_TABLES | {"alembic_version"}
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == HEAD_REVISION
    assert {row["name"] for row in inspector.get_unique_constraints("command_receipt")} >= {
        "uq_command_receipt_source_digest"
    }
    assert {row["name"] for row in inspector.get_indexes("transaction_entry")} >= {
        "ix_transaction_entry_account_transaction",
        "ix_transaction_entry_category_transaction",
    }
    assert {row["name"] for row in inspector.get_check_constraints("transaction_entry")} >= {
        "ck_transaction_entry_amount_nonzero",
        "ck_transaction_entry_role",
        "ck_transaction_entry_target_shape",
    }
    engine.dispose()


@pytest.mark.c3("MIG-01", "MIG-02", "MIG-05", "MIG-07")
def test_first_revision_with_all_minor_data_upgrades_to_new_head_without_rewriting_data(
    tmp_path: Path,
) -> None:
    url = f"sqlite:///{(tmp_path / 'preserve.sqlite3').as_posix()}"
    config = migration_config(url)
    command.upgrade(config, FIRST_REVISION)
    engine = make_engine(url)
    service = FinanceService(
        make_session_factory(engine), IdempotencyKeys({1: b"p1-c4-migration-virtual-secret"})
    )
    account = service.create_account(
        CreateAccount(source_system="p1-c4", source_event_id="preserve-account", name="虚拟迁移账户")
    )
    category = service.create_category(
        CreateCategory(
            source_system="p1-c4",
            source_event_id="preserve-category",
            kind="income", name="虚拟迁移收入",
        )
    )
    expense_category = service.create_category(
        CreateCategory(
            source_system="p1-c4", source_event_id="preserve-expense-category",
            kind="expense", name="虚拟迁移支出",
        )
    )
    transaction = service.record_income(
        RecordIncome(
            source_system="p1-c4",
            source_event_id="preserve-income",
            account_id=account.result_id,
            category_id=category.result_id,
            amount="12.34",
            occurred_at=datetime(2026, 9, 1, tzinfo=TZ),
        )
    )
    expense = service.record_expense(
        RecordExpense(
            source_system="p1-c4", source_event_id="preserve-expense",
            account_id=account.result_id, category_id=expense_category.result_id,
            amount="2.00", occurred_at=datetime(2026, 9, 2, tzinfo=TZ),
        )
    )
    template = service.create_activity_template(
        CreateActivityTemplate(
            source_system="p1-c4", source_event_id="preserve-template",
            name="虚拟迁移活动", reference_amount="1.00",
        )
    )
    occurrence = service.record_activity_occurrence(
        RecordActivityOccurrence(
            source_system="p1-c4", source_event_id="preserve-occurrence",
            template_id=template.result_id, occurred_at=datetime(2026, 9, 2, tzinfo=TZ),
        )
    )
    schedule = service.create_income_schedule(
        CreateIncomeSchedule(
            source_system="p1-c4", source_event_id="preserve-schedule",
            amount="3.00", effective_from="2026-09-01", due_day=30,
        )
    )
    expectation = service.generate_income_expectation(
        GenerateIncomeExpectation(
            source_system="p1-c4", source_event_id="preserve-expectation",
            schedule_id=schedule.result_id, period="2026-09",
        )
    )
    with service._sessions() as session:
        expense_entry = session.scalar(
            select(TransactionEntry.id).where(
                TransactionEntry.transaction_id == expense.result_id,
                TransactionEntry.entry_role == "expense",
            )
        )
        income_entry = session.scalar(
            select(TransactionEntry.id).where(
                TransactionEntry.transaction_id == transaction.result_id,
                TransactionEntry.entry_role == "income",
            )
        )
    assert expense_entry is not None and income_entry is not None
    service.allocate_activity_expense(
        AllocateActivityExpense(
            source_system="p1-c4", source_event_id="preserve-allocation",
            occurrence_id=occurrence.result_id, expense_entry_id=expense_entry, amount="1.00",
        )
    )
    service.match_income_expectation(
        MatchIncomeExpectation(
            source_system="p1-c4", source_event_id="preserve-match",
            expectation_id=expectation.result_id, income_entry_id=income_entry, amount="1.00",
        )
    )
    plan = service.create_budget_plan(
        CreateBudgetPlan(source_system="p1-c4", source_event_id="preserve-plan", name="虚拟迁移预算")
    )
    budget = service.publish_budget_version(
        PublishBudgetVersion(
            source_system="p1-c4", source_event_id="preserve-budget",
            plan_id=plan.result_id, expected_version=1, period="2026-09",
            allocations=[BudgetAllocationInput(category_id=expense_category.result_id, limit="1.00")],
            published_at=datetime(2026, 9, 1, tzinfo=TZ),
        )
    )
    with engine.connect() as connection:
        before = {
            table: connection.execute(
                text(f"SELECT id, {column} FROM {table} ORDER BY id")
            ).all()
            for table, column in MINOR_COLUMNS.items()
        }
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == FIRST_REVISION
    engine.dispose()
    command.upgrade(config, HEAD_REVISION)
    engine = make_engine(url)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == HEAD_REVISION
        after = {
            table: connection.execute(
                text(f"SELECT id, {column} FROM {table} ORDER BY id")
            ).all()
            for table, column in MINOR_COLUMNS.items()
        }
        assert after == before
        assert connection.scalar(
            text("SELECT limit_minor FROM budget_allocation WHERE budget_version_id=:id"),
            {"id": budget.result_id.hex},
        ) == 100
    engine.dispose()


@pytest.mark.c3("MIG-03")
def test_sqlite_development_downgrade_to_base_and_rebuild(tmp_path: Path) -> None:
    url = f"sqlite:///{(tmp_path / 'rebuild.sqlite3').as_posix()}"
    config = migration_config(url)
    command.upgrade(config, HEAD_REVISION)
    engine = make_engine(url)
    service = FinanceService(
        make_session_factory(engine), IdempotencyKeys({1: b"p1-c4-rebuild-virtual-secret"})
    )
    service.create_account(
        CreateAccount(source_system="p1-c4", source_event_id="rebuild-account", name="虚拟重建账户")
    )
    engine.dispose()
    command.downgrade(config, "base")
    engine = create_engine(url)
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}
    engine.dispose()
    command.upgrade(config, HEAD_REVISION)
    engine = make_engine(url)
    assert set(inspect(engine).get_table_names()) == EXPECTED_TABLES | {"alembic_version"}
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM account")) == 0
    engine.dispose()


@pytest.mark.c3("MIG-04")
def test_failed_sqlite_upgrade_does_not_delete_unknown_existing_data_and_fresh_rebuild_recovers(
    tmp_path: Path,
) -> None:
    broken_path = tmp_path / "broken.sqlite3"
    broken_url = f"sqlite:///{broken_path.as_posix()}"
    engine = create_engine(broken_url)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE account (private_marker TEXT NOT NULL)"))
        connection.execute(text("INSERT INTO account(private_marker) VALUES ('VIRTUAL_MARKER')"))
    engine.dispose()
    with pytest.raises((OperationalError, RuntimeError)):
        command.upgrade(migration_config(broken_url), HEAD_REVISION)
    engine = create_engine(broken_url)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT private_marker FROM account")) == "VIRTUAL_MARKER"
        version_table = "alembic_version" in inspect(connection).get_table_names()
        if version_table:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) is None
    engine.dispose()

    fresh_url = f"sqlite:///{(tmp_path / 'fresh-recovery.sqlite3').as_posix()}"
    command.upgrade(migration_config(fresh_url), HEAD_REVISION)
    fresh = make_engine(fresh_url)
    assert set(inspect(fresh).get_table_names()) == EXPECTED_TABLES | {"alembic_version"}
    fresh.dispose()


@pytest.mark.c3("MIG-06", "ERR-02")
def test_every_application_sqlite_connection_enables_foreign_keys(sqlite_url: str) -> None:
    engine = make_engine(sqlite_url)
    for _ in range(3):
        with engine.connect() as connection:
            assert connection.scalar(text("PRAGMA foreign_keys")) == 1
            with pytest.raises(IntegrityError):
                connection.execute(
                    text(
                        "INSERT INTO audit_event "
                        "(id, command_receipt_id, entity_type, entity_id, action, created_at) "
                        "VALUES (:id, :receipt, 'virtual', :entity, 'virtual', CURRENT_TIMESTAMP)"
                    ),
                    {
                        "id": uuid.uuid4().hex,
                        "receipt": uuid.uuid4().hex,
                        "entity": uuid.uuid4().hex,
                    },
                )
    engine.dispose()


@pytest.mark.c3("MIG-07", "ERR-01")
def test_sqlite_rejects_non_integer_storage_class_for_minor_amounts(service, virtual, sqlite_engine) -> None:
    account = virtual.account("虚拟动态类型账户")
    income_category = virtual.category("income", "虚拟动态类型收入")
    category = virtual.category("expense", "虚拟动态类型支出")
    income = service.record_income(
        RecordIncome(
            **virtual.source(), account_id=account, category_id=income_category,
            amount="3.00", occurred_at=datetime(2026, 9, 1, tzinfo=TZ),
        )
    )
    expense = service.record_expense(
        RecordExpense(
            **virtual.source(), account_id=account, category_id=category,
            amount="2.00", occurred_at=datetime(2026, 9, 2, tzinfo=TZ),
        )
    )
    template = service.create_activity_template(
        CreateActivityTemplate(**virtual.source(), name="虚拟动态类型活动", reference_amount="1.00")
    )
    occurrence = service.record_activity_occurrence(
        RecordActivityOccurrence(
            **virtual.source(), template_id=template.result_id,
            occurred_at=datetime(2026, 9, 2, tzinfo=TZ),
        )
    )
    schedule = service.create_income_schedule(
        CreateIncomeSchedule(
            **virtual.source(), amount="3.00", effective_from="2026-09-01", due_day=30,
        )
    )
    expectation = service.generate_income_expectation(
        GenerateIncomeExpectation(**virtual.source(), schedule_id=schedule.result_id, period="2026-09")
    )
    with service._sessions() as session:
        expense_entry = session.scalar(
            select(TransactionEntry.id).where(
                TransactionEntry.transaction_id == expense.result_id,
                TransactionEntry.entry_role == "expense",
            )
        )
        income_entry = session.scalar(
            select(TransactionEntry.id).where(
                TransactionEntry.transaction_id == income.result_id,
                TransactionEntry.entry_role == "income",
            )
        )
    assert expense_entry is not None and income_entry is not None
    service.allocate_activity_expense(
        AllocateActivityExpense(
            **virtual.source(), occurrence_id=occurrence.result_id,
            expense_entry_id=expense_entry, amount="1.00",
        )
    )
    service.match_income_expectation(
        MatchIncomeExpectation(
            **virtual.source(), expectation_id=expectation.result_id,
            income_entry_id=income_entry, amount="1.00",
        )
    )
    plan = service.create_budget_plan(CreateBudgetPlan(**virtual.source(), name="虚拟动态类型预算"))
    service.publish_budget_version(
        PublishBudgetVersion(
            **virtual.source(),
            plan_id=plan.result_id,
            expected_version=1,
            period="2026-09",
            allocations=[BudgetAllocationInput(category_id=category, limit="1.00")],
            published_at=datetime(2026, 9, 1, tzinfo=TZ),
        )
    )

    for table, column in MINOR_COLUMNS.items():
        for invalid in ("VIRTUAL_NON_INTEGER_AMOUNT", 1.5):
            with pytest.raises(IntegrityError):
                with sqlite_engine.begin() as connection:
                    connection.execute(
                        text(
                            f"UPDATE {table} SET {column}=:value "
                            f"WHERE rowid=(SELECT min(rowid) FROM {table})"
                        ),
                        {"value": invalid},
                    )
        with sqlite_engine.begin() as connection:
            changed = connection.execute(
                text(
                    f"UPDATE {table} SET {column}={column} "
                    f"WHERE rowid=(SELECT min(rowid) FROM {table})"
                )
            )
            assert changed.rowcount == 1

    with sqlite_engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE activity_template_revision SET reference_minor=NULL "
                "WHERE rowid=(SELECT min(rowid) FROM activity_template_revision)"
            )
        )
        assert connection.scalar(
            text("SELECT reference_minor FROM activity_template_revision ORDER BY rowid LIMIT 1")
        ) is None
    for table, column in MINOR_COLUMNS.items():
        if table == "activity_template_revision":
            continue
        with pytest.raises(IntegrityError):
            with sqlite_engine.begin() as connection:
                connection.execute(
                    text(
                        f"UPDATE {table} SET {column}=NULL "
                        f"WHERE rowid=(SELECT min(rowid) FROM {table})"
                    )
                )


@pytest.mark.c3("MIG-01", "MIG-07")
def test_postgresql_offline_ddl_omits_sqlite_typeof_guards(tmp_path: Path) -> None:
    config = migration_config(
        "postgresql+psycopg://wife_test:wife_test_only@127.0.0.1:55432/wife_finance_test"
    )
    output = tmp_path / "postgresql-offline.sql"
    with output.open("w", encoding="utf-8") as stream:
        config.output_buffer = stream
        command.upgrade(config, HEAD_REVISION, sql=True)
    ddl = output.read_text(encoding="utf-8").lower()
    assert "1377551283d0" in ddl
    assert "typeof(" not in ddl
    assert "deferrable initially deferred" in ddl


@pytest.mark.c3("MIG-08")
def test_sqlite_public_timepoints_round_trip_as_aware_utc(service, virtual) -> None:
    account = service.create_account(
        CreateAccount(**virtual.source(), name="虚拟时区账户")
    )
    category = service.create_category(
        CreateCategory(**virtual.source(), kind="income", name="虚拟时区收入")
    )
    expense_category = virtual.category("expense", "虚拟时区支出")
    result = service.record_income(
        RecordIncome(
            **virtual.source(),
            account_id=account.result_id,
            category_id=category.result_id,
            amount="1.00",
            occurred_at=datetime(2026, 9, 1, 0, 30, tzinfo=TZ),
        )
    )
    plan = service.create_budget_plan(CreateBudgetPlan(**virtual.source(), name="虚拟时区预算"))
    service.publish_budget_version(
        PublishBudgetVersion(
            **virtual.source(), plan_id=plan.result_id, expected_version=1, period="2026-09",
            allocations=[BudgetAllocationInput(category_id=expense_category, limit="1.00")],
            published_at=datetime(2026, 9, 1, 1, 0, tzinfo=TZ),
        )
    )
    service.archive_account(
        ArchiveResource(
            **virtual.source(), resource_id=account.result_id, expected_version=1, reason="虚拟归档"
        )
    )
    service.archive_category(
        ArchiveResource(
            **virtual.source(), resource_id=category.result_id, expected_version=1, reason="虚拟归档"
        )
    )
    row = next(item for item in service.list_transactions() if item.id == result.result_id)
    account_view = next(
        item for item in service.list_accounts(include_archived=True) if item.id == account.result_id
    )
    category_view = next(
        item for item in service.list_categories(include_archived=True) if item.id == category.result_id
    )
    budget_view = service.list_budget_versions(plan.result_id, period="2026-09")[0]
    assert row.occurred_at.isoformat() == "2026-08-31T16:30:00+00:00"
    for value in (
        row.occurred_at,
        account_view.created_at,
        account_view.archived_at,
        category_view.created_at,
        category_view.archived_at,
        budget_view.published_at,
    ):
        assert value is not None
        assert value.tzinfo is UTC
