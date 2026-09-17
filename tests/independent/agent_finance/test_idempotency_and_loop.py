from __future__ import annotations

import json
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select

from wife_system.agent.application import AgentApplicationError
from wife_system.agent.loop import AgentRunner
from wife_system.agent.models import AgentRunRecord, PendingActionRecord
from wife_system.agent.providers import ProviderError, ProviderTimeoutError, ScriptedModelProvider
from wife_system.agent.types import AssistantTurn, ToolCall
from wife_system.tools import Tool, ToolRegistry

from conftest import ACTOR, CONVERSATION, NOW, IndependentHarness
from test_tools_and_lifecycle import expense_count, expense_turn, start_candidate


class Empty(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Indexed(BaseModel):
    model_config = ConfigDict(extra="forbid")
    index: int


def test_sequential_source_replay_conflict_and_distinct_events(ih: IndependentHarness) -> None:
    """IDM-01..IDM-03."""
    event = uuid.uuid4()
    app, provider, first = start_candidate(ih, event_id=event)
    replay = app.start(
        actor_id=ACTOR, conversation_id=CONVERSATION, client_event_id=event,
        message="虚拟午饭 18 元", permissions=frozenset({"finance:write"}), received_at=NOW,
    )
    assert replay.run_id == first.run_id and replay.replayed and provider.calls == 1
    with pytest.raises(AgentApplicationError) as conflict:
        app.start(
            actor_id=ACTOR, conversation_id=CONVERSATION, client_event_id=event,
            message="虚拟午饭 19 元", permissions=frozenset({"finance:write"}), received_at=NOW,
        )
    assert conflict.value.code == "duplicate_request_conflict"

    second_provider = ScriptedModelProvider([expense_turn(ih)])
    second = ih.app(second_provider).start(
        actor_id=ACTOR, conversation_id=CONVERSATION, client_event_id=uuid.uuid4(),
        message="虚拟午饭 18 元", permissions=frozenset({"finance:write"}), received_at=NOW,
    )
    assert second.run_id != first.run_id
    with ih.sessions() as session:
        assert session.scalar(select(func.count()).select_from(AgentRunRecord)) == 2
        assert session.scalar(select(func.count()).select_from(PendingActionRecord)) == 2


def test_model_wait_does_not_hold_database_connection(ih: IndependentHarness) -> None:
    """CTX-05."""
    entered, release = threading.Event(), threading.Event()

    class Blocking:
        def complete(self, messages, tools, timeout_seconds):
            entered.set()
            assert release.wait(5)
            return expense_turn(ih)

    app = ih.app(Blocking())
    bind = ih.sessions.kw["bind"]
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            app.start,
            actor_id=ACTOR,
            conversation_id=CONVERSATION,
            client_event_id=uuid.uuid4(),
            message="虚拟午饭 18 元",
            permissions=frozenset({"finance:write"}),
            received_at=NOW,
        )
        assert entered.wait(5)
        assert bind.pool.checkedout() == 0
        release.set()
        assert future.result(5).pause_reason == "needs_confirmation"
    assert bind.pool.checkedout() == 0

def test_concurrent_source_event_runs_model_once(ih: IndependentHarness) -> None:
    """IDM-01, IDM-06, HTTP-09."""
    entered, release = threading.Event(), threading.Event()

    class Blocking:
        calls = 0

        def complete(self, messages, tools, timeout_seconds):
            self.calls += 1
            entered.set()
            assert release.wait(5)
            return expense_turn(ih)

    provider = Blocking()
    app = ih.app(provider)
    event = uuid.uuid4()

    def submit():
        return app.start(
            actor_id=ACTOR, conversation_id=CONVERSATION, client_event_id=event,
            message="虚拟午饭 18 元", permissions=frozenset({"finance:write"}), received_at=NOW,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        one = pool.submit(submit)
        assert entered.wait(5)
        two = pool.submit(submit)
        release.set()
        results = [one.result(5), two.result(5)]
    assert provider.calls == 1 and results[0].run_id == results[1].run_id
    assert sum(result.replayed for result in results) == 1


def test_concurrent_confirm_and_restart_recovery_are_exactly_once(ih: IndependentHarness) -> None:
    """IDM-05, IDM-06, IDM-09, IDM-10, DB-02."""
    _, _, candidate = start_candidate(ih)
    code = candidate.result["confirmation_code"]
    restarted = ih.app(ScriptedModelProvider([]))

    def confirm():
        return restarted.resume(
            candidate.run_id, actor_id=ACTOR, conversation_id=CONVERSATION,
            action="confirm", permissions=frozenset({"finance:write"}),
            confirmation_code=code, now=NOW,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [future.result(5) for future in [pool.submit(confirm), pool.submit(confirm)]]
    assert {row.result["result_id"] for row in results} == {results[0].result["result_id"]}
    assert sorted(row.result["replayed"] for row in results) == [False, True]
    assert expense_count(ih) == 1
    status = restarted.get(candidate.run_id, actor_id=ACTOR, conversation_id=CONVERSATION)
    assert status.status == "success" and status.result["result_id"] == results[0].result["result_id"]


def test_retry_policy_distinguishes_transient_and_permanent(ih: IndependentHarness) -> None:
    """LOOP-01..LOOP-03."""
    class SequenceProvider:
        def __init__(self, errors):
            self.errors = list(errors)
            self.calls = 0

        def complete(self, messages, tools, timeout_seconds):
            self.calls += 1
            item = self.errors.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

    transient = SequenceProvider([ProviderTimeoutError(), AssistantTurn(content="虚拟成功")])
    result = ih.app(transient).start(
        actor_id=ACTOR, conversation_id=CONVERSATION, client_event_id=uuid.uuid4(),
        message="查询", permissions=frozenset({"finance:read"}), received_at=NOW,
    )
    assert result.status == "success" and transient.calls == 2

    exhausted = SequenceProvider([ProviderTimeoutError(), ProviderTimeoutError()])
    result = ih.app(exhausted).start(
        actor_id=ACTOR, conversation_id=CONVERSATION, client_event_id=uuid.uuid4(),
        message="查询", permissions=frozenset({"finance:read"}), received_at=NOW,
    )
    assert result.error_code == "model_timeout" and exhausted.calls == 2

    permanent = SequenceProvider([
        ProviderError("PRIVATE-CANARY", code="model_auth_failed", retryable=False)
    ])
    result = ih.app(permanent).start(
        actor_id=ACTOR, conversation_id=CONVERSATION, client_event_id=uuid.uuid4(),
        message="查询", permissions=frozenset({"finance:read"}), received_at=NOW,
    )
    assert result.error_code == "model_auth_failed" and permanent.calls == 1


@pytest.mark.parametrize(
    ("turn", "code"),
    [
        (AssistantTurn(), "empty_model_response"),
        (AssistantTurn(tool_calls=(ToolCall(id="x", name="not_registered_CANARY", arguments={}),)), "unknown_tool"),
        (AssistantTurn(tool_calls=(ToolCall(id="x", name="read", arguments={"extra": 1}),)), "invalid_tool_arguments"),
    ],
)
def test_protocol_failures_are_safe(turn: AssistantTurn, code: str) -> None:
    """LOOP-04, LOOP-05, LOOP-09, PRV-05."""
    registry = ToolRegistry([Tool("read", "read", Empty, lambda _: {"secret": "never"})])
    result = AgentRunner(provider=ScriptedModelProvider([turn]), tools=registry).run("safe", str(uuid.uuid4()))
    assert result.error_code == code
    assert "CANARY" not in (result.error_message or "")


def test_duplicate_calls_write_and_total_limits_are_deterministic() -> None:
    """IDM-07, LOOP-06..LOOP-08."""
    calls = []
    registry = ToolRegistry([
        Tool("read", "read", Empty, lambda _: calls.append("r") or {"status": "ok"}),
        Tool("write", "write", Empty, lambda _: calls.append("w") or {"status": "ok"}, is_write=True),
        Tool("indexed", "indexed", Indexed, lambda _: calls.append("i") or {"status": "ok"}),
    ])
    duplicate = AgentRunner(
        provider=ScriptedModelProvider([
            AssistantTurn(tool_calls=(ToolCall(id="same", name="read", arguments={}), ToolCall(id="same", name="read", arguments={})))
        ]), tools=registry,
    ).run("duplicate", "dup")
    assert duplicate.error_code == "duplicate_tool_call" and calls == ["r"]

    calls.clear()
    writes = AgentRunner(
        provider=ScriptedModelProvider([
            AssistantTurn(tool_calls=(ToolCall(id="w1", name="write", arguments={}), ToolCall(id="w2", name="write", arguments={})))
        ]), tools=registry,
    ).run("writes", "writes")
    assert writes.error_code in {"duplicate_tool_call", "write_limit_exceeded"} and calls == ["w"]

    calls.clear()
    turns = [AssistantTurn(tool_calls=(ToolCall(id=f"r{i}", name="indexed", arguments={"index": i}),)) for i in range(4)]
    limited = AgentRunner(provider=ScriptedModelProvider(turns), tools=registry, max_model_turns=4).run("loop", "loop")
    assert limited.error_code == "max_model_turns_exceeded" and calls == ["i"] * 4
    calls.clear()
    nine = tuple(
        ToolCall(id=f"n{i}", name="indexed", arguments={"index": i}) for i in range(9)
    )
    tool_limited = AgentRunner(
        provider=ScriptedModelProvider([AssistantTurn(tool_calls=nine)]), tools=registry
    ).run("nine", "nine")
    assert tool_limited.error_code == "tool_limit_exceeded" and calls == ["i"] * 8


def test_execution_events_and_logs_exclude_message_and_exception_canaries(
    ih: IndependentHarness, caplog: pytest.LogCaptureFixture
) -> None:
    """PRV-01, PRV-02, PRV-04, PRV-05."""
    canaries = ["RAW_MESSAGE_CANARY", "API_KEY_CANARY", "AUTH_CANARY", "C:\\PRIVATE\\PATH"]
    caplog.set_level("INFO")
    provider = ScriptedModelProvider([AssistantTurn(content="虚拟答复")])
    result = ih.app(provider).start(
        actor_id=ACTOR, conversation_id=CONVERSATION, client_event_id=uuid.uuid4(),
        message=canaries[0] + "\n{\"event\":\"forged\"}",
        permissions=frozenset({"finance:read"}), received_at=NOW,
    )
    assert result.status == "success"
    records = [record.getMessage() for record in caplog.records]
    assert records
    for raw in records:
        json.loads(raw)
    corpus = "\n".join(records) + json.dumps(result.model_dump(mode="json"))
    assert all(canary not in corpus for canary in canaries)


def test_database_failure_does_not_report_false_commit(ih: IndependentHarness, monkeypatch) -> None:
    """DB-01, DB-02, DB-04, LOOP-11."""
    app, _, candidate = start_candidate(ih)
    original = ih.finance.record_expense

    def fail(_):
        raise RuntimeError("SQL PRIVATE-CANARY C:\\PRIVATE\\db")

    monkeypatch.setattr(ih.finance, "record_expense", fail)
    failed = app.resume(
        candidate.run_id, actor_id=ACTOR, conversation_id=CONVERSATION,
        action="confirm", permissions=frozenset({"finance:write"}),
        confirmation_code=candidate.result["confirmation_code"], now=NOW,
    )
    assert failed.status == "paused" and failed.error_code == "tool_error" and expense_count(ih) == 0
    assert "PRIVATE" not in json.dumps(failed.model_dump(mode="json"))
    monkeypatch.setattr(ih.finance, "record_expense", original)
    recovered = app.resume(
        candidate.run_id, actor_id=ACTOR, conversation_id=CONVERSATION,
        action="confirm", permissions=frozenset({"finance:write"}),
        confirmation_code=candidate.result["confirmation_code"], now=NOW,
    )
    assert recovered.result["status"] == "committed" and expense_count(ih) == 1

def test_database_unavailable_before_run_has_stable_classification(
    ih: IndependentHarness, monkeypatch
) -> None:
    """DB-01, PRV-05."""
    from sqlalchemy.exc import OperationalError

    app = ih.app(ScriptedModelProvider([AssistantTurn(content="must not run")]))

    def unavailable():
        raise OperationalError("PRIVATE SQL", {}, RuntimeError("PRIVATE"))

    monkeypatch.setattr(app, "_sessions", unavailable)
    with pytest.raises(AgentApplicationError) as captured:
        app.start(
            actor_id=ACTOR, conversation_id=CONVERSATION, client_event_id=uuid.uuid4(),
            message="虚拟查询", permissions=frozenset({"finance:read"}), received_at=NOW,
        )
    assert captured.value.code == "database_unavailable"
    assert captured.value.status_code == 503 and captured.value.retryable is True
