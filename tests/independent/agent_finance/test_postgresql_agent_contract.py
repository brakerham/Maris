from __future__ import annotations

import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, inspect, select, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from wife_system.agent.application import AgentApplication
from wife_system.agent.finance_tools import FinanceToolAdapter, finance_registry
from wife_system.agent.loop import AgentRunner
from wife_system.agent.models import AgentRunRecord, PendingActionRecord
from wife_system.agent.pending import PendingActionStore
from wife_system.agent.providers import ModelProvider, ScriptedModelProvider
from wife_system.agent.types import AssistantTurn, ToolCall
from wife_system.finance.db import make_engine, make_session_factory
from wife_system.finance.models import Account, Category, CommandReceipt, FinancialTransaction
from wife_system.finance.service import FinanceService, IdempotencyKeys
from wife_system.host.auth.models import AppUser
from wife_system.host.state_models import ConversationRecord


ACTOR = uuid.UUID("c7000000-0000-0000-0000-000000000001")
CONVERSATION = uuid.UUID("c7000000-0000-0000-0000-000000000002")
NOW = datetime(2026, 9, 17, 0, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def pg_clock(independent_clock):
    """Align the shared controllable P2 clock with this PG module's frozen NOW."""
    independent_clock.current = NOW
    return independent_clock


def migration_config(url: str) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


@dataclass
class PgHarness:
    engine: Engine
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
            digest_key=b"pg-c7-agent-digest-key",
        )


@pytest.fixture
def pg_harness() -> PgHarness:
    raw_url = os.getenv("FINANCE_TEST_POSTGRES_URL")
    if not raw_url:
        pytest.skip("FINANCE_TEST_POSTGRES_URL is required for PG-C7")
    parsed = make_url(raw_url)
    if parsed.get_backend_name() != "postgresql":
        pytest.skip("PG-C7 requires a PostgreSQL URL")

    schema = f"p2_c7_{uuid.uuid4().hex}"
    admin = make_engine(raw_url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    query = dict(parsed.query)
    query["options"] = f"-csearch_path={schema},public"
    isolated_url = parsed.set(query=query).render_as_string(hide_password=False)
    engine: Engine | None = None
    try:
        command.upgrade(migration_config(isolated_url), "head")
        engine = make_engine(isolated_url)
        sessions = make_session_factory(engine)
        with sessions() as session, session.begin():
            session.add(AppUser(id=ACTOR, handle="pg_c7_owner", status="active"))
            session.add(ConversationRecord(
                id=CONVERSATION,
                user_id=ACTOR,
                channel="api_test",
                module_id="daily_finance",
                profile_id="daily_finance.assistant@1",
                created_at=NOW,
            ))
            session.flush()
            account = Account(user_id=ACTOR, name="PG-C7 虚拟账户", currency="CNY", version_id=1)
            category = Category(
                user_id=ACTOR,
                kind="expense",
                name="PG-C7 虚拟餐饮",
                name_normalized="pg-c7 虚拟餐饮",
                version_id=1,
            )
            session.add_all([account, category])
            session.flush()
            account_id, category_id = account.id, category.id
        finance = FinanceService(
            sessions,
            IdempotencyKeys({1: b"pg-c7-virtual-finance-key"}),
            user_id=ACTOR,
        )
        pending = PendingActionStore(sessions)
        yield PgHarness(
            engine=engine,
            sessions=sessions,
            finance=finance,
            pending=pending,
            adapter=FinanceToolAdapter(finance, pending),
            account_id=account_id,
            category_id=category_id,
        )
    finally:
        if engine is not None:
            engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin.dispose()


def expense_turn(harness: PgHarness) -> AssistantTurn:
    return AssistantTurn(
        tool_calls=(
            ToolCall(
                id="pg-expense",
                name="finance_record_expense",
                arguments={
                    "amount": "18.00",
                    "account_id": str(harness.account_id),
                    "category_id": str(harness.category_id),
                },
            ),
        )
    )


def start_candidate(harness: PgHarness):
    provider = ScriptedModelProvider([expense_turn(harness)])
    application = harness.app(provider)
    result = application.start(
        actor_id=ACTOR,
        conversation_id=CONVERSATION,
        client_event_id=uuid.uuid4(),
        message="PG-C7 虚拟午饭 18 元",
        permissions=frozenset({"finance:read", "finance:write"}),
        received_at=NOW,
    )
    return application, result


def test_postgresql_p2_head_has_agent_tables_and_constraints(pg_harness: PgHarness) -> None:
    """P2 migration and PostgreSQL persistence constraints."""
    inspector = inspect(pg_harness.engine)
    assert {"agent_run", "pending_action", "conversation", "app_user"}.issubset(
        inspector.get_table_names()
    )
    assert {"agent_run", "pending_action"}.issubset(inspector.get_table_names())
    assert pg_harness.engine.connect().scalar(text("SELECT version_num FROM alembic_version")) == "p4_host_state"
    assert {"uq_run_user_source_event", "uq_agent_run_user_id"}.issubset(
        {item["name"] for item in inspector.get_unique_constraints("agent_run")}
    )
    assert {"uq_pending_action_run_id", "uq_pending_action_confirmation_code", "uq_pending_action_user_id"}.issubset(
        {item["name"] for item in inspector.get_unique_constraints("pending_action")}
    )


def test_postgresql_concurrent_same_event_is_single_run(pg_harness: PgHarness) -> None:
    """IDM-01 on two application instances."""
    entered, release = threading.Event(), threading.Event()

    class BlockingProvider:
        calls = 0

        def complete(self, messages, tools, timeout_seconds):
            self.calls += 1
            entered.set()
            assert release.wait(10)
            return AssistantTurn(content="PG-C7 虚拟答复")

    first_provider = BlockingProvider()
    second_provider = ScriptedModelProvider([AssistantTurn(content="不应执行")])
    first_app = pg_harness.app(first_provider)
    second_app = pg_harness.app(second_provider)
    event_id = uuid.uuid4()

    def submit(app):
        return app.start(
            actor_id=ACTOR,
            conversation_id=CONVERSATION,
            client_event_id=event_id,
            message="PG-C7 同事件",
            permissions=frozenset({"finance:read"}),
            received_at=NOW,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(submit, first_app)
        assert entered.wait(10)
        second = pool.submit(submit, second_app)
        replay = second.result(20)
        release.set()
        completed = first.result(20)
    assert replay.run_id == completed.run_id
    assert replay.replayed is True and completed.status == "success"
    assert first_provider.calls == 1 and second_provider.calls == 0
    with pg_harness.sessions() as session:
        assert session.scalar(select(func.count()).select_from(AgentRunRecord)) == 1


def test_postgresql_concurrent_confirm_commits_once_and_matches_p1(pg_harness: PgHarness) -> None:
    """IDM-04..IDM-06, IDM-10, HTTP-04, P1-01..P1-05."""
    _, candidate = start_candidate(pg_harness)
    restarted = pg_harness.app(ScriptedModelProvider([]))
    code = candidate.result["confirmation_code"]

    def confirm():
        return restarted.resume(
            candidate.run_id,
            actor_id=ACTOR,
            conversation_id=CONVERSATION,
            action="confirm",
            permissions=frozenset({"finance:write"}),
            confirmation_code=code,
            now=NOW,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [future.result(20) for future in [pool.submit(confirm), pool.submit(confirm)]]
    actual = [row.model_dump(mode="json") for row in results]
    assert all(
        row.status == "success"
        and row.result is not None
        and row.result.get("status") == "committed"
        for row in results
    ), actual
    assert {row.result["result_id"] for row in results} == {results[0].result["result_id"]}
    assert sorted(row.result["replayed"] for row in results) == [False, True]
    assert pg_harness.finance.account_balance(pg_harness.account_id) == -1800
    with pg_harness.sessions() as session:
        assert session.scalar(select(func.count()).select_from(FinancialTransaction)) == 1
        assert session.scalar(select(func.count()).select_from(CommandReceipt)) == 1


def test_postgresql_commit_response_loss_recovers_same_result(
    pg_harness: PgHarness, monkeypatch: pytest.MonkeyPatch, independent_clock
) -> None:
    """IDM-08, IDM-10, DB-02, DB-03, LOOP-11."""
    application, candidate = start_candidate(pg_harness)
    original = pg_harness.pending.mark_committed
    calls = 0

    def lose_response(action_id, result, *, claim, user_id, now):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("PG-C7 simulated response loss")
        return original(action_id, result, claim=claim, user_id=user_id, now=now)

    monkeypatch.setattr(pg_harness.pending, "mark_committed", lose_response)
    with pytest.raises(RuntimeError, match="simulated response loss"):
        initial = application.resume(
            candidate.run_id,
            actor_id=ACTOR,
            conversation_id=CONVERSATION,
            action="confirm",
            permissions=frozenset({"finance:write"}),
            confirmation_code=candidate.result["confirmation_code"],
            now=NOW,
        )
        pytest.fail(
            "commit never reached the simulated response-loss point: "
            f"{initial.model_dump(mode='json')}"
        )
    recovery_time = independent_clock.advance(timedelta(seconds=61))
    recovered = pg_harness.app(ScriptedModelProvider([])).resume(
        candidate.run_id,
        actor_id=ACTOR,
        conversation_id=CONVERSATION,
        action="confirm",
        permissions=frozenset({"finance:write"}),
        confirmation_code=candidate.result["confirmation_code"],
        now=recovery_time,
    )
    assert recovered.result["status"] == "committed"
    assert recovered.result["replayed"] is True
    with pg_harness.sessions() as session:
        assert session.scalar(select(func.count()).select_from(FinancialTransaction)) == 1
        assert session.scalar(select(func.count()).select_from(PendingActionRecord)) == 1
