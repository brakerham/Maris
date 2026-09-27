from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import func, select

from wife_system.finance.errors import FinanceError
from wife_system.finance.models import (
    ActivityEntryAllocation,
    ActivityOccurrence,
    ActivityTemplateRevision,
    FinancialTransaction,
    TransactionEntry,
)
from wife_system.finance.schemas import (
    AllocateActivityExpense,
    CancelActivityOccurrence,
    CreateActivityTemplate,
    LedgerSplitInput,
    RecordActivityOccurrence,
    RecordExpense,
    RecordIncome,
    RecordRefund,
    RecordSplitExpense,
    RecordTransfer,
    ReviseActivityTemplate,
)
from wife_system.finance.service import FinanceService

from conftest import WHEN


def _expense_entry(service, transaction_id: uuid.UUID) -> uuid.UUID:
    with service._sessions() as session:
        value = session.scalar(
            select(TransactionEntry.id).where(
                TransactionEntry.transaction_id == transaction_id,
                TransactionEntry.entry_role == "expense",
                TransactionEntry.amount_minor > 0,
            )
        )
    assert value is not None
    return value


@pytest.mark.c3("REF-01", "REF-02", "REF-03", "REF-04", "SNP-03")
def test_partial_multiple_full_and_excess_refunds(service, virtual) -> None:
    account = virtual.account()
    category = virtual.category("expense", "虚拟餐食")
    expense = service.record_expense(
        RecordExpense(
            **virtual.source(), account_id=account, category_id=category, amount="18.00", occurred_at=WHEN
        )
    )
    for amount in ("5.00", "7.00", "6.00"):
        service.record_refund(
            RecordRefund(
                **virtual.source(),
                original_transaction_id=expense.result_id,
                destination_account_id=account,
                amount=amount,
                occurred_at=WHEN.replace(day=16),
            )
        )
    assert service.account_balance(account) == 0
    snapshot = service.monthly_snapshot("2026-09", WHEN.replace(day=30, hour=23, minute=59))
    assert (snapshot.gross_expense_minor, snapshot.refund_minor, snapshot.net_expense_minor) == (1800, 1800, 0)

    before = len(service.list_transactions())
    with pytest.raises(FinanceError) as raised:
        service.record_refund(
            RecordRefund(
                **virtual.source(),
                original_transaction_id=expense.result_id,
                destination_account_id=account,
                amount="0.01",
                occurred_at=WHEN.replace(day=17),
            )
        )
    assert raised.value.code == "refund_exceeds_original"
    assert len(service.list_transactions()) == before


@pytest.mark.c3("REF-05")
def test_refund_rejects_missing_income_and_transfer_origins(service, virtual) -> None:
    account = virtual.account("虚拟账户一")
    other = virtual.account("虚拟账户二")
    income_category = virtual.category("income", "虚拟收入")
    income = service.record_income(
        RecordIncome(
            **virtual.source(), account_id=account, category_id=income_category, amount="5.00", occurred_at=WHEN
        )
    )
    transfer = service.record_transfer(
        RecordTransfer(
            **virtual.source(),
            source_account_id=account,
            destination_account_id=other,
            amount="1.00",
            occurred_at=WHEN,
        )
    )
    for original_id, code in (
        (uuid.uuid4(), "not_found"),
        (income.result_id, "invalid_transaction_relation"),
        (transfer.result_id, "invalid_transaction_relation"),
    ):
        with pytest.raises(FinanceError) as raised:
            service.record_refund(
                RecordRefund(
                    **virtual.source(),
                    original_transaction_id=original_id,
                    destination_account_id=account,
                    amount="1.00",
                    occurred_at=WHEN,
                )
            )
        assert raised.value.code == code


@pytest.mark.c3("REF-01", "REF-02", "AMT-05")
def test_split_refund_preserves_category_proportion_and_stable_remainder(service, virtual) -> None:
    account = virtual.account()
    food = virtual.category("expense", "虚拟餐食")
    travel = virtual.category("expense", "虚拟交通")
    expense = service.record_split_expense(
        RecordSplitExpense(
            **virtual.source(),
            account_id=account,
            occurred_at=WHEN,
            entries=[
                LedgerSplitInput(category_id=food, amount="7.00"),
                LedgerSplitInput(category_id=travel, amount="3.00"),
            ],
        )
    )
    service.record_refund(
        RecordRefund(
            **virtual.source(),
            original_transaction_id=expense.result_id,
            destination_account_id=account,
            amount="5.01",
            occurred_at=WHEN,
        )
    )
    snapshot = service.monthly_snapshot("2026-09", WHEN.replace(day=30, hour=23, minute=59))
    refunds = [row.refund_minor for row in snapshot.categories]
    assert sorted(refunds) in ([150, 351], [151, 350])
    assert sum(refunds) == 501


@pytest.mark.c3("REF-03", "AMT-05")
def test_repeated_cent_refunds_preserve_final_original_proportions(service, virtual) -> None:
    account = virtual.account()
    first = virtual.category("expense", "虚拟一分钱分类甲")
    second = virtual.category("expense", "虚拟一分钱分类乙")
    expense = service.record_split_expense(
        RecordSplitExpense(
            **virtual.source(),
            account_id=account,
            occurred_at=WHEN,
            entries=[
                LedgerSplitInput(category_id=first, amount="0.01"),
                LedgerSplitInput(category_id=second, amount="0.01"),
            ],
        )
    )
    for day in (16, 17):
        service.record_refund(
            RecordRefund(
                **virtual.source(),
                original_transaction_id=expense.result_id,
                destination_account_id=account,
                amount="0.01",
                occurred_at=WHEN.replace(day=day),
            )
        )
    snapshot = service.monthly_snapshot("2026-09", WHEN.replace(day=30, hour=23, minute=59))
    by_category = {row.category_id: row for row in snapshot.categories}
    assert by_category[first].refund_minor == 1
    assert by_category[second].refund_minor == 1
    assert all(row.net_expense_minor >= 0 for row in by_category.values())


@pytest.mark.c3("REF-01", "REF-02", "REF-03", "REF-04", "AMT-05", "IDM-01")
def test_multi_category_partial_refunds_follow_cumulative_targets_replay_and_cap(
    service, virtual
) -> None:
    account = virtual.account("虚拟累计退款账户")
    categories = [
        virtual.category("expense", "虚拟累计分类甲"),
        virtual.category("expense", "虚拟累计分类乙"),
        virtual.category("expense", "虚拟累计分类丙"),
    ]
    original = dict(zip(categories, (333, 222, 445), strict=True))
    expense = service.record_split_expense(
        RecordSplitExpense(
            **virtual.source(), account_id=account, occurred_at=WHEN,
            entries=[
                LedgerSplitInput(
                    category_id=category_id,
                    amount=f"{minor // 100}.{minor % 100:02d}",
                )
                for category_id, minor in original.items()
            ],
        )
    )
    with service._sessions() as session:
        entry_order = list(
            session.execute(
                select(TransactionEntry.category_id, TransactionEntry.id).where(
                    TransactionEntry.transaction_id == expense.result_id,
                    TransactionEntry.entry_role == "expense",
                )
            ).all()
        )

    def expected_target(cumulative_minor: int) -> dict[uuid.UUID, int]:
        target = {
            category_id: cumulative_minor * amount_minor // 1000
            for category_id, amount_minor in original.items()
        }
        remaining = cumulative_minor - sum(target.values())
        for category_id, _ in sorted(entry_order, key=lambda row: str(row[1]))[:remaining]:
            target[category_id] += 1
        return target

    cumulative = 0
    for index, amount in enumerate(("1.01", "2.03", "6.96"), start=1):
        command = RecordRefund(
            source_system="p1-c4-r2", source_event_id=f"virtual-cumulative-refund-{index}",
            original_transaction_id=expense.result_id, destination_account_id=account,
            amount=amount, occurred_at=WHEN.replace(day=15 + index),
        )
        first = service.record_refund(command)
        transaction_count = len(service.list_transactions())
        replay = service.record_refund(command)
        assert replay.replayed is True
        assert replay.result_id == first.result_id
        assert len(service.list_transactions()) == transaction_count

        cumulative += int(amount.replace(".", ""))
        snapshot = service.monthly_snapshot("2026-09", WHEN.replace(day=30, hour=23, minute=59))
        actual = {row.category_id: row.refund_minor for row in snapshot.categories}
        assert actual == expected_target(cumulative)
        assert sum(actual.values()) == cumulative
        assert all(actual[key] <= original[key] for key in categories)

    assert actual == original
    before = len(service.list_transactions())
    with pytest.raises(FinanceError) as raised:
        service.record_refund(
            RecordRefund(
                **virtual.source(), original_transaction_id=expense.result_id,
                destination_account_id=account, amount="0.01",
                occurred_at=WHEN.replace(day=19),
            )
        )
    assert raised.value.code == "refund_exceeds_original"
    assert len(service.list_transactions()) == before


@pytest.mark.c3("REF-08", "ERR-05")
def test_refund_failure_rolls_back_header_entries_receipt_and_audit(service, virtual, monkeypatch) -> None:
    account = virtual.account()
    category = virtual.category("expense", "虚拟退款回滚")
    expense = service.record_expense(
        RecordExpense(
            **virtual.source(), account_id=account, category_id=category, amount="10.00", occurred_at=WHEN
        )
    )
    original = FinanceService._post_transaction

    def fail_after_header(session, receipt, kind, occurred_at, entries, **kwargs):
        transaction = FinancialTransaction(
            user_id=service.user_id,
            kind=kind,
            occurred_at=occurred_at,
            currency="CNY",
            related_transaction_id=kwargs.get("related_id"),
            relation_kind=kwargs.get("relation_kind"),
            command_receipt_id=receipt.id,
        )
        session.add(transaction)
        session.flush()
        raise RuntimeError("virtual refund failure")

    before_balance = service.account_balance(account)
    with service._sessions() as session:
        before_counts = (
            int(session.scalar(select(func.count()).select_from(FinancialTransaction)) or 0),
            int(session.scalar(select(func.count()).select_from(TransactionEntry)) or 0),
        )
    monkeypatch.setattr(FinanceService, "_post_transaction", staticmethod(fail_after_header))
    with pytest.raises(RuntimeError, match="virtual refund failure"):
        service.record_refund(
            RecordRefund(
                source_system="p1-c4",
                source_event_id="virtual-refund-retry",
                original_transaction_id=expense.result_id,
                destination_account_id=account,
                amount="4.00",
                occurred_at=WHEN,
            )
        )
    with service._sessions() as session:
        assert (
            int(session.scalar(select(func.count()).select_from(FinancialTransaction)) or 0),
            int(session.scalar(select(func.count()).select_from(TransactionEntry)) or 0),
        ) == before_counts
    assert service.account_balance(account) == before_balance

    monkeypatch.setattr(FinanceService, "_post_transaction", staticmethod(original))
    replay = service.record_refund(
        RecordRefund(
            source_system="p1-c4",
            source_event_id="virtual-refund-retry",
            original_transaction_id=expense.result_id,
            destination_account_id=account,
            amount="4.00",
            occurred_at=WHEN,
        )
    )
    assert not replay.replayed


@pytest.mark.c3("ACT-01", "ACT-02", "ACT-05")
def test_template_revision_and_same_day_occurrences_do_not_create_ledger_entries(service, virtual) -> None:
    before = len(service.list_transactions())
    template = service.create_activity_template(
        CreateActivityTemplate(**virtual.source(), name="虚拟健身", reference_amount="30.00")
    )
    morning = service.record_activity_occurrence(
        RecordActivityOccurrence(
            **virtual.source(), template_id=template.result_id, occurred_at=WHEN.replace(hour=8)
        )
    )
    revised = service.revise_activity_template(
        ReviseActivityTemplate(
            **virtual.source(),
            template_id=template.result_id,
            expected_version=1,
            name="虚拟健身新版",
            reference_amount="35.00",
        )
    )
    evening = service.record_activity_occurrence(
        RecordActivityOccurrence(
            **virtual.source(), template_id=template.result_id, occurred_at=WHEN.replace(hour=20)
        )
    )
    assert morning.result_id != evening.result_id
    assert revised.version_id == 2
    assert len(service.list_transactions()) == before
    with service._sessions() as session:
        occurrences = {
            row.id: row.template_revision_id for row in session.scalars(select(ActivityOccurrence)).all()
        }
        revisions = list(
            session.scalars(
                select(ActivityTemplateRevision).order_by(ActivityTemplateRevision.revision_no)
            ).all()
        )
    assert [row.revision_no for row in revisions] == [1, 2]
    assert occurrences[morning.result_id] == revisions[0].id
    assert occurrences[evening.result_id] == revisions[1].id


@pytest.mark.c3("ACT-03", "ACT-04")
def test_activity_many_to_many_allocations_are_bounded(service, virtual) -> None:
    account = virtual.account()
    category = virtual.category("expense", "虚拟活动支出")
    expenses = [
        service.record_expense(
            RecordExpense(
                **virtual.source(), account_id=account, category_id=category, amount=amount, occurred_at=WHEN
            )
        )
        for amount in ("30.00", "8.00", "5.00")
    ]
    entries = [_expense_entry(service, item.result_id) for item in expenses]
    template = service.create_activity_template(CreateActivityTemplate(**virtual.source(), name="虚拟活动"))
    first = service.record_activity_occurrence(
        RecordActivityOccurrence(**virtual.source(), template_id=template.result_id, occurred_at=WHEN)
    )
    second = service.record_activity_occurrence(
        RecordActivityOccurrence(
            **virtual.source(), template_id=template.result_id, occurred_at=WHEN.replace(hour=18)
        )
    )
    for entry, amount in zip(entries, ("30.00", "8.00", "5.00"), strict=True):
        service.allocate_activity_expense(
            AllocateActivityExpense(
                **virtual.source(), occurrence_id=first.result_id, expense_entry_id=entry, amount=amount
            )
        )
    assert service.account_balance(account) == -4300

    with pytest.raises(FinanceError) as raised:
        service.allocate_activity_expense(
            AllocateActivityExpense(
                **virtual.source(), occurrence_id=second.result_id, expense_entry_id=entries[0], amount="0.01"
            )
        )
    assert raised.value.code == "allocation_exceeds_expense"


@pytest.mark.c3("ACT-05", "ACT-07")
def test_cancelled_activity_keeps_links_and_expense_but_forbids_new_allocation(service, virtual) -> None:
    account = virtual.account()
    category = virtual.category("expense", "虚拟取消活动支出")
    expense = service.record_expense(
        RecordExpense(
            **virtual.source(), account_id=account, category_id=category, amount="10.00", occurred_at=WHEN
        )
    )
    entry = _expense_entry(service, expense.result_id)
    template = service.create_activity_template(CreateActivityTemplate(**virtual.source(), name="虚拟取消活动"))
    occurrence = service.record_activity_occurrence(
        RecordActivityOccurrence(**virtual.source(), template_id=template.result_id, occurred_at=WHEN)
    )
    service.allocate_activity_expense(
        AllocateActivityExpense(
            **virtual.source(), occurrence_id=occurrence.result_id, expense_entry_id=entry, amount="4.00"
        )
    )
    service.cancel_activity_occurrence(
        CancelActivityOccurrence(
            **virtual.source(), occurrence_id=occurrence.result_id, expected_version=1, reason="虚拟取消"
        )
    )
    with pytest.raises(FinanceError) as raised:
        service.allocate_activity_expense(
            AllocateActivityExpense(
                **virtual.source(), occurrence_id=occurrence.result_id, expense_entry_id=entry, amount="1.00"
            )
        )
    assert raised.value.code == "archived_resource"
    with service._sessions() as session:
        assert session.get(TransactionEntry, entry) is not None
        assert session.scalar(
            select(func.count()).select_from(ActivityEntryAllocation).where(
                ActivityEntryAllocation.occurrence_id == occurrence.result_id
            )
        ) == 1


@pytest.mark.c3("REF-06", "MIG-09")
def test_sqlite_concurrent_refunds_never_exceed_original_or_leave_half_write(service, virtual) -> None:
    account = virtual.account()
    category = virtual.category("expense", "虚拟 SQLite 并发退款")
    expense = service.record_expense(
        RecordExpense(
            **virtual.source(), account_id=account, category_id=category, amount="18.00", occurred_at=WHEN
        )
    )
    barrier = Barrier(2)

    def submit(index: int):
        barrier.wait(timeout=5)
        try:
            return service.record_refund(
                RecordRefund(
                    source_system="p1-c4",
                    source_event_id=f"virtual-sqlite-refund-{index}",
                    original_transaction_id=expense.result_id,
                    destination_account_id=account,
                    amount="12.00",
                    occurred_at=WHEN,
                )
            )
        except FinanceError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = [future.result(timeout=10) for future in [pool.submit(submit, 1), pool.submit(submit, 2)]]
    successes = [row for row in outcomes if not isinstance(row, FinanceError)]
    errors = [row for row in outcomes if isinstance(row, FinanceError)]
    assert len(successes) == 1
    assert len(errors) == 1
    assert errors[0].code in {"refund_exceeds_original", "database_unavailable"}
    snapshot = service.monthly_snapshot("2026-09", WHEN.replace(day=30, hour=23, minute=59))
    assert snapshot.refund_minor == 1200
    assert snapshot.refund_minor <= snapshot.gross_expense_minor
