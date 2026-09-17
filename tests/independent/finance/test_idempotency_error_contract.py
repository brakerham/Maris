from __future__ import annotations

import json
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from wife_system.finance.db import Base, make_engine, make_session_factory
from wife_system.finance.errors import FinanceError
from wife_system.finance.models import Account, AuditEvent, CommandReceipt, FinancialTransaction
from wife_system.finance.schemas import CreateAccount, RecordExpense
from wife_system.finance.service import FinanceService, IdempotencyKeys

from conftest import WHEN


def _expense_command(virtual, account, category, event: str, amount: str = "18.00") -> RecordExpense:
    return RecordExpense(
        source_system="p1-c4",
        source_event_id=event,
        account_id=account,
        category_id=category,
        amount=amount,
        occurred_at=WHEN,
    )


@pytest.mark.c3("IDM-01", "IDM-02", "ERR-03")
def test_sequential_replay_and_conflicting_payload_have_one_side_effect(service, virtual) -> None:
    account = virtual.account()
    category = virtual.category("expense", "虚拟幂等分类")
    first = service.record_expense(_expense_command(virtual, account, category, "virtual-same-key"))
    replay = service.record_expense(
        _expense_command(virtual, account, category, "virtual-same-key", amount="18.0")
    )
    assert replay.replayed and replay.result_id == first.result_id

    with pytest.raises(FinanceError) as raised:
        service.record_expense(
            _expense_command(virtual, account, category, "virtual-same-key", amount="16.00")
        )
    assert raised.value.code == "duplicate_request_conflict"
    assert service.account_balance(account) == -1800
    with service._sessions() as session:
        assert session.scalar(
            select(func.count()).select_from(FinancialTransaction).where(
                FinancialTransaction.kind == "expense"
            )
        ) == 1


@pytest.mark.c3("IDM-01", "IDM-02", "ERR-06")
def test_hmac_receipt_stores_no_raw_source_id_or_payload(service, virtual) -> None:
    canary = "PRIVATE_PAYLOAD_CANARY_SOURCE"
    account = virtual.account()
    category = virtual.category("expense", "虚拟隐私分类")
    service.record_expense(_expense_command(virtual, account, category, canary))
    with service._sessions() as session:
        receipt = session.scalar(
            select(CommandReceipt).where(CommandReceipt.command_name == "record_expense")
        )
        assert receipt is not None
        serialized = "|".join(
            [receipt.key_digest, receipt.request_fingerprint, receipt.result_json or ""]
        )
        assert canary not in serialized
        assert len(receipt.key_digest) == 64
        assert len(receipt.request_fingerprint) == 64
        audits = session.scalars(
            select(AuditEvent).where(AuditEvent.command_receipt_id == receipt.id)
        ).all()
        assert len(audits) == 1
        assert canary not in "|".join(
            str(value)
            for audit in audits
            for value in (
                audit.entity_type,
                audit.entity_id,
                audit.action,
                audit.reason,
            )
        )


@pytest.mark.c3("IDM-05", "IDM-06")
def test_different_keys_are_distinct_and_event_time_controls_order(service, virtual) -> None:
    account = virtual.account()
    category = virtual.category("expense", "虚拟乱序分类")
    late = RecordExpense(
        source_system="p1-c4",
        source_event_id="virtual-late-arrives-first",
        account_id=account,
        category_id=category,
        amount="1.00",
        occurred_at=WHEN.replace(day=20),
    )
    early = RecordExpense(
        source_system="p1-c4",
        source_event_id="virtual-early-arrives-second",
        account_id=account,
        category_id=category,
        amount="1.00",
        occurred_at=WHEN.replace(day=10),
    )
    late_result = service.record_expense(late)
    early_result = service.record_expense(early)
    rows = service.list_transactions()
    assert [row.id for row in rows] == [early_result.result_id, late_result.result_id]
    assert service.account_balance(account) == -200


@pytest.mark.c3("IDM-03", "IDM-05", "MIG-09")
def test_sqlite_two_connection_same_key_is_single_effect_and_different_keys_both_commit(
    service, virtual
) -> None:
    account = virtual.account()
    category = virtual.category("expense", "虚拟 SQLite 并发")
    barrier = Barrier(2)

    def submit(event: str, amount: str = "1.00"):
        barrier.wait(timeout=5)
        try:
            return service.record_expense(_expense_command(virtual, account, category, event, amount))
        except FinanceError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: submit("virtual-concurrent-same"), range(2)))
    successes = [row for row in outcomes if not isinstance(row, FinanceError)]
    errors = [row for row in outcomes if isinstance(row, FinanceError)]
    assert len(successes) >= 1
    assert all(error.code in {"concurrent_modification", "database_unavailable"} for error in errors)
    assert len({row.result_id for row in successes}) == 1
    assert service.account_balance(account) == -100

    barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(
            pool.map(
                lambda event: submit(event),
                ("virtual-concurrent-a", "virtual-concurrent-b"),
            )
        )
    assert all(not isinstance(row, FinanceError) for row in outcomes)
    assert service.account_balance(account) == -300


@pytest.mark.c3("IDM-04", "MIG-09")
def test_sqlite_concurrent_same_key_different_payload_has_one_winner(service, virtual) -> None:
    account = virtual.account()
    category = virtual.category("expense", "虚拟 SQLite 冲突")
    barrier = Barrier(2)

    def submit(amount: str):
        barrier.wait(timeout=5)
        try:
            return service.record_expense(
                _expense_command(virtual, account, category, "virtual-concurrent-conflict", amount)
            )
        except FinanceError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(submit, ("1.00", "2.00")))
    successes = [row for row in outcomes if not isinstance(row, FinanceError)]
    errors = [row for row in outcomes if isinstance(row, FinanceError)]
    assert len(successes) == 1
    assert len(errors) == 1
    assert errors[0].code in {"duplicate_request_conflict", "database_unavailable"}
    assert service.account_balance(account) in {-100, -200}
    with service._sessions() as session:
        assert session.scalar(
            select(func.count()).select_from(FinancialTransaction).where(
                FinancialTransaction.kind == "expense"
            )
        ) == 1


@pytest.mark.c3("ERR-01", "ERR-02", "ERR-04")
def test_database_constraints_and_business_validation_form_two_defense_layers(
    service, virtual
) -> None:
    account = virtual.account()
    category = virtual.category("expense", "虚拟约束分类")
    with pytest.raises(FinanceError) as raised:
        service.record_expense(
            RecordExpense(
                **virtual.source(),
                account_id=uuid.uuid4(),
                category_id=category,
                amount="1.00",
                occurred_at=WHEN,
            )
        )
    assert raised.value.code == "not_found"

    with service._sessions() as session, session.begin():
        session.add(Account(name="虚拟非法币种", currency="USD"))
        with pytest.raises(IntegrityError):
            session.flush()

    with service._sessions() as session:
        assert session.get(Account, account) is not None
        assert session.scalar(select(func.count()).select_from(Account)) == 1


@pytest.mark.c3("ERR-03", "ERR-06")
def test_constraint_error_is_privacy_safe_and_does_not_expose_driver_text(
    service, caplog
) -> None:
    canary = "PRIVATE_PAYLOAD_CANARY_CONSTRAINT"
    command = CreateAccount(
        source_system="p1-c4",
        source_event_id=canary,
        name="虚拟敏感账户",
    )

    def invalid_worker(session, receipt):
        row = Account(name=canary, currency="USD")
        session.add(row)
        session.flush()
        raise AssertionError("unreachable")

    with caplog.at_level(logging.ERROR, logger="wife_system.finance"):
        with pytest.raises(FinanceError) as raised:
            service._execute(command, "virtual_constraint_failure", {"name": canary}, invalid_worker)
    assert raised.value.code == "persistence_error"
    assert canary not in str(raised.value)
    assert canary not in caplog.text
    event = json.loads(caplog.records[-1].message)
    assert set(event) == {"event", "code", "command", "correlation_id"}


@pytest.mark.c3("ERR-06")
def test_database_unavailable_error_and_log_are_retryable_and_private(caplog) -> None:
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    service = FinanceService(
        make_session_factory(engine),
        IdempotencyKeys({1: b"p1-c4-private-virtual-secret"}),
    )
    engine.dispose()
    canary = "PRIVATE_PAYLOAD_CANARY_DATABASE"
    with caplog.at_level(logging.ERROR, logger="wife_system.finance"):
        with pytest.raises(FinanceError) as raised:
            service.create_account(
                CreateAccount(
                    source_system="p1-c4",
                    source_event_id=canary,
                    name="虚拟隐私账户",
                )
            )
    assert raised.value.code == "database_unavailable"
    assert raised.value.retryable
    assert canary not in caplog.text
    assert canary not in str(raised.value)


@pytest.mark.c3("ERR-06")
def test_success_validation_conflict_and_unhandled_paths_do_not_log_private_payload(
    service, virtual, caplog
) -> None:
    canary = "PRIVATE_PAYLOAD_CANARY_ALL_PATHS"
    account = virtual.account()
    category = virtual.category("expense", "虚拟日志隐私")
    command = _expense_command(virtual, account, category, canary)
    with caplog.at_level(logging.DEBUG, logger="wife_system.finance"):
        service.record_expense(command)
        with pytest.raises(FinanceError):
            service.record_expense(command.model_copy(update={"amount": "2.00"}))
        with pytest.raises(RuntimeError):
            service._execute(
                CreateAccount(
                    source_system="p1-c4", source_event_id=canary + "-runtime", name="虚拟账户"
                ),
                "virtual_unhandled",
                {"canary": canary},
                lambda session, receipt: (_ for _ in ()).throw(RuntimeError("virtual failure")),
            )
    assert canary not in caplog.text
