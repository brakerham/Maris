from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from wife_system.agent.application import AgentApplicationError
from wife_system.agent.context import RunContext
from wife_system.agent.finance_tools import finance_registry
from wife_system.agent.models import AgentRunRecord, PendingActionRecord
from wife_system.agent.providers import ScriptedModelProvider
from wife_system.agent.types import AssistantTurn, ToolCall
from wife_system.finance.models import CommandReceipt
from wife_system.finance.schemas import ArchiveResource
from wife_system.tools import ToolArgumentsError

from conftest import ACTOR, CONVERSATION, NOW, IndependentHarness


def context(ih: IndependentHarness, **updates) -> RunContext:
    values = dict(
        agent_run_id=uuid.uuid4(),
        actor_id=ACTOR,
        conversation_id=CONVERSATION,
        source_system="desktop_chat",
        source_event_id=str(uuid.uuid4()),
        received_at=NOW,
        permissions=frozenset({"finance:read", "finance:write"}),
        user_message="虚拟午饭 18 元",
    )
    values.update(updates)
    return RunContext(**values)


def expense_turn(ih: IndependentHarness, **arguments) -> AssistantTurn:
    values = {
        "amount": "18.00",
        "account_id": str(ih.account_id),
        "category_id": str(ih.category_id),
    }
    values.update(arguments)
    return AssistantTurn(
        tool_calls=(ToolCall(id=str(uuid.uuid4()), name="finance_record_expense", arguments=values),)
    )


def start_candidate(
    ih: IndependentHarness,
    *,
    message: str = "虚拟午饭 18 元",
    event_id: uuid.UUID | None = None,
    turn: AssistantTurn | None = None,
):
    provider = ScriptedModelProvider([turn or expense_turn(ih)])
    app = ih.app(provider)
    result = app.start(
        actor_id=ACTOR,
        conversation_id=CONVERSATION,
        client_event_id=event_id or uuid.uuid4(),
        message=message,
        permissions=frozenset({"finance:read", "finance:write"}),
        received_at=NOW,
    )
    return app, provider, result


def expense_count(ih: IndependentHarness) -> int:
    return sum(row.kind == "expense" for row in ih.finance.list_transactions())


def test_schema_hides_context_and_all_tools_forbid_context_override(ih: IndependentHarness) -> None:
    """CTX-01, CTX-02, QRY-06, ACT-10."""
    registry = finance_registry(ih.adapter)
    ctx = context(ih)
    encoded = json.dumps(registry.schemas(ctx), sort_keys=True)
    forbidden = {
        "agent_run_id", "actor_id", "conversation_id", "source_system",
        "source_event_id", "received_at", "permissions", "approval_grant_id",
        "pending_action_id", "confirmed",
    }
    assert forbidden.isdisjoint(encoded.split('"'))
    for schema in registry.schemas(ctx):
        name = schema["function"]["name"]
        with pytest.raises(ToolArgumentsError):
            registry.invoke(name, {"actor_id": str(uuid.uuid4())}, ctx)


def test_context_rejects_naive_time_and_is_immutable(ih: IndependentHarness) -> None:
    """CTX-01, CTX-04."""
    with pytest.raises(ValueError):
        context(ih, received_at=datetime(2026, 9, 16, 12, 0))
    trusted = context(ih)
    with pytest.raises(Exception):
        trusted.actor_id = uuid.uuid4()  # type: ignore[misc]


def test_five_queries_match_p1_and_enforce_bounds(ih: IndependentHarness) -> None:
    """QRY-01..QRY-05, P1-02..P1-04."""
    registry = finance_registry(ih.adapter)
    ctx = context(ih)
    accounts = registry.invoke("finance_list_accounts", {}, ctx)
    categories = registry.invoke("finance_list_categories", {"kind": "expense"}, ctx)
    balance = registry.invoke("finance_get_account_balance", {"account_id": str(ih.account_id)}, ctx)
    txs = registry.invoke("finance_list_transactions", {"limit": 1}, ctx)
    snapshot = registry.invoke("finance_get_monthly_snapshot", {"period": "2026-09"}, ctx)
    assert [item["id"] for item in accounts["items"]] == [str(row.id) for row in ih.finance.list_accounts()]
    assert [item["id"] for item in categories["items"]] == [str(row.id) for row in ih.finance.list_categories() if row.kind == "expense"]
    assert balance == {
        "status": "ok", "account_id": str(ih.account_id), "balance_minor": 100_000,
        "currency": "CNY", "as_of": NOW.isoformat().replace("+00:00", "Z"),
    }
    assert txs["truncated"] is False and len(txs["items"]) == 1
    assert snapshot["snapshot"] == ih.finance.monthly_snapshot("2026-09", NOW).model_dump(mode="json")


@pytest.mark.parametrize(
    ("name", "arguments"),
    [
        ("finance_get_account_balance", {}),
        ("finance_get_account_balance", {"account_id": "bad"}),
        ("finance_list_transactions", {"limit": 0}),
        ("finance_list_transactions", {"limit": 51}),
        ("finance_list_transactions", {"start": "2026-09-01T00:00:00", "end": "2026-09-02T00:00:00Z"}),
        ("finance_get_monthly_snapshot", {"period": "2026-13"}),
        ("finance_list_categories", {"kind": "other"}),
    ],
)
def test_query_bad_arguments_are_local(name: str, arguments: dict, ih: IndependentHarness) -> None:
    """QRY-06, LOOP-04."""
    with pytest.raises(ToolArgumentsError):
        finance_registry(ih.adapter).invoke(name, arguments, context(ih))


def test_permissions_hide_and_deny_tools_without_data_leak(ih: IndependentHarness) -> None:
    """QRY-07, LOOP-10."""
    registry = finance_registry(ih.adapter)
    ctx = context(ih, permissions=frozenset())
    assert registry.schemas(ctx) == ()
    for name, args in (
        ("finance_list_accounts", {}),
        ("finance_record_expense", {"amount": "18.00"}),
    ):
        output = registry.invoke(name, args, ctx)
        assert output == {
            "status": "error",
            "error": {"code": "permission_denied", "message": "This action is not permitted.", "retryable": False},
        }
    assert expense_count(ih) == 0


@pytest.mark.parametrize(
    ("message", "turn", "question"),
    [
        ("虚拟午饭多少钱忘了", lambda ih: expense_turn(ih, amount=None), "ask_amount"),
        ("虚拟午饭大约十几元", lambda ih: expense_turn(ih), "ask_amount"),
        ("明天计划虚拟午饭 18 元", lambda ih: expense_turn(ih), "ask_record_intent"),
    ],
)
def test_uncertain_or_planned_expense_only_creates_question(
    ih: IndependentHarness, message: str, turn, question: str
) -> None:
    """ACT-02, ACT-03, ACT-06."""
    _, _, result = start_candidate(ih, message=message, turn=turn(ih))
    assert result.status == "paused" and result.pause_reason == "needs_input"
    assert result.result["question_code"] == question
    assert expense_count(ih) == 0


@pytest.mark.parametrize(
    ("missing", "question"),
    [("account_id", "ask_account_id"), ("category_id", "ask_category_id")],
)
def test_ambiguous_reference_uses_database_choices(
    ih: IndependentHarness, missing: str, question: str
) -> None:
    """ACT-04, ACT-05."""
    _, _, result = start_candidate(
        ih,
        message="虚拟歧义引用 18 元",
        turn=expense_turn(ih, **{missing: None}),
    )
    assert result.pause_reason == "needs_input" and result.result["question_code"] == question
    expected = ih.account_id if missing == "account_id" else ih.category_id
    assert any(choice["id"] == str(expected) for choice in result.result["choices"])
    assert expense_count(ih) == 0

def test_candidate_summary_trusted_date_and_persistence_privacy(ih: IndependentHarness) -> None:
    """CTX-04, ACT-01, ACT-07, ACT-09, PRV-03."""
    model_time = "2030-01-01T00:00:00Z"
    _, _, result = start_candidate(
        ih,
        message="昨天虚拟午饭 18 元",
        turn=expense_turn(ih, occurred_at=model_time),
    )
    assert result.pause_reason == "needs_confirmation" and expense_count(ih) == 0
    summary = result.result["summary"]
    assert summary["amount"] == "18.00" and summary["currency"] == "CNY"
    assert summary["operation"] == "record_expense" and summary["candidate"]
    assert summary["occurred_at"] == "2026-09-15T15:30:00+00:00"
    with ih.sessions() as session:
        run = session.get(AgentRunRecord, result.run_id)
        pending = session.get(PendingActionRecord, result.pending_action_id)
        serialized = " ".join(str(value) for value in vars(run).values()) + pending.action_json
    assert "昨天虚拟午饭" not in serialized and model_time not in pending.action_json


def test_two_expenses_are_rejected_without_candidate(ih: IndependentHarness) -> None:
    """ACT-08."""
    _, _, result = start_candidate(ih, message="虚拟午饭 18 元，虚拟打车 12 元")
    assert result.status == "error" and result.error_code == "multiple_expenses_unsupported"
    with ih.sessions() as session:
        assert session.scalar(select(func.count()).select_from(PendingActionRecord)) == 0
    assert expense_count(ih) == 0


def test_supplement_cancel_and_confirm_after_cancel(ih: IndependentHarness) -> None:
    """ACT-11, ACT-12."""
    app, _, first = start_candidate(ih, turn=expense_turn(ih, account_id=None, category_id=None))
    updated = app.resume(
        first.run_id, actor_id=ACTOR, conversation_id=CONVERSATION,
        action="provide_input", permissions=frozenset({"finance:write"}),
        values={"account_id": str(ih.account_id), "category_id": str(ih.category_id)}, now=NOW,
    )
    assert updated.pending_action_id == first.pending_action_id
    assert updated.pause_reason == "needs_confirmation"
    cancelled = app.resume(
        first.run_id, actor_id=ACTOR, conversation_id=CONVERSATION,
        action="cancel", permissions=frozenset({"finance:write"}), now=NOW,
    )
    assert cancelled.result == {"status": "cancelled"}
    with pytest.raises(AgentApplicationError) as exc:
        app.resume(
            first.run_id, actor_id=ACTOR, conversation_id=CONVERSATION,
            action="confirm", permissions=frozenset({"finance:write"}),
            confirmation_code=updated.result["confirmation_code"], now=NOW,
        )
    assert exc.value.code == "pending_action_cancelled"
    assert expense_count(ih) == 0


def test_expiry_identity_and_stale_resource_never_commit(ih: IndependentHarness) -> None:
    """ACT-13..ACT-16, P1-06."""
    app, _, candidate = start_candidate(ih)
    code = candidate.result["confirmation_code"]
    with pytest.raises(AgentApplicationError) as foreign:
        app.resume(
            candidate.run_id, actor_id=uuid.uuid4(), conversation_id=CONVERSATION,
            action="confirm", permissions=frozenset({"finance:write"}), confirmation_code=code, now=NOW,
        )
    assert foreign.value.code == "pending_action_not_found"
    ih.finance.archive_category(
        ArchiveResource(
            source_system="p2-c6", source_event_id="archive", resource_id=ih.category_id,
            expected_version=1, reason="virtual stale check",
        )
    )
    with pytest.raises(AgentApplicationError) as stale:
        app.resume(
            candidate.run_id, actor_id=ACTOR, conversation_id=CONVERSATION,
            action="confirm", permissions=frozenset({"finance:write"}), confirmation_code=code, now=NOW,
        )
    assert stale.value.code == "pending_action_stale" and expense_count(ih) == 0

    _, _, old = start_candidate(ih, event_id=uuid.uuid4(), turn=expense_turn(ih, category_id=None))
    with pytest.raises(AgentApplicationError) as expired:
        app.resume(
            old.run_id, actor_id=ACTOR, conversation_id=CONVERSATION,
            action="provide_input", permissions=frozenset({"finance:write"}), values={},
            now=NOW + timedelta(hours=24),
        )
    assert expired.value.code == "pending_action_expired"


def test_active_resource_version_change_invalidates_candidate(ih: IndependentHarness) -> None:
    """ACT-15."""
    from sqlalchemy import update
    from wife_system.finance.models import Category

    app, _, candidate = start_candidate(ih)
    with ih.sessions() as session, session.begin():
        session.execute(
            update(Category).where(Category.id == ih.category_id).values(version_id=2)
        )
    with pytest.raises(AgentApplicationError) as stale:
        app.resume(
            candidate.run_id, actor_id=ACTOR, conversation_id=CONVERSATION,
            action="confirm", permissions=frozenset({"finance:write"}),
            confirmation_code=candidate.result["confirmation_code"], now=NOW,
        )
    assert stale.value.code == "pending_action_stale" and expense_count(ih) == 0

def test_confirmation_just_before_expiry_is_allowed(ih: IndependentHarness) -> None:
    """ACT-13."""
    app, _, candidate = start_candidate(ih)
    committed = app.resume(
        candidate.run_id, actor_id=ACTOR, conversation_id=CONVERSATION,
        action="confirm", permissions=frozenset({"finance:write"}),
        confirmation_code=candidate.result["confirmation_code"],
        now=NOW + timedelta(hours=24) - timedelta(microseconds=1),
    )
    assert committed.result["status"] == "committed" and expense_count(ih) == 1

def test_commit_replay_receipt_balance_and_result_are_single_source(ih: IndependentHarness) -> None:
    """IDM-04, IDM-05, IDM-10, P1-01..P1-05."""
    app, provider, candidate = start_candidate(ih)
    code = candidate.result["confirmation_code"]
    first = app.resume(
        candidate.run_id, actor_id=ACTOR, conversation_id=CONVERSATION,
        action="confirm", permissions=frozenset({"finance:write"}), confirmation_code=code, now=NOW,
    )
    restarted = ih.app(ScriptedModelProvider([]))
    replay = restarted.resume(
        candidate.run_id, actor_id=ACTOR, conversation_id=CONVERSATION,
        action="confirm", permissions=frozenset({"finance:write"}), confirmation_code=code, now=NOW,
    )
    assert provider.calls == 1
    assert first.result["amount_minor"] == 1800 and first.result["currency"] == "CNY"
    assert replay.result["result_id"] == first.result["result_id"] and replay.result["replayed"] is True
    assert expense_count(ih) == 1 and ih.finance.account_balance(ih.account_id) == 98_200
    with ih.sessions() as session:
        receipts = session.scalars(
            select(CommandReceipt).where(CommandReceipt.result_id == uuid.UUID(first.result["result_id"]))
        ).all()
    assert len(receipts) == 1
    assert receipts[0].key_digest and len(receipts[0].key_digest) == 64
    assert receipts[0].source_system == "desktop_chat"
