from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url

from wife_system.finance.db import make_engine, make_session_factory
from wife_system.finance.errors import FinanceError
from wife_system.finance.schemas import CreateAccount, CreateCategory, RecordExpense
from wife_system.finance.service import FinanceService, IdempotencyKeys


P1_HEAD_REVISION = "1377551283d0"


def _migration_config(database_url: str) -> Config:
    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


@pytest.fixture
def postgresql_service() -> Iterator[FinanceService]:
    raw_url = os.getenv("FINANCE_TEST_POSTGRES_URL")
    if not raw_url:
        pytest.skip("FINANCE_TEST_POSTGRES_URL is required for the executor PostgreSQL regression")
    parsed = make_url(raw_url)
    if parsed.get_backend_name() != "postgresql":
        pytest.skip("FINANCE_TEST_POSTGRES_URL must be a PostgreSQL URL")

    schema = f"c7_data_r1_{uuid.uuid4().hex}"
    admin = make_engine(raw_url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    query = dict(parsed.query)
    query["options"] = f"-csearch_path={schema},public"
    isolated_url = parsed.set(query=query).render_as_string(hide_password=False)
    engine = None
    try:
        command.upgrade(_migration_config(isolated_url), P1_HEAD_REVISION)
        engine = make_engine(isolated_url)
        yield FinanceService(
            make_session_factory(engine),
            IdempotencyKeys({1: b"pg-c7-data-r1-virtual-secret"}),
        )
    finally:
        if engine is not None:
            engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin.dispose()


def test_postgresql_first_write_owns_new_claim(postgresql_service: FinanceService) -> None:
    result = postgresql_service.create_account(
        CreateAccount(
            source_system="pg-c7-data-r1",
            source_event_id="first-account",
            name="虚拟 PostgreSQL 首写账户",
        )
    )

    assert result.result_type == "account"
    assert result.replayed is False


def test_postgresql_claim_replays_same_payload_and_rejects_conflict(
    postgresql_service: FinanceService,
) -> None:
    command = CreateAccount(
        source_system="pg-c7-data-r1",
        source_event_id="replay-account",
        name="虚拟 PostgreSQL 重放账户",
    )

    first = postgresql_service.create_account(command)
    replay = postgresql_service.create_account(command)

    assert first.replayed is False
    assert replay.replayed is True
    assert replay.result_id == first.result_id

    with pytest.raises(FinanceError) as raised:
        postgresql_service.create_account(
            command.model_copy(update={"name": "虚拟 PostgreSQL 冲突账户"})
        )
    assert raised.value.code == "duplicate_request_conflict"
    assert [row.id for row in postgresql_service.list_accounts()] == [first.result_id]


def test_postgresql_concurrent_same_key_creates_one_business_result(
    postgresql_service: FinanceService,
) -> None:
    barrier = Barrier(2)
    command = CreateAccount(
        source_system="pg-c7-data-r1",
        source_event_id="concurrent-account",
        name="虚拟 PostgreSQL 并发账户",
    )

    def submit():
        barrier.wait(timeout=10)
        return postgresql_service.create_account(command)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(submit), pool.submit(submit)]
        results = [future.result(timeout=20) for future in futures]

    assert len({result.result_id for result in results}) == 1
    assert sorted(result.replayed for result in results) == [False, True]
    assert [row.id for row in postgresql_service.list_accounts()] == [results[0].result_id]


def test_postgresql_failed_business_write_rolls_back_claim(
    postgresql_service: FinanceService,
) -> None:
    account = postgresql_service.create_account(
        CreateAccount(
            source_system="pg-c7-data-r1",
            source_event_id="atomic-account",
            name="虚拟 PostgreSQL 原子账户",
        )
    )
    failed = RecordExpense(
        source_system="pg-c7-data-r1",
        source_event_id="atomic-expense",
        account_id=account.result_id,
        category_id=uuid.uuid4(),
        amount="1.00",
        occurred_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )

    with pytest.raises(FinanceError):
        postgresql_service.record_expense(failed)

    category = postgresql_service.create_category(
        CreateCategory(
            source_system="pg-c7-data-r1",
            source_event_id="atomic-category",
            kind="expense",
            name="虚拟 PostgreSQL 原子分类",
        )
    )
    recovered = postgresql_service.record_expense(
        failed.model_copy(update={"category_id": category.result_id})
    )

    assert recovered.result_type == "financial_transaction"
    assert recovered.replayed is False
