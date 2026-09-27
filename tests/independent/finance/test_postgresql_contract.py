from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Barrier

import pytest
from alembic import command
from sqlalchemy import event, inspect, select, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from wife_system.finance.db import make_engine, make_session_factory
from wife_system.finance.errors import FinanceError
from wife_system.finance.models import CommandReceipt, FinancialTransaction, TransactionEntry
from wife_system.finance.schemas import (
    BudgetAllocationInput,
    CreateAccount,
    CreateBudgetPlan,
    CreateCategory,
    PublishBudgetVersion,
    RecordExpense,
    RecordIncome,
    RecordRefund,
    RecordTransfer,
)
from wife_system.finance.service import FinanceService, IdempotencyKeys

from conftest import EXPECTED_TABLES, P1_HEAD_REVISION, TZ, migration_config


pytestmark = pytest.mark.postgresql


@pytest.fixture
def postgresql_engine() -> Engine:
    raw_url = os.getenv("FINANCE_TEST_POSTGRES_URL")
    if not raw_url:
        pytest.skip("FINANCE_TEST_POSTGRES_URL is not set; real PostgreSQL evidence is blocked")
    parsed = make_url(raw_url)
    if parsed.get_backend_name() != "postgresql":
        pytest.skip("FINANCE_TEST_POSTGRES_URL is not a PostgreSQL URL")

    schema = f"p1_c4_{uuid.uuid4().hex}"
    admin = make_engine(raw_url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    query = dict(parsed.query)
    query["options"] = f"-csearch_path={schema},public"
    isolated_url = parsed.set(query=query).render_as_string(hide_password=False)
    engine: Engine | None = None
    try:
        command.upgrade(migration_config(isolated_url), P1_HEAD_REVISION)
        engine = make_engine(isolated_url)
        yield engine
    finally:
        if engine is not None:
            engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin.dispose()


@pytest.fixture
def postgresql_service(postgresql_engine: Engine) -> FinanceService:
    return FinanceService(
        make_session_factory(postgresql_engine),
        IdempotencyKeys({1: b"p1-c4-postgresql-virtual-secret"}),
    )


def _source(event_id: str) -> dict[str, str]:
    return {"source_system": "p1-c4-postgresql", "source_event_id": event_id}


def _setup_account_category(service: FinanceService, kind: str = "expense"):
    suffix = uuid.uuid4().hex
    account = service.create_account(
        CreateAccount(**_source(f"account-{suffix}"), name=f"虚拟 PG 账户 {suffix[:8]}")
    ).result_id
    category = service.create_category(
        CreateCategory(
            **_source(f"category-{suffix}"),
            kind=kind,
            name=f"虚拟 PG 分类 {suffix[:8]}",
        )
    ).result_id
    return account, category


@pytest.mark.c3("MIG-01", "MIG-05", "MIG-07", "MIG-08")
def test_postgresql_empty_migration_constraints_types_and_repeat_upgrade(postgresql_engine: Engine) -> None:
    inspector = inspect(postgresql_engine)
    assert EXPECTED_TABLES | {"alembic_version"} <= set(inspector.get_table_names())
    command.upgrade(
        migration_config(postgresql_engine.url.render_as_string(hide_password=False)), P1_HEAD_REVISION
    )
    occurred_at = next(
        row for row in inspector.get_columns("financial_transaction") if row["name"] == "occurred_at"
    )
    amount_minor = next(
        row for row in inspector.get_columns("transaction_entry") if row["name"] == "amount_minor"
    )
    assert occurred_at["type"].timezone is True
    assert amount_minor["type"].python_type is int


@pytest.mark.c3("LED-10", "ERR-01", "MIG-05")
def test_postgresql_deferred_balance_trigger_rejects_direct_unbalanced_commit(
    postgresql_engine: Engine,
) -> None:
    with pytest.raises(IntegrityError):
        with Session(postgresql_engine) as session, session.begin():
            receipt = CommandReceipt(
                source_system="p1-c4-postgresql",
                key_version=1,
                key_digest=uuid.uuid4().hex + uuid.uuid4().hex,
                request_fingerprint=uuid.uuid4().hex + uuid.uuid4().hex,
                command_name="virtual_unbalanced",
            )
            session.add(receipt)
            session.flush()
            transaction = FinancialTransaction(
                kind="opening_balance",
                occurred_at=datetime(2026, 9, 1, tzinfo=TZ),
                currency="CNY",
                command_receipt_id=receipt.id,
            )
            session.add(transaction)
            session.flush()
            session.add(
                TransactionEntry(
                    transaction_id=transaction.id,
                    line_no=1,
                    entry_role="opening_equity",
                    amount_minor=100,
                )
            )


@pytest.mark.c3("IDM-03")
def test_postgresql_two_connection_same_key_returns_one_result(
    postgresql_service: FinanceService,
) -> None:
    account, category = _setup_account_category(postgresql_service)
    barrier = Barrier(2)

    def submit():
        barrier.wait(timeout=10)
        return postgresql_service.record_expense(
            RecordExpense(
                **_source("same-key"),
                account_id=account,
                category_id=category,
                amount="1.00",
                occurred_at=datetime(2026, 9, 2, tzinfo=TZ),
            )
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [future.result(timeout=20) for future in [pool.submit(submit), pool.submit(submit)]]
    assert {row.result_id for row in results}.__len__() == 1
    assert sorted(row.replayed for row in results) == [False, True]
    assert postgresql_service.account_balance(account) == -100


@pytest.mark.c3("REF-06", "MIG-09")
def test_postgresql_concurrent_refunds_lock_original_and_enforce_total(
    postgresql_service: FinanceService,
) -> None:
    account, category = _setup_account_category(postgresql_service)
    expense = postgresql_service.record_expense(
        RecordExpense(
            **_source("refund-original"),
            account_id=account,
            category_id=category,
            amount="18.00",
            occurred_at=datetime(2026, 9, 2, tzinfo=TZ),
        )
    )
    barrier = Barrier(2)

    def submit(index: int):
        barrier.wait(timeout=10)
        try:
            return postgresql_service.record_refund(
                RecordRefund(
                    **_source(f"refund-{index}"),
                    original_transaction_id=expense.result_id,
                    destination_account_id=account,
                    amount="12.00",
                    occurred_at=datetime(2026, 9, 3, tzinfo=TZ),
                )
            )
        except FinanceError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = [future.result(timeout=20) for future in [pool.submit(submit, 1), pool.submit(submit, 2)]]
    assert sum(not isinstance(row, FinanceError) for row in outcomes) == 1
    errors = [row for row in outcomes if isinstance(row, FinanceError)]
    assert [row.code for row in errors] == ["refund_exceeds_original"]
    assert postgresql_service.account_balance(account) == -600


@pytest.mark.c3("TRF-06", "MIG-09")
def test_postgresql_concurrent_transfers_append_both_ledger_facts_without_lost_update(
    postgresql_service: FinanceService,
) -> None:
    source, _ = _setup_account_category(postgresql_service)
    first_destination, _ = _setup_account_category(postgresql_service)
    second_destination, _ = _setup_account_category(postgresql_service)
    barrier = Barrier(2)

    def submit(index: int, destination: uuid.UUID):
        barrier.wait(timeout=10)
        return postgresql_service.record_transfer(
            RecordTransfer(
                **_source(f"transfer-{index}"),
                source_account_id=source,
                destination_account_id=destination,
                amount=f"{index}.00",
                occurred_at=datetime(2026, 9, 4, tzinfo=TZ),
            )
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [
            future.result(timeout=20)
            for future in [
                pool.submit(submit, 1, first_destination),
                pool.submit(submit, 2, second_destination),
            ]
        ]
    assert len({row.result_id for row in results}) == 2
    assert postgresql_service.account_balance(source) == -300
    assert postgresql_service.account_balance(first_destination) == 100
    assert postgresql_service.account_balance(second_destination) == 200


@pytest.mark.c3("BUD-07", "LED-08", "MIG-09")
def test_postgresql_concurrent_budget_publish_has_one_version_winner(
    postgresql_service: FinanceService,
) -> None:
    _, category = _setup_account_category(postgresql_service)
    plan = postgresql_service.create_budget_plan(
        CreateBudgetPlan(**_source("budget-plan"), name="虚拟 PG 并发预算")
    )
    barrier = Barrier(2)

    def publish(index: int):
        barrier.wait(timeout=10)
        try:
            return postgresql_service.publish_budget_version(
                PublishBudgetVersion(
                    **_source(f"budget-{index}"),
                    plan_id=plan.result_id,
                    expected_version=1,
                    period="2026-09",
                    allocations=[
                        BudgetAllocationInput(category_id=category, limit=f"{index}.00")
                    ],
                    published_at=datetime(2026, 9, index, tzinfo=TZ),
                )
            )
        except FinanceError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = [future.result(timeout=20) for future in [pool.submit(publish, 1), pool.submit(publish, 2)]]
    assert sum(not isinstance(row, FinanceError) for row in outcomes) == 1
    errors = [row for row in outcomes if isinstance(row, FinanceError)]
    assert [row.code for row in errors] == ["concurrent_modification"]
    versions = postgresql_service.list_budget_versions(plan.result_id)
    assert [row.version_no for row in versions] == [1]


@pytest.mark.c3("SNP-09", "MIG-09")
def test_postgresql_snapshot_sets_read_only_repeatable_read_transaction(
    postgresql_engine: Engine, postgresql_service: FinanceService
) -> None:
    statements: list[str] = []

    def capture(_connection, _cursor, statement, _parameters, _context, _executemany):
        statements.append(statement)

    event.listen(postgresql_engine, "before_cursor_execute", capture)
    try:
        snapshot = postgresql_service.monthly_snapshot(
            "2026-09", datetime(2026, 10, 1, tzinfo=TZ)
        )
    finally:
        event.remove(postgresql_engine, "before_cursor_execute", capture)
    assert snapshot.period == "2026-09"
    assert any(
        "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY" in statement.upper()
        for statement in statements
    )


@pytest.mark.c3("MIG-08")
def test_postgresql_timestamptz_round_trip_is_aware_utc(
    postgresql_service: FinanceService,
) -> None:
    account, category = _setup_account_category(postgresql_service, kind="income")
    result = postgresql_service.record_income(
        RecordIncome(
            **_source("time-round-trip"),
            account_id=account,
            category_id=category,
            amount="1.00",
            occurred_at=datetime(2026, 9, 1, 0, 30, tzinfo=TZ),
        )
    )
    row = next(item for item in postgresql_service.list_transactions() if item.id == result.result_id)
    assert row.occurred_at.tzinfo is not None
    assert row.occurred_at.utcoffset() is not None
    assert row.occurred_at.isoformat() == "2026-08-31T16:30:00+00:00"
