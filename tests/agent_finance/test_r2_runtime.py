from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import timedelta

import pytest
from sqlalchemy import select, update
from fastapi.testclient import TestClient

from wife_system.agent.application import AgentApplicationError
from wife_system.agent.models import AgentRunRecord
from wife_system.agent.application import build_agent_application
from wife_system.agent.finance_tools import FinanceToolAdapter
from wife_system.agent.pending import PendingActionStore
from wife_system.agent.providers import ScriptedModelProvider
from wife_system.agent.types import AgentRunResult, AssistantTurn, RunStatus, ToolCall
from wife_system.api.app import create_app
from wife_system.finance.db import Base, make_engine, make_session_factory
from wife_system.finance.schemas import CreateAccount, CreateCategory
from wife_system.finance.service import FinanceService, IdempotencyKeys
from wife_system.host.auth.service import AuthSecrets
from wife_system.host.auth.models import AppUser
from wife_system.host.factory import build_host_runtime
from wife_system.host.registry import ModuleDefinition, ModuleRegistry
from wife_system.host.state import HostKeys
from wife_system.modules.daily_finance import daily_finance_definition

from .conftest import ACTOR_ID, CONVERSATION_ID, RECEIVED_AT, AgentHarness
from .test_vertical_slice import start_candidate


def _versioned_host_agent(tmp_path, provider):
    engine = make_engine(f"sqlite+pysqlite:///{tmp_path / 'versioned-host.db'}")
    Base.metadata.create_all(engine)
    sessions = make_session_factory(engine)
    finance = FinanceService(
        sessions,
        IdempotencyKeys({1: b"versioned-finance-key"}),
        user_id=ACTOR_ID,
    )
    pending = PendingActionStore(sessions)
    adapter = FinanceToolAdapter(finance, pending)
    runtime = build_host_runtime(
        sessions=sessions,
        finance_adapter=adapter,
        auth_secrets=AuthSecrets(
            bootstrap_token=b"b" * 32,
            binding_hmac_key=b"h" * 32,
            adapter_token=b"a" * 32,
        ),
        state_keys=HostKeys({1: b"s" * 32}),
        cursor_secret=b"c" * 32,
    )
    with sessions() as session, session.begin():
        session.add(
            AppUser(
                id=ACTOR_ID,
                handle="version_owner",
                status="active",
                bootstrap_marker=None,
            )
        )
    base = daily_finance_definition(adapter)
    profile = base.manifest.profiles[0].model_copy(update={"version": "1.4.0"})
    manifest = base.manifest.model_copy(
        update={"version": "1.8.0", "profiles": (profile,)}
    )
    registry = ModuleRegistry(
        [ModuleDefinition(manifest=manifest, tools=base.tools)], sessions=sessions
    )
    runtime = replace(runtime, registry=registry)
    conversation, _ = runtime.conversations.create(
        user_id=ACTOR_ID,
        channel="api_test",
        module_id="daily_finance",
        profile_id="daily_finance.assistant@1",
        idempotency_key="versioned-conversation",
        now=RECEIVED_AT,
    )
    agent = build_agent_application(
        sessions=sessions,
        finance=finance,
        provider=provider,
        digest_key=b"versioned-agent-digest-key",
        host_runtime=runtime,
    )
    return engine, sessions, finance, runtime, agent, conversation


def test_start_persists_distinct_module_and_profile_versions(tmp_path) -> None:
    provider = ScriptedModelProvider([AssistantTurn(content="完成")])
    engine, sessions, _, _, agent, conversation = _versioned_host_agent(
        tmp_path, provider
    )
    try:
        result = agent.start(
            actor_id=ACTOR_ID,
            conversation_id=conversation.id,
            client_event_id=uuid.uuid4(),
            message="检查版本",
            permissions=frozenset({"finance:read"}),
            received_at=RECEIVED_AT,
            channel="api_test",
        )
        assert result.status == "success"
        with sessions() as session:
            row = session.scalar(select(AgentRunRecord))
            assert row is not None
            assert row.module_version == "1.8.0"
            assert row.profile_version == "1.4.0"
    finally:
        engine.dispose()


@pytest.mark.parametrize("drift_field", ["module_version", "profile_version"])
def test_expired_takeover_rejects_module_or_profile_version_drift_before_provider(
    tmp_path, drift_field: str
) -> None:
    class CrashProvider:
        calls = 0

        def complete(self, messages, tools, timeout_seconds):
            del messages, tools, timeout_seconds
            self.calls += 1
            raise RuntimeError("virtual crash")

    crash = CrashProvider()
    engine, sessions, finance, runtime, agent, conversation = _versioned_host_agent(
        tmp_path, crash
    )
    event_id = uuid.uuid4()
    try:
        with pytest.raises(RuntimeError, match="virtual crash"):
            agent.start(
                actor_id=ACTOR_ID,
                conversation_id=conversation.id,
                client_event_id=event_id,
                message="恢复版本测试",
                permissions=frozenset({"finance:read"}),
                received_at=RECEIVED_AT,
                channel="api_test",
            )
        assert crash.calls == 1
        with sessions() as session, session.begin():
            row = session.scalar(select(AgentRunRecord))
            assert row is not None
            run_id = row.id
            setattr(row, drift_field, "1.9.0")
            row.lease_expires_at = RECEIVED_AT - timedelta(seconds=1)

        class CountingProvider:
            calls = 0

            def complete(self, messages, tools, timeout_seconds):
                del messages, tools, timeout_seconds
                self.calls += 1
                return AssistantTurn(content="不应调用")

        recovered_provider = CountingProvider()
        recovered = build_agent_application(
            sessions=sessions,
            finance=finance,
            provider=recovered_provider,
            digest_key=b"versioned-agent-digest-key",
            host_runtime=runtime,
        )
        with pytest.raises(AgentApplicationError, match="profile_changed") as captured:
            recovered.start(
                actor_id=ACTOR_ID,
                conversation_id=conversation.id,
                client_event_id=event_id,
                message="恢复版本测试",
                permissions=frozenset({"finance:read"}),
                received_at=RECEIVED_AT,
                channel="api_test",
            )
        assert captured.value.status_code == 409
        assert recovered_provider.calls == 0
        assert finance.list_transactions() == []
        with sessions() as session:
            row = session.get(AgentRunRecord, run_id)
            assert row is not None and row.status == "running" and row.attempt_no == 2
    finally:
        engine.dispose()


def test_cancel_is_terminal_cancelled_and_never_posts(harness: AgentHarness) -> None:
    application, _, candidate = start_candidate(harness)
    cancelled = application.resume(
        candidate.run_id,
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        action="cancel",
        permissions=frozenset({"finance:write"}),
        now=RECEIVED_AT,
    )
    assert cancelled.status == "cancelled"
    assert application.get(
        candidate.run_id,
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
    ).status == "cancelled"
    assert not [row for row in harness.finance.list_transactions() if row.kind == "expense"]


def test_active_commit_owner_blocks_second_confirm_and_cancel(
    harness: AgentHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    application, _, candidate = start_candidate(harness)

    def unavailable(command):
        del command
        from wife_system.finance import FinanceError

        raise FinanceError("database_unavailable")

    monkeypatch.setattr(harness.finance, "record_expense", unavailable)
    first = application.resume(
        candidate.run_id,
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        action="confirm",
        permissions=frozenset({"finance:write"}),
        confirmation_code=candidate.result["confirmation_code"],
        now=RECEIVED_AT,
    )
    assert first.status == "paused" and first.pause_reason == "committing"
    for action in ("confirm", "cancel"):
        with pytest.raises(AgentApplicationError, match="commit_in_progress") as captured:
            application.resume(
                candidate.run_id,
                actor_id=ACTOR_ID,
                conversation_id=CONVERSATION_ID,
                action=action,
                permissions=frozenset({"finance:write"}),
                confirmation_code=candidate.result["confirmation_code"],
                now=RECEIVED_AT + timedelta(seconds=30),
            )
        assert captured.value.retryable
    assert not [row for row in harness.finance.list_transactions() if row.kind == "expense"]


def test_expired_run_takeover_executes_and_old_attempt_cannot_save(
    harness: AgentHarness,
) -> None:
    class CrashProvider:
        def complete(self, messages, tools, timeout_seconds):
            del messages, tools, timeout_seconds
            raise RuntimeError("virtual crash")

    event_id = uuid.uuid4()
    crashed = harness.application(CrashProvider())
    with pytest.raises(RuntimeError, match="virtual crash"):
        crashed.start(
            actor_id=ACTOR_ID,
            conversation_id=CONVERSATION_ID,
            client_event_id=event_id,
            message="继续执行",
            permissions=frozenset({"finance:read"}),
            received_at=RECEIVED_AT,
        )
    with harness.sessions() as session, session.begin():
        row = session.scalar(select(AgentRunRecord))
        assert row is not None and row.attempt_no == 1 and row.status == "running"
        run_id = row.id
        session.execute(
            update(AgentRunRecord)
            .where(AgentRunRecord.id == run_id)
            .values(lease_expires_at=RECEIVED_AT - timedelta(seconds=1))
        )

    recovered_app = harness.application(
        ScriptedModelProvider([AssistantTurn(content="恢复完成")])
    )
    recovered = recovered_app.start(
        actor_id=ACTOR_ID,
        conversation_id=CONVERSATION_ID,
        client_event_id=event_id,
        message="继续执行",
        permissions=frozenset({"finance:read"}),
        received_at=RECEIVED_AT,
    )
    assert recovered.status == "success" and recovered.answer == "恢复完成"
    with harness.sessions() as session:
        row = session.get(AgentRunRecord, run_id)
        assert row is not None and row.attempt_no == 2
    with pytest.raises(AgentApplicationError, match="run_lease_lost"):
        crashed._save_result(
            run_id,
            AgentRunResult(
                request_id=str(run_id),
                status=RunStatus.SUCCESS,
                answer="stale",
                events=(),
            ),
            user_id=ACTOR_ID,
            attempt_no=1,
            now=RECEIVED_AT,
        )


def test_api_compiles_host_prompt_and_bound_tool_to_pending(tmp_path) -> None:
    engine = make_engine(f"sqlite+pysqlite:///{tmp_path / 'host-agent.db'}")
    Base.metadata.create_all(engine)
    sessions = make_session_factory(engine)
    keys = IdempotencyKeys({1: b"finance-r2-host-key"})
    finance = FinanceService(sessions, keys)
    pending = PendingActionStore(sessions)
    adapter = FinanceToolAdapter(finance, pending)
    runtime = build_host_runtime(
        sessions=sessions,
        finance_adapter=adapter,
        auth_secrets=AuthSecrets(
            bootstrap_token=b"b" * 32,
            binding_hmac_key=b"h" * 32,
            adapter_token=b"a" * 32,
        ),
        state_keys=HostKeys({1: b"s" * 32}),
        cursor_secret=b"c" * 32,
    )
    runtime.auth.ensure_pending_owner(now=RECEIVED_AT)

    captured = {}

    class Provider:
        def complete(self, messages, tools, timeout_seconds):
            captured["messages"] = tuple(messages)
            captured["tools"] = tuple(tools)
            del timeout_seconds
            return AssistantTurn(
                tool_calls=(
                    ToolCall(
                        id="host-expense",
                        name="finance_record_expense",
                        arguments={
                            "amount": "18.00",
                            "account_id": str(captured["account_id"]),
                            "category_id": str(captured["category_id"]),
                        },
                    ),
                )
            )

    provider = Provider()
    agent = build_agent_application(
        sessions=sessions,
        finance=finance,
        provider=provider,
        digest_key=b"agent-r2-host-digest-key-32bytes",
        host_runtime=runtime,
    )
    app = create_app(host_runtime=runtime, agent_application=agent)
    with TestClient(app, client=("127.0.0.1", 50000)) as client:
        initialized = client.post(
            "/api/v1/auth/initialize",
            headers={"Idempotency-Key": "r2-init", "X-Bootstrap-Token": "b" * 32},
            json={"handle": "owner", "password": "correct horse battery staple"},
        )
        assert initialized.status_code == 200
        login = client.post(
            "/api/v1/auth/login",
            json={
                "handle": "owner",
                "password": "correct horse battery staple",
                "client_fingerprint": "r2-client",
                "device_name": "pytest",
                "platform": "api_test",
            },
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        account = finance.create_account(
            CreateAccount(source_system="test", source_event_id="r2-account", name="日常账户")
        )
        category = finance.create_category(
            CreateCategory(
                source_system="test",
                source_event_id="r2-category",
                kind="expense",
                name="餐饮",
            )
        )
        captured["account_id"] = account.result_id
        captured["category_id"] = category.result_id
        conversation = client.post(
            "/api/v1/conversations",
            headers={**headers, "Idempotency-Key": "r2-conversation"},
            json={
                "channel": "api_test",
                "module_id": "daily_finance",
                "profile_id": "daily_finance.assistant@1",
            },
        )
        response = client.post(
            "/api/v1/agent/runs",
            headers=headers,
            json={
                "conversation_id": conversation.json()["id"],
                "client_event_id": str(uuid.uuid4()),
                "message": "午饭 18 元",
            },
        )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "paused"
    messages = captured["messages"]
    assert messages[0].content.startswith("Host safety rules:")
    assert "daily finance" in messages[1].content.casefold() or messages[1].content
    assert messages[2].content.startswith("Trusted Host context:")
    assert messages[-1].role == "user" and messages[-1].content == "午饭 18 元"
    assert any(schema["function"]["name"] == "finance_record_expense" for schema in captured["tools"])
    engine.dispose()
