from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from pydantic import ValidationError
from sqlalchemy import func, inspect, select

from wife_system.finance.errors import FinanceError
from wife_system.finance.models import AuditEvent, CommandReceipt, FinancialTransaction, TransactionEntry
from wife_system.finance.schemas import (
    ArchiveResource,
    RecordExpense,
    RecordIncome,
    RecordOpeningBalance,
    RecordReversal,
    RecordTransfer,
)
from wife_system.finance.service import FinanceService

from conftest import WHEN


def _counts(service) -> tuple[int, int, int, int]:
    with service._sessions() as session:
        return (
            int(session.scalar(select(func.count()).select_from(CommandReceipt)) or 0),
            int(session.scalar(select(func.count()).select_from(FinancialTransaction)) or 0),
            int(session.scalar(select(func.count()).select_from(TransactionEntry)) or 0),
            int(session.scalar(select(func.count()).select_from(AuditEvent)) or 0),
        )


@pytest.mark.c3("LED-01", "LED-02", "LED-06", "LED-09", "LED-10")
def test_income_expense_opening_and_negative_balance_are_ledger_derived(service, virtual, sqlite_engine) -> None:
    account = virtual.account("虚拟钱包")
    income_category = virtual.category("income", "虚拟工资")
    expense_category = virtual.category("expense", "虚拟餐食")

    service.record_opening_balance(
        RecordOpeningBalance(**virtual.source(), account_id=account, amount="500.00", occurred_at=WHEN)
    )
    service.record_income(
        RecordIncome(
            **virtual.source(), account_id=account, category_id=income_category, amount="1500.00", occurred_at=WHEN
        )
    )
    service.record_expense(
        RecordExpense(
            **virtual.source(), account_id=account, category_id=expense_category, amount="2100.00", occurred_at=WHEN
        )
    )

    assert service.account_balance(account) == -10_000
    assert "balance" not in {column["name"] for column in inspect(sqlite_engine).get_columns("account")}
    transactions = service.list_transactions()
    assert {row.kind for row in transactions} == {"opening_balance", "income", "expense"}
    for transaction in transactions:
        assert len(transaction.entries) >= 2
        assert sum(entry.amount_minor for entry in transaction.entries) == 0


@pytest.mark.c3("LED-03")
@pytest.mark.parametrize("amount", ["0", "-1.00"])
def test_zero_and_negative_ledger_commands_leave_no_rows(service, virtual, amount: str) -> None:
    account = virtual.account()
    category = virtual.category("expense", "虚拟支出")
    before = _counts(service)
    command = RecordExpense(
        **virtual.source(), account_id=account, category_id=category, amount=amount, occurred_at=WHEN
    )
    with pytest.raises(FinanceError):
        service.record_expense(command)
    assert _counts(service) == before


@pytest.mark.c3("LED-04", "LED-05", "ERR-02")
def test_missing_archived_and_wrong_kind_references_have_stable_errors(service, virtual) -> None:
    active_account = virtual.account()
    archived_account = virtual.account("虚拟归档账户")
    expense = virtual.category("expense", "虚拟支出")
    income = virtual.category("income", "虚拟收入")
    service.archive_account(
        ArchiveResource(
            **virtual.source(), resource_id=archived_account, expected_version=1, reason="虚拟归档理由"
        )
    )

    cases = [
        (
            RecordExpense(
                **virtual.source(),
                account_id=uuid.uuid4(),
                category_id=expense,
                amount="1.00",
                occurred_at=WHEN,
            ),
            "not_found",
        ),
        (
            RecordExpense(
                **virtual.source(),
                account_id=archived_account,
                category_id=expense,
                amount="1.00",
                occurred_at=WHEN,
            ),
            "archived_resource",
        ),
        (
            RecordExpense(
                **virtual.source(),
                account_id=active_account,
                category_id=uuid.uuid4(),
                amount="1.00",
                occurred_at=WHEN,
            ),
            "not_found",
        ),
        (
            RecordExpense(
                **virtual.source(),
                account_id=active_account,
                category_id=income,
                amount="1.00",
                occurred_at=WHEN,
            ),
            "validation_error",
        ),
    ]
    for command, code in cases:
        with pytest.raises(FinanceError) as raised:
            service.record_expense(command)
        assert raised.value.code == code


@pytest.mark.c3("TRF-01", "TRF-03", "SNP-02", "SNP-05")
def test_transfer_moves_cash_without_income_or_expense(service, virtual) -> None:
    wallet = virtual.account("虚拟钱包")
    bank = virtual.account("虚拟银行卡")
    service.record_opening_balance(
        RecordOpeningBalance(**virtual.source(), account_id=wallet, amount="500.00", occurred_at=WHEN)
    )
    result = service.record_transfer(
        RecordTransfer(
            **virtual.source(),
            source_account_id=wallet,
            destination_account_id=bank,
            amount="100.00",
            occurred_at=WHEN,
        )
    )
    assert (service.account_balance(wallet), service.account_balance(bank)) == (40_000, 10_000)
    snapshot = service.monthly_snapshot("2026-09", WHEN.replace(day=30, hour=23, minute=59))
    assert (snapshot.income_minor, snapshot.gross_expense_minor, snapshot.net_expense_minor) == (0, 0, 0)
    assert (snapshot.transfer_in_minor, snapshot.transfer_out_minor) == (10_000, 10_000)
    transaction = next(row for row in service.list_transactions() if row.id == result.result_id)
    assert {entry.entry_role for entry in transaction.entries} == {"account"}

    with pytest.raises(ValidationError):
        RecordTransfer(
            **virtual.source(),
            source_account_id=wallet,
            destination_account_id=wallet,
            amount="1.00",
            occurred_at=WHEN,
        )


@pytest.mark.c3("TRF-04", "ERR-02")
def test_transfer_to_missing_account_is_atomic(service, virtual) -> None:
    source = virtual.account()
    service.record_opening_balance(
        RecordOpeningBalance(**virtual.source(), account_id=source, amount="10.00", occurred_at=WHEN)
    )
    before = _counts(service)
    with pytest.raises(FinanceError) as raised:
        service.record_transfer(
            RecordTransfer(
                **virtual.source(),
                source_account_id=source,
                destination_account_id=uuid.uuid4(),
                amount="1.00",
                occurred_at=WHEN,
            )
        )
    assert raised.value.code == "not_found"
    assert _counts(service) == before
    assert service.account_balance(source) == 1000


@pytest.mark.c3("TRF-02", "ERR-05", "IDM-08")
def test_injected_failure_after_transaction_header_rolls_back_and_retry_succeeds(
    service, virtual, monkeypatch
) -> None:
    source = virtual.account("虚拟源账户")
    destination = virtual.account("虚拟目标账户")
    command = RecordTransfer(
        source_system="p1-c4",
        source_event_id="virtual-transfer-retry",
        source_account_id=source,
        destination_account_id=destination,
        amount="1.00",
        occurred_at=WHEN,
    )
    original = FinanceService._post_transaction

    def fail_after_header(session, receipt, kind, occurred_at, entries, **kwargs):
        transaction = FinancialTransaction(
            user_id=service.user_id,
            kind=kind,
            occurred_at=occurred_at,
            currency="CNY",
            command_receipt_id=receipt.id,
        )
        session.add(transaction)
        session.flush()
        raise RuntimeError("virtual injected persistence failure")

    monkeypatch.setattr(FinanceService, "_post_transaction", staticmethod(fail_after_header))
    with pytest.raises(RuntimeError, match="virtual injected"):
        service.record_transfer(command)
    assert _counts(service)[0:3] == (2, 0, 0)
    assert (service.account_balance(source), service.account_balance(destination)) == (0, 0)

    monkeypatch.setattr(FinanceService, "_post_transaction", staticmethod(original))
    result = service.record_transfer(command)
    assert not result.replayed
    assert (service.account_balance(source), service.account_balance(destination)) == (-100, 100)


@pytest.mark.c3("LED-08")
def test_reversal_preserves_original_and_fully_negates_it(service, virtual) -> None:
    account = virtual.account()
    category = virtual.category("expense", "虚拟纠错分类")
    original = service.record_expense(
        RecordExpense(
            **virtual.source(), account_id=account, category_id=category, amount="18.00", occurred_at=WHEN
        )
    )
    reversed_result = service.record_reversal(
        RecordReversal(
            **virtual.source(),
            original_transaction_id=original.result_id,
            occurred_at=WHEN.replace(day=16),
            reason="虚拟纠错",
        )
    )
    transactions = {row.id: row for row in service.list_transactions()}
    assert original.result_id in transactions
    reversal = transactions[reversed_result.result_id]
    assert reversal.related_transaction_id == original.result_id
    assert reversal.relation_kind == "reversal_of"
    assert service.account_balance(account) == 0
    with pytest.raises(FinanceError) as raised:
        service.record_reversal(
            RecordReversal(
                **virtual.source(),
                original_transaction_id=original.result_id,
                occurred_at=WHEN.replace(day=17),
                reason="虚拟重复纠错",
            )
        )
    assert raised.value.code == "invalid_transaction_relation"


@pytest.mark.c3("CAT-01")
def test_archiving_category_preserves_stable_identity_and_historical_ledger_reference(
    service, virtual
) -> None:
    account = virtual.account()
    category = virtual.category("expense", "虚拟历史分类")
    expense = service.record_expense(
        RecordExpense(
            **virtual.source(), account_id=account, category_id=category, amount="1.00", occurred_at=WHEN
        )
    )
    service.archive_category(
        ArchiveResource(
            **virtual.source(), resource_id=category, expected_version=1, reason="虚拟归档分类"
        )
    )
    assert category not in {row.id for row in service.list_categories()}
    archived = {row.id: row for row in service.list_categories(include_archived=True)}
    assert archived[category].name == "虚拟历史分类"
    assert archived[category].version_id == 2
    transaction = next(row for row in service.list_transactions() if row.id == expense.result_id)
    assert any(row.category_id == category for row in transaction.entries)
    snapshot = service.monthly_snapshot("2026-09", WHEN.replace(day=30, hour=23, minute=59))
    assert snapshot.categories[0].category_id == category


@pytest.mark.c3("TRF-06", "MIG-09")
def test_sqlite_concurrent_transfers_have_no_lost_or_partial_ledger_write(service, virtual) -> None:
    source = virtual.account("虚拟 SQLite 并发源账户")
    destinations = [
        virtual.account("虚拟 SQLite 并发目标甲"),
        virtual.account("虚拟 SQLite 并发目标乙"),
    ]
    barrier = Barrier(2)

    def submit(index: int):
        barrier.wait(timeout=5)
        try:
            result = service.record_transfer(
                RecordTransfer(
                    source_system="p1-c4",
                    source_event_id=f"virtual-sqlite-transfer-{index}",
                    source_account_id=source,
                    destination_account_id=destinations[index - 1],
                    amount=f"{index}.00",
                    occurred_at=WHEN,
                )
            )
            return index, result
        except FinanceError as exc:
            return index, exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = [future.result(timeout=10) for future in [pool.submit(submit, 1), pool.submit(submit, 2)]]
    successful = [index for index, outcome in outcomes if not isinstance(outcome, FinanceError)]
    errors = [outcome for _, outcome in outcomes if isinstance(outcome, FinanceError)]
    assert successful
    assert all(error.code == "database_unavailable" for error in errors)
    assert service.account_balance(source) == -sum(index * 100 for index in successful)
    for index, destination in enumerate(destinations, start=1):
        expected = index * 100 if index in successful else 0
        assert service.account_balance(destination) == expected
