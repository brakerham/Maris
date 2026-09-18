from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, tzinfo
from pathlib import Path
from threading import Lock
from typing import Callable, Iterator

import pytest
from sqlalchemy.orm import Session, sessionmaker

from wife_system.agent import application as application_module
from wife_system.agent import pending as pending_module
from wife_system.agent.application import AgentApplication
from wife_system.agent.finance_tools import FinanceToolAdapter, finance_registry
from wife_system.agent.loop import AgentRunner
from wife_system.agent.models import AgentRunRecord, PendingActionRecord  # noqa: F401
from wife_system.agent.pending import PendingActionStore
from wife_system.agent.providers import ModelProvider
from wife_system.finance.db import Base, make_engine, make_session_factory
from wife_system.finance.schemas import CreateAccount, CreateCategory, RecordOpeningBalance
from wife_system.finance.service import FinanceService, IdempotencyKeys


ACTOR_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
CONVERSATION_ID = uuid.UUID("20000000-0000-0000-0000-000000000001")
RECEIVED_AT = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)


@dataclass
class AgentTestClock:
    """One mutable UTC clock per test, shared with application worker threads."""

    _current: datetime = RECEIVED_AT
    _lock: Lock = field(default_factory=Lock, repr=False)

    def now(self) -> datetime:
        with self._lock:
            return self._current

    def advance(self, delta: timedelta) -> datetime:
        if delta < timedelta(0):
            raise ValueError("test time must move forward")
        with self._lock:
            self._current += delta
            return self._current


@pytest.fixture(autouse=True)
def agent_clock(monkeypatch: pytest.MonkeyPatch) -> Iterator[AgentTestClock]:
    """Freeze only the two runtime lookups; restore them after every test."""

    clock = AgentTestClock()

    class ControlledDateTime(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> datetime:
            current = clock.now()
            if tz is None:
                return current.astimezone().replace(tzinfo=None)
            return current.astimezone(tz)

    # Patch where the names are looked up, including implicit get/resume calls.
    # A child context leaves other monkeypatches owned by the test untouched.
    with monkeypatch.context() as patch:
        patch.setattr(application_module, "datetime", ControlledDateTime)
        patch.setattr(pending_module, "datetime", ControlledDateTime)
        yield clock


@dataclass
class AgentHarness:
    sessions: sessionmaker[Session]
    finance: FinanceService
    pending: PendingActionStore
    adapter: FinanceToolAdapter
    account_id: uuid.UUID
    category_id: uuid.UUID

    def application(self, provider: ModelProvider) -> AgentApplication:
        runner = AgentRunner(provider=provider, tools=finance_registry(self.adapter))
        return AgentApplication(
            sessions=self.sessions,
            runner=runner,
            finance_tools=self.adapter,
            pending=self.pending,
            digest_key=b"virtual-agent-digest-key",
        )


@pytest.fixture
def harness(tmp_path: Path) -> Iterator[AgentHarness]:
    engine = make_engine(f"sqlite+pysqlite:///{tmp_path / 'agent.db'}")
    Base.metadata.create_all(engine)
    sessions = make_session_factory(engine)
    finance = FinanceService(sessions, IdempotencyKeys({1: b"virtual-finance-key"}))
    account = finance.create_account(
        CreateAccount(source_system="test", source_event_id="account", name="日常账户")
    )
    category = finance.create_category(
        CreateCategory(
            source_system="test",
            source_event_id="category",
            kind="expense",
            name="餐饮",
        )
    )
    finance.record_opening_balance(
        RecordOpeningBalance(
            source_system="test",
            source_event_id="opening",
            account_id=account.result_id,
            amount="1000.00",
            occurred_at=datetime(2026, 9, 1, tzinfo=UTC),
        )
    )
    pending = PendingActionStore(sessions)
    adapter = FinanceToolAdapter(finance, pending)
    yield AgentHarness(
        sessions=sessions,
        finance=finance,
        pending=pending,
        adapter=adapter,
        account_id=account.result_id,
        category_id=category.result_id,
    )
    engine.dispose()
