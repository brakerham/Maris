from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Engine

from wife_system.finance.db import make_engine, make_session_factory
from wife_system.finance.schemas import CreateAccount, CreateCategory
from wife_system.finance.service import FinanceService, IdempotencyKeys


ROOT = Path(__file__).resolve().parents[3]
TZ = ZoneInfo("Asia/Shanghai")
WHEN = datetime(2026, 9, 15, 12, 30, tzinfo=TZ)
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
P1_HEAD_REVISION = "head"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "c3(*ids): P1-C3 case IDs covered by an independent test")
    config.addinivalue_line("markers", "postgresql: requires a real isolated PostgreSQL service")


def migration_config(database_url: str) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


@pytest.fixture
def sqlite_url(tmp_path: Path) -> str:
    path = tmp_path / "independent-finance.sqlite3"
    url = f"sqlite:///{path.as_posix()}"
    command.upgrade(migration_config(url), P1_HEAD_REVISION)
    return url


@pytest.fixture
def sqlite_engine(sqlite_url: str) -> Iterator[Engine]:
    engine = make_engine(sqlite_url)
    yield engine
    engine.dispose()


@pytest.fixture
def service(sqlite_engine: Engine) -> FinanceService:
    return FinanceService(
        make_session_factory(sqlite_engine),
        IdempotencyKeys({1: b"p1-c4-independent-virtual-secret"}),
    )


class VirtualFinance:
    def __init__(self, service: FinanceService) -> None:
        self.service = service
        self._counter = 0

    def event(self, label: str = "event") -> str:
        self._counter += 1
        return f"c4-{label}-{self._counter}"

    def source(self, label: str = "event") -> dict[str, str]:
        return {"source_system": "p1-c4", "source_event_id": self.event(label)}

    def account(self, name: str = "虚拟账户"):
        return self.service.create_account(CreateAccount(**self.source("account"), name=name)).result_id

    def category(self, kind: str, name: str):
        return self.service.create_category(
            CreateCategory(**self.source("category"), kind=kind, name=name)
        ).result_id


@pytest.fixture
def virtual(service: FinanceService) -> VirtualFinance:
    return VirtualFinance(service)
