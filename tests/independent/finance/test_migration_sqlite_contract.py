from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.exc import IntegrityError, OperationalError

from wife_system.finance.db import make_engine, make_session_factory
from wife_system.finance.models import BOOTSTRAP_USER_ID, TransactionEntry
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
HEAD_REVISION = "p4_host_state"
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
    assert EXPECTED_TABLES | {"alembic_version"} <= set(inspector.get_table_names())
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == HEAD_REVISION
    assert {row["name"] for row in inspector.get_unique_constraints("command_receipt")} >= {
        "uq_receipt_user_source_digest"
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
def test_first_p1_revision_finance_facts_upgrade_to_p4_without_rewriting_data(
    tmp_path: Path,
) -> None:
    url = f"sqlite:///{(tmp_path / 'preserve.sqlite3').as_posix()}"
    config = migration_config(url)
    command.upgrade(config, FIRST_REVISION)

    ids = {name: uuid.uuid4().hex for name in (
        "account", "expense_category", "income_category", "receipt", "transaction",
        "account_entry", "expense_entry",
    )}
    created_at = "2026-09-01 08:00:00+00:00"
    engine = create_engine(url)
    with engine.begin() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == FIRST_REVISION
        connection.execute(
            text(
                "INSERT INTO account (id,name,currency,archived_at,created_at,version_id) "
                "VALUES (:id,'virtual first-revision account','CNY',NULL,:created,1)"
            ),
            {"id": ids["account"], "created": created_at},
        )
        connection.execute(
            text(
                "INSERT INTO category "
                "(id,kind,name,name_normalized,archived_at,created_at,version_id) VALUES "
                "(:expense,'expense','virtual first-revision expense','virtual first-revision expense',NULL,:created,1),"
                "(:income,'income','virtual first-revision income','virtual first-revision income',NULL,:created,1)"
            ),
            {
                "expense": ids["expense_category"],
                "income": ids["income_category"],
                "created": created_at,
            },
        )
        connection.execute(
            text(
                "INSERT INTO command_receipt "
                "(id,source_system,key_version,key_digest,request_fingerprint,command_name,"
                "result_type,result_id,result_json,completed_at,created_at) VALUES "
                "(:id,'p4-c11-r1',1,:digest,:fingerprint,'record_expense',"
                "'financial_transaction',:result_id,NULL,:created,:created)"
            ),
            {
                "id": ids["receipt"],
                "digest": "1" * 64,
                "fingerprint": "2" * 64,
                "result_id": ids["transaction"],
                "created": created_at,
            },
        )
        connection.execute(
            text(
                "INSERT INTO financial_transaction "
                "(id,kind,status,occurred_at,currency,related_transaction_id,relation_kind,"
                "command_receipt_id,created_at) VALUES "
                "(:id,'expense','posted',:created,'CNY',NULL,NULL,:receipt,:created)"
            ),
            {"id": ids["transaction"], "receipt": ids["receipt"], "created": created_at},
        )
        connection.execute(
            text(
                "INSERT INTO transaction_entry "
                "(id,transaction_id,line_no,entry_role,amount_minor,account_id,category_id) VALUES "
                "(:account_entry,:transaction,1,'account',-1234,:account,NULL),"
                "(:expense_entry,:transaction,2,'expense',1234,NULL,:category)"
            ),
            {
                "account_entry": ids["account_entry"],
                "expense_entry": ids["expense_entry"],
                "transaction": ids["transaction"],
                "account": ids["account"],
                "category": ids["expense_category"],
            },
        )
    engine.dispose()

    command.upgrade(config, HEAD_REVISION)
    engine = create_engine(url)
    owner = BOOTSTRAP_USER_ID.hex
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == HEAD_REVISION
        assert connection.scalar(text("PRAGMA foreign_key_check")) is None
        assert connection.scalar(text("SELECT COUNT(*) FROM account")) == 1
        assert connection.scalar(text("SELECT COUNT(*) FROM category")) == 2
        assert connection.scalar(text("SELECT COUNT(*) FROM financial_transaction")) == 1
        assert connection.scalar(text("SELECT COUNT(*) FROM transaction_entry")) == 2
        assert connection.execute(
            text(
                "SELECT kind,status,currency,command_receipt_id FROM financial_transaction WHERE id=:id"
            ),
            {"id": ids["transaction"]},
        ).one() == ("expense", "posted", "CNY", ids["receipt"])
        assert connection.execute(
            text(
                "SELECT line_no,entry_role,amount_minor,typeof(amount_minor),account_id,category_id "
                "FROM transaction_entry WHERE transaction_id=:id ORDER BY line_no"
            ),
            {"id": ids["transaction"]},
        ).all() == [
            (1, "account", -1234, "integer", ids["account"], None),
            (2, "expense", 1234, "integer", None, ids["expense_category"]),
        ]
        scoped_tables = [
            table
            for table in inspect(connection).get_table_names()
            if any(column["name"] == "user_id" for column in inspect(connection).get_columns(table))
        ]
        for table in scoped_tables:
            assert connection.scalar(
                text(f"SELECT COUNT(*) FROM {table} WHERE user_id IS NULL OR CAST(user_id AS TEXT)='' ")
            ) == 0
        for table in ("account", "category", "command_receipt", "financial_transaction", "transaction_entry"):
            assert connection.scalar(
                text(f"SELECT COUNT(*) FROM {table} WHERE user_id<>:owner"), {"owner": owner}
            ) == 0
        assert connection.scalar(
            text("SELECT COUNT(*) FROM app_user WHERE id=:owner AND bootstrap_marker='bootstrap-owner'"),
            {"owner": owner},
        ) == 1
    assert ScriptDirectory.from_config(config).get_heads() == [HEAD_REVISION]
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
    assert EXPECTED_TABLES | {"alembic_version"} <= set(inspect(engine).get_table_names())
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
    assert EXPECTED_TABLES | {"alembic_version"} <= set(inspect(fresh).get_table_names())
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
        # This is a P1 dialect guard.  Later data migrations intentionally run
        # online preflight queries, so bind the offline SQL assertion to the
        # P1 integer-minor revision it was written to verify.
        command.upgrade(config, "1377551283d0", sql=True)
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
