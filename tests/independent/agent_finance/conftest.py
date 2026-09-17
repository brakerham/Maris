from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

import pytest
from sqlalchemy.orm import Session, sessionmaker

from wife_system.agent.application import AgentApplication
from wife_system.agent.finance_tools import FinanceToolAdapter, finance_registry
from wife_system.agent.loop import AgentRunner
from wife_system.agent.pending import PendingActionStore
from wife_system.agent.providers import ModelProvider
from wife_system.finance.db import Base, make_engine, make_session_factory
from wife_system.finance.schemas import CreateAccount, CreateCategory, RecordOpeningBalance
from wife_system.finance.service import FinanceService, IdempotencyKeys


ACTOR = uuid.UUID("c6000000-0000-0000-0000-000000000001")
CONVERSATION = uuid.UUID("c6000000-0000-0000-0000-000000000002")
NOW = datetime(2026, 9, 16, 15, 30, tzinfo=UTC)


@dataclass
class IndependentHarness:
    sessions: sessionmaker[Session]
    finance: FinanceService
    pending: PendingActionStore
    adapter: FinanceToolAdapter
    account_id: uuid.UUID
    category_id: uuid.UUID

    def app(self, provider: ModelProvider) -> AgentApplication:
        return AgentApplication(
            sessions=self.sessions,
            runner=AgentRunner(provider=provider, tools=finance_registry(self.adapter)),
            finance_tools=self.adapter,
            pending=self.pending,
            digest_key=b"p2-c6-independent-virtual-key",
        )


@pytest.fixture
def ih(tmp_path: Path) -> Iterator[IndependentHarness]:
    engine = make_engine(f"sqlite+pysqlite:///{tmp_path / 'independent-agent.sqlite3'}")
    Base.metadata.create_all(engine)
    sessions = make_session_factory(engine)
    finance = FinanceService(sessions, IdempotencyKeys({1: b"p2-c6-virtual-finance-key"}))
    account = finance.create_account(
        CreateAccount(source_system="p2-c6", source_event_id="account", name="虚拟日常账户")
    )
    category = finance.create_category(
        CreateCategory(
            source_system="p2-c6", source_event_id="category", kind="expense", name="虚拟餐饮"
        )
    )
    finance.record_opening_balance(
        RecordOpeningBalance(
            source_system="p2-c6",
            source_event_id="opening",
            account_id=account.result_id,
            amount="1000.00",
            occurred_at=datetime(2026, 9, 1, tzinfo=UTC),
        )
    )
    pending = PendingActionStore(sessions)
    yield IndependentHarness(
        sessions=sessions,
        finance=finance,
        pending=pending,
        adapter=FinanceToolAdapter(finance, pending),
        account_id=account.result_id,
        category_id=category.result_id,
    )
    engine.dispose()
