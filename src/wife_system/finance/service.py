from __future__ import annotations

import calendar
import hashlib
import hmac
import json
import logging
import re
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, TypeVar
from zoneinfo import ZoneInfo

from sqlalchemy import func, insert, or_, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.exc import StaleDataError

from .errors import FinanceError
from .models import (
    Account,
    ActivityEntryAllocation,
    ActivityOccurrence,
    ActivityTemplate,
    ActivityTemplateRevision,
    AuditEvent,
    BudgetAllocation,
    BudgetPlan,
    BudgetVersion,
    Category,
    CommandReceipt,
    FinancialTransaction,
    IncomeExpectation,
    IncomeExpectationMatch,
    IncomeSchedule,
    IncomeScheduleVersion,
    TransactionEntry,
    utc_now,
)
from .money import ensure_aggregate, parse_minor, require_cny
from .repositories import FinanceRepository
from .schemas import (
    AccountSnapshot,
    AccountView,
    AllocateActivityExpense,
    ArchiveResource,
    BudgetAllocationInput,
    BudgetAllocationView,
    BudgetVersionView,
    CancelActivityOccurrence,
    CategorySnapshot,
    CategoryView,
    CommandResult,
    CreateAccount,
    CreateActivityTemplate,
    CreateBudgetPlan,
    CreateCategory,
    CreateIncomeSchedule,
    GenerateIncomeExpectation,
    MatchIncomeExpectation,
    MonthlySnapshot,
    PublishBudgetVersion,
    RecordActivityOccurrence,
    RecordExpense,
    RecordIncome,
    RecordOpeningBalance,
    RecordRefund,
    RecordReversal,
    RecordSplitExpense,
    RecordSplitIncome,
    RecordTransfer,
    ReviseActivityTemplate,
    ReviseIncomeSchedule,
    TransactionEntryView,
    TransactionView,
    WriteCommand,
)

T = TypeVar("T")
SHANGHAI = ZoneInfo("Asia/Shanghai")
LOGGER = logging.getLogger("wife_system.finance")


@dataclass(frozen=True)
class IdempotencyKeys:
    keys: dict[int, bytes]
    current_version: int = 1

    def current(self) -> bytes:
        try:
            return self.keys[self.current_version]
        except KeyError as exc:
            raise ValueError("missing current idempotency key") from exc


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _normalize_name(value: str) -> str:
    normalized = _clean_name(value).casefold()
    if not normalized:
        raise FinanceError("validation_error")
    return normalized


def _clean_name(value: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise FinanceError("validation_error")
    return normalized


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise FinanceError("validation_error", "timezone is required")
    return value.astimezone(UTC)


def _aware_utc(value: datetime | None) -> datetime | None:
    """Restore the UTC meaning lost by SQLite's naive DateTime round trip."""
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _period_bounds(period: str) -> tuple[date, datetime, datetime]:
    if not isinstance(period, str) or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", period):
        raise FinanceError("validation_error", "period must be YYYY-MM")
    try:
        year, month = (int(piece) for piece in period.split("-", 1))
        local_start = datetime(year, month, 1, tzinfo=SHANGHAI)
    except (ValueError, TypeError) as exc:
        raise FinanceError("validation_error", "period must be YYYY-MM") from exc
    if month == 12:
        local_end = datetime(year + 1, 1, 1, tzinfo=SHANGHAI)
    else:
        local_end = datetime(year, month + 1, 1, tzinfo=SHANGHAI)
    return local_start.date(), local_start.astimezone(UTC), local_end.astimezone(UTC)


def _proportional(total: int, entries: list[tuple[uuid.UUID, int]]) -> list[tuple[uuid.UUID, int]]:
    denominator = sum(amount for _, amount in entries)
    if total <= 0 or denominator <= 0 or total > denominator:
        raise FinanceError("refund_exceeds_original")
    allocated = [(entry_id, total * amount // denominator) for entry_id, amount in entries]
    remainder = total - sum(amount for _, amount in allocated)
    ranked = sorted(entries, key=lambda item: str(item[0]))
    bonuses = {entry_id for entry_id, _ in ranked[:remainder]}
    return [(entry_id, amount + (1 if entry_id in bonuses else 0)) for entry_id, amount in allocated]


class FinanceService:
    """Synchronous command service; every write owns one short transaction."""

    def __init__(self, sessions: sessionmaker[Session], keys: IdempotencyKeys) -> None:
        self._sessions = sessions
        self._keys = keys

    def _digests(self, command: WriteCommand, command_name: str, payload: dict[str, Any]) -> tuple[str, str]:
        secret = self._keys.current()
        key_digest = hmac.new(
            secret,
            f"{command.source_system}\0{command.source_event_id}".encode(),
            hashlib.sha256,
        ).hexdigest()
        fingerprint = hmac.new(
            secret,
            b"p1-v1\0" + command_name.encode() + b"\0" + _canonical(payload),
            hashlib.sha256,
        ).hexdigest()
        return key_digest, fingerprint

    def _claim(
        self,
        session: Session,
        command: WriteCommand,
        command_name: str,
        payload: dict[str, Any],
    ) -> tuple[CommandReceipt, bool]:
        key_digest, fingerprint = self._digests(command, command_name, payload)
        values = {
            "id": uuid.uuid4(),
            "source_system": command.source_system,
            "key_version": self._keys.current_version,
            "key_digest": key_digest,
            "request_fingerprint": fingerprint,
            "command_name": command_name,
            "created_at": utc_now(),
        }
        dialect = session.bind.dialect.name if session.bind is not None else ""
        if dialect == "postgresql":
            from sqlalchemy.dialects.postgresql import insert as dialect_insert
            statement = (
                dialect_insert(CommandReceipt)
                .values(**values)
                .on_conflict_do_nothing(
                    index_elements=[CommandReceipt.source_system, CommandReceipt.key_digest]
                )
                .returning(CommandReceipt.id)
            )
            inserted = session.scalar(statement) is not None
        else:
            if dialect == "sqlite":
                from sqlalchemy.dialects.sqlite import insert as dialect_insert
                statement = dialect_insert(CommandReceipt).values(**values).on_conflict_do_nothing(
                    index_elements=[CommandReceipt.source_system, CommandReceipt.key_digest]
                )
            else:
                statement = insert(CommandReceipt).values(**values)
            result = session.execute(statement)
            inserted = result.rowcount == 1
        receipt = session.scalar(
            select(CommandReceipt).where(
                CommandReceipt.source_system == command.source_system,
                CommandReceipt.key_digest == key_digest,
            )
        )
        if receipt is None:
            raise FinanceError("persistence_error")
        if not inserted:
            if receipt.request_fingerprint != fingerprint:
                raise FinanceError("duplicate_request_conflict")
            if not receipt.result_json:
                raise FinanceError("concurrent_modification")
        return receipt, not inserted

    def _execute(
        self,
        command: WriteCommand,
        command_name: str,
        payload: dict[str, Any],
        worker: Callable[[Session, CommandReceipt], CommandResult],
    ) -> CommandResult:
        require_cny(command.currency)
        correlation_id = str(uuid.uuid4())
        try:
            with self._sessions() as session, session.begin():
                receipt, replayed = self._claim(session, command, command_name, payload)
                if replayed:
                    stored = CommandResult.model_validate_json(receipt.result_json or "{}")
                    return stored.model_copy(update={"replayed": True})
                outcome = worker(session, receipt)
                receipt.result_type = outcome.result_type
                receipt.result_id = outcome.result_id
                receipt.result_json = outcome.model_dump_json()
                receipt.completed_at = utc_now()
                session.flush()
                return outcome
        except FinanceError:
            raise
        except StaleDataError as exc:
            raise FinanceError("concurrent_modification") from exc
        except OperationalError as exc:
            LOGGER.error(json.dumps({"event": "finance_command_failed", "code": "database_unavailable", "command": command_name, "correlation_id": correlation_id}, separators=(",", ":")))
            raise FinanceError("database_unavailable") from exc
        except IntegrityError as exc:
            LOGGER.error(json.dumps({"event": "finance_command_failed", "code": "persistence_error", "command": command_name, "correlation_id": correlation_id}, separators=(",", ":")))
            raise FinanceError("persistence_error") from exc
        except DBAPIError as exc:
            LOGGER.error(json.dumps({"event": "finance_command_failed", "code": "persistence_error", "command": command_name, "correlation_id": correlation_id}, separators=(",", ":")))
            raise FinanceError("persistence_error") from exc

    @staticmethod
    def _audit(
        session: Session,
        receipt: CommandReceipt,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        before: int | None = None,
        after: int | None = None,
        reason: str | None = None,
    ) -> None:
        session.add(AuditEvent(
            command_receipt_id=receipt.id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            before_version=before,
            after_version=after,
            reason=reason,
        ))

    @staticmethod
    def _account(session: Session, account_id: uuid.UUID, *, active: bool = True, lock: bool = False) -> Account:
        account = FinanceRepository(session).account(account_id, for_update=lock)
        if account is None:
            raise FinanceError("not_found")
        if active and account.archived_at is not None:
            raise FinanceError("archived_resource")
        require_cny(account.currency)
        return account

    @staticmethod
    def _category(session: Session, category_id: uuid.UUID, kind: str, *, active: bool = True) -> Category:
        category = FinanceRepository(session).category(category_id)
        if category is None:
            raise FinanceError("not_found")
        if category.kind != kind:
            raise FinanceError("validation_error")
        if active and category.archived_at is not None:
            raise FinanceError("archived_resource")
        return category

    @staticmethod
    def _check_account_deltas(session: Session, deltas: dict[uuid.UUID, int]) -> None:
        for account_id, delta in deltas.items():
            balance = int(session.scalar(
                select(func.coalesce(func.sum(TransactionEntry.amount_minor), 0))
                .where(TransactionEntry.account_id == account_id)
            ) or 0)
            ensure_aggregate(balance + delta)

    def create_account(self, command: CreateAccount) -> CommandResult:
        name = _clean_name(command.name)
        require_cny(command.currency)
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            account = Account(name=name, currency="CNY")
            session.add(account)
            session.flush()
            self._audit(session, receipt, "account", account.id, "create", None, 1)
            return CommandResult(result_type="account", result_id=account.id, version_id=1)
        return self._execute(command, "create_account", {"name": name, "currency": "CNY"}, work)

    def create_category(self, command: CreateCategory) -> CommandResult:
        name = _clean_name(command.name)
        normalized = _normalize_name(name)
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            if session.scalar(select(Category.id).where(Category.kind == command.kind, Category.name_normalized == normalized)):
                raise FinanceError("validation_error")
            category = Category(kind=command.kind, name=name, name_normalized=normalized)
            session.add(category)
            session.flush()
            self._audit(session, receipt, "category", category.id, "create", None, 1)
            return CommandResult(result_type="category", result_id=category.id, version_id=1)
        return self._execute(command, "create_category", {"kind": command.kind, "name": normalized}, work)

    def archive_account(self, command: ArchiveResource) -> CommandResult:
        return self._archive(command, Account, "account")

    def archive_category(self, command: ArchiveResource) -> CommandResult:
        return self._archive(command, Category, "category")

    def archive_activity_template(self, command: ArchiveResource) -> CommandResult:
        return self._archive(command, ActivityTemplate, "activity_template")

    def archive_income_schedule(self, command: ArchiveResource) -> CommandResult:
        return self._archive(command, IncomeSchedule, "income_schedule")

    def archive_budget_plan(self, command: ArchiveResource) -> CommandResult:
        return self._archive(command, BudgetPlan, "budget_plan")

    def _archive(self, command: ArchiveResource, model: type[Any], entity: str) -> CommandResult:
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            item = session.get(model, command.resource_id)
            if item is None:
                raise FinanceError("not_found")
            if item.version_id != command.expected_version:
                raise FinanceError("concurrent_modification")
            if item.archived_at is not None:
                raise FinanceError("archived_resource")
            before = item.version_id
            item.archived_at = utc_now()
            item.version_id = before + 1
            session.flush()
            self._audit(session, receipt, entity, item.id, "archive", before, item.version_id, command.reason)
            return CommandResult(result_type=entity, result_id=item.id, version_id=item.version_id)
        return self._execute(
            command,
            f"archive_{entity}",
            {"resource_id": str(command.resource_id), "expected_version": command.expected_version, "reason": command.reason},
            work,
        )

    @staticmethod
    def _post_transaction(
        session: Session,
        receipt: CommandReceipt,
        kind: str,
        occurred_at: datetime,
        entries: list[dict[str, Any]],
        *,
        related_id: uuid.UUID | None = None,
        relation_kind: str | None = None,
    ) -> tuple[FinancialTransaction, list[TransactionEntry]]:
        if len(entries) < 2 or any(int(entry["amount_minor"]) == 0 for entry in entries):
            raise FinanceError("unbalanced_transaction")
        if sum(int(entry["amount_minor"]) for entry in entries) != 0:
            raise FinanceError("unbalanced_transaction")
        for entry in entries:
            ensure_aggregate(int(entry["amount_minor"]))
            role = entry["entry_role"]
            account_id, category_id = entry.get("account_id"), entry.get("category_id")
            shape_ok = (
                (role == "account" and account_id is not None and category_id is None)
                or (role in {"expense", "income"} and account_id is None and category_id is not None)
                or (role == "opening_equity" and account_id is None and category_id is None)
            )
            if not shape_ok:
                raise FinanceError("unbalanced_transaction")
        txn = FinancialTransaction(
            kind=kind,
            occurred_at=_utc(occurred_at),
            currency="CNY",
            related_transaction_id=related_id,
            relation_kind=relation_kind,
            command_receipt_id=receipt.id,
        )
        session.add(txn)
        session.flush()
        rows = [TransactionEntry(transaction_id=txn.id, line_no=i + 1, **entry) for i, entry in enumerate(entries)]
        session.add_all(rows)
        session.flush()
        return txn, rows

    def record_opening_balance(self, command: RecordOpeningBalance) -> CommandResult:
        amount = parse_minor(command.amount)
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            self._account(session, command.account_id)
            self._check_account_deltas(session, {command.account_id: amount})
            txn, _ = self._post_transaction(session, receipt, "opening_balance", command.occurred_at, [
                {"entry_role": "account", "amount_minor": amount, "account_id": command.account_id},
                {"entry_role": "opening_equity", "amount_minor": -amount},
            ])
            self._audit(session, receipt, "financial_transaction", txn.id, "post")
            return CommandResult(result_type="financial_transaction", result_id=txn.id)
        return self._execute(command, "record_opening_balance", {"account_id": str(command.account_id), "amount_minor": amount, "occurred_at": _utc(command.occurred_at).isoformat()}, work)

    def record_income(self, command: RecordIncome) -> CommandResult:
        return self._record_simple(command, "income")

    def record_expense(self, command: RecordExpense) -> CommandResult:
        return self._record_simple(command, "expense")

    def record_split_income(self, command: RecordSplitIncome) -> CommandResult:
        return self._record_split(command, "income")

    def record_split_expense(self, command: RecordSplitExpense) -> CommandResult:
        return self._record_split(command, "expense")

    def _record_split(self, command: RecordSplitIncome | RecordSplitExpense, kind: str) -> CommandResult:
        parsed = [(row.category_id, parse_minor(row.amount)) for row in command.entries]
        if len({category_id for category_id, _ in parsed}) != len(parsed):
            raise FinanceError("validation_error")
        total = ensure_aggregate(sum(amount for _, amount in parsed))
        account_delta = total if kind == "income" else -total
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            self._account(session, command.account_id)
            for category_id, _ in parsed:
                self._category(session, category_id, kind)
            self._check_account_deltas(session, {command.account_id: account_delta})
            entries: list[dict[str, Any]] = [{"entry_role": "account", "amount_minor": account_delta, "account_id": command.account_id}]
            sign = -1 if kind == "income" else 1
            entries.extend({"entry_role": kind, "amount_minor": sign * amount, "category_id": category_id} for category_id, amount in parsed)
            txn, _ = self._post_transaction(session, receipt, kind, command.occurred_at, entries)
            self._audit(session, receipt, "financial_transaction", txn.id, "post")
            return CommandResult(result_type="financial_transaction", result_id=txn.id)
        payload = {
            "account_id": str(command.account_id),
            "entries": sorted([{"category_id": str(category_id), "amount_minor": amount} for category_id, amount in parsed], key=lambda row: row["category_id"]),
            "occurred_at": _utc(command.occurred_at).isoformat(),
        }
        return self._execute(command, f"record_split_{kind}", payload, work)

    def _record_simple(self, command: RecordIncome | RecordExpense, kind: str) -> CommandResult:
        amount = parse_minor(command.amount)
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            self._account(session, command.account_id)
            self._category(session, command.category_id, kind)
            account_amount = amount if kind == "income" else -amount
            category_amount = -amount if kind == "income" else amount
            self._check_account_deltas(session, {command.account_id: account_amount})
            txn, _ = self._post_transaction(session, receipt, kind, command.occurred_at, [
                {"entry_role": "account", "amount_minor": account_amount, "account_id": command.account_id},
                {"entry_role": kind, "amount_minor": category_amount, "category_id": command.category_id},
            ])
            self._audit(session, receipt, "financial_transaction", txn.id, "post")
            return CommandResult(result_type="financial_transaction", result_id=txn.id)
        payload = {"account_id": str(command.account_id), "category_id": str(command.category_id), "amount_minor": amount, "occurred_at": _utc(command.occurred_at).isoformat()}
        return self._execute(command, f"record_{kind}", payload, work)

    def record_transfer(self, command: RecordTransfer) -> CommandResult:
        amount = parse_minor(command.amount)
        if command.source_account_id == command.destination_account_id:
            raise FinanceError("validation_error")
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            self._account(session, command.source_account_id)
            self._account(session, command.destination_account_id)
            self._check_account_deltas(session, {
                command.source_account_id: -amount,
                command.destination_account_id: amount,
            })
            txn, _ = self._post_transaction(session, receipt, "transfer", command.occurred_at, [
                {"entry_role": "account", "amount_minor": -amount, "account_id": command.source_account_id},
                {"entry_role": "account", "amount_minor": amount, "account_id": command.destination_account_id},
            ])
            self._audit(session, receipt, "financial_transaction", txn.id, "post")
            return CommandResult(result_type="financial_transaction", result_id=txn.id)
        payload = {"source_account_id": str(command.source_account_id), "destination_account_id": str(command.destination_account_id), "amount_minor": amount, "occurred_at": _utc(command.occurred_at).isoformat()}
        return self._execute(command, "record_transfer", payload, work)

    def record_refund(self, command: RecordRefund) -> CommandResult:
        amount = parse_minor(command.amount)
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            self._account(session, command.destination_account_id)
            stmt = select(FinancialTransaction).where(FinancialTransaction.id == command.original_transaction_id)
            if session.bind is not None and session.bind.dialect.name == "postgresql":
                stmt = stmt.with_for_update()
            original = session.scalar(stmt)
            if original is None:
                raise FinanceError("not_found")
            if original.kind != "expense" or original.currency != "CNY":
                raise FinanceError("invalid_transaction_relation")
            originals = list(session.scalars(select(TransactionEntry).where(
                TransactionEntry.transaction_id == original.id,
                TransactionEntry.entry_role == "expense",
                TransactionEntry.amount_minor > 0,
            )).all())
            original_total = sum(row.amount_minor for row in originals)
            refunded_rows = session.execute(select(
                TransactionEntry.category_id,
                func.coalesce(func.sum(-TransactionEntry.amount_minor), 0),
            ).join(
                FinancialTransaction, FinancialTransaction.id == TransactionEntry.transaction_id
            ).where(
                FinancialTransaction.kind == "refund",
                FinancialTransaction.related_transaction_id == original.id,
                TransactionEntry.entry_role == "expense",
                TransactionEntry.amount_minor < 0,
            ).group_by(TransactionEntry.category_id)).all()
            refunded_by_category = {category_id: int(refunded_minor) for category_id, refunded_minor in refunded_rows}
            refunded = sum(refunded_by_category.values())
            if amount + refunded > original_total:
                raise FinanceError("refund_exceeds_original")
            self._check_account_deltas(session, {command.destination_account_id: amount})
            cumulative_targets = dict(_proportional(refunded + amount, [(row.id, row.amount_minor) for row in originals]))
            by_id = {row.id: row for row in originals}
            remaining = amount
            allocations: list[tuple[uuid.UUID, int]] = []
            for entry_id in sorted(by_id, key=str):
                row = by_id[entry_id]
                already_refunded = refunded_by_category.get(row.category_id, 0)
                desired_increment = max(cumulative_targets[entry_id] - already_refunded, 0)
                increment = min(desired_increment, remaining)
                if increment:
                    allocations.append((entry_id, increment))
                    remaining -= increment
            if remaining:
                raise FinanceError("persistence_error")
            entries: list[dict[str, Any]] = [{"entry_role": "account", "amount_minor": amount, "account_id": command.destination_account_id}]
            entries.extend({"entry_role": "expense", "amount_minor": -part, "category_id": by_id[entry_id].category_id} for entry_id, part in allocations)
            txn, _ = self._post_transaction(session, receipt, "refund", command.occurred_at, entries, related_id=original.id, relation_kind="refund_of")
            self._audit(session, receipt, "financial_transaction", txn.id, "post_refund")
            return CommandResult(result_type="financial_transaction", result_id=txn.id)
        payload = {"original_transaction_id": str(command.original_transaction_id), "destination_account_id": str(command.destination_account_id), "amount_minor": amount, "occurred_at": _utc(command.occurred_at).isoformat()}
        return self._execute(command, "record_refund", payload, work)

    def record_reversal(self, command: RecordReversal) -> CommandResult:
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            original = session.get(FinancialTransaction, command.original_transaction_id)
            if original is None:
                raise FinanceError("not_found")
            if original.kind == "reversal":
                raise FinanceError("invalid_transaction_relation")
            if session.scalar(select(FinancialTransaction.id).where(FinancialTransaction.kind == "reversal", FinancialTransaction.related_transaction_id == original.id)):
                raise FinanceError("invalid_transaction_relation")
            rows = list(session.scalars(select(TransactionEntry).where(TransactionEntry.transaction_id == original.id).order_by(TransactionEntry.line_no)).all())
            entries = [{"entry_role": row.entry_role, "amount_minor": -row.amount_minor, "account_id": row.account_id, "category_id": row.category_id} for row in rows]
            deltas: dict[uuid.UUID, int] = {}
            for row in rows:
                if row.account_id is not None:
                    deltas[row.account_id] = deltas.get(row.account_id, 0) - row.amount_minor
            self._check_account_deltas(session, deltas)
            txn, _ = self._post_transaction(session, receipt, "reversal", command.occurred_at, entries, related_id=original.id, relation_kind="reversal_of")
            self._audit(session, receipt, "financial_transaction", txn.id, "post_reversal", reason=command.reason)
            return CommandResult(result_type="financial_transaction", result_id=txn.id)
        payload = {"original_transaction_id": str(command.original_transaction_id), "occurred_at": _utc(command.occurred_at).isoformat(), "reason": command.reason}
        return self._execute(command, "record_reversal", payload, work)

    def create_activity_template(self, command: CreateActivityTemplate) -> CommandResult:
        reference = parse_minor(command.reference_amount, allow_zero=True) if command.reference_amount is not None else None
        name = _clean_name(command.name)
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            return self._create_activity_template_in_session(
                session,
                receipt,
                name=name,
                reference_minor=reference,
                reference_min_minor=reference,
                reference_max_minor=reference,
            )
        return self._execute(command, "create_activity_template", {"name": name, "reference_minor": reference}, work)

    def revise_activity_template(self, command: ReviseActivityTemplate) -> CommandResult:
        reference = parse_minor(command.reference_amount, allow_zero=True) if command.reference_amount is not None else None
        name = _clean_name(command.name)
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            template = session.get(ActivityTemplate, command.template_id)
            if template is None:
                raise FinanceError("not_found")
            return self._revise_activity_template_in_session(
                session,
                receipt,
                template=template,
                expected_version=command.expected_version,
                name=name,
                reference_minor=reference,
                reference_min_minor=reference,
                reference_max_minor=reference,
            )
        payload = {"template_id": str(command.template_id), "expected_version": command.expected_version, "name": name, "reference_minor": reference}
        return self._execute(command, "revise_activity_template", payload, work)

    def _create_activity_template_in_session(
        self,
        session: Session,
        receipt: CommandReceipt,
        *,
        name: str,
        reference_minor: int | None,
        reference_min_minor: int | None,
        reference_max_minor: int | None,
        source_import_candidate_id: uuid.UUID | None = None,
    ) -> CommandResult:
        """Append a template inside a transaction owned by the caller."""
        clean_name = _clean_name(name)
        template = ActivityTemplate(name_normalized=_normalize_name(clean_name))
        session.add(template)
        session.flush()
        revision = ActivityTemplateRevision(
            template_id=template.id,
            revision_no=1,
            name=clean_name,
            reference_minor=reference_minor,
            reference_min_minor=reference_min_minor,
            reference_max_minor=reference_max_minor,
            source_import_candidate_id=source_import_candidate_id,
        )
        session.add(revision)
        session.flush()
        template.current_revision_id = revision.id
        session.flush()
        self._audit(session, receipt, "activity_template", template.id, "create", None, template.version_id)
        return CommandResult(result_type="activity_template", result_id=template.id, version_id=template.version_id)

    def _revise_activity_template_in_session(
        self,
        session: Session,
        receipt: CommandReceipt,
        *,
        template: ActivityTemplate,
        expected_version: int,
        name: str,
        reference_minor: int | None,
        reference_min_minor: int | None,
        reference_max_minor: int | None,
        source_import_candidate_id: uuid.UUID | None = None,
    ) -> CommandResult:
        """Append a revision inside a transaction owned by the caller."""
        if template.archived_at is not None:
            raise FinanceError("archived_resource")
        if template.version_id != expected_version:
            raise FinanceError("concurrent_modification")
        clean_name = _clean_name(name)
        revision_no = (session.scalar(
            select(func.max(ActivityTemplateRevision.revision_no)).where(
                ActivityTemplateRevision.template_id == template.id
            )
        ) or 0) + 1
        revision = ActivityTemplateRevision(
            template_id=template.id,
            revision_no=revision_no,
            name=clean_name,
            reference_minor=reference_minor,
            reference_min_minor=reference_min_minor,
            reference_max_minor=reference_max_minor,
            source_import_candidate_id=source_import_candidate_id,
        )
        session.add(revision)
        session.flush()
        before = template.version_id
        template.name_normalized = _normalize_name(clean_name)
        template.current_revision_id = revision.id
        template.version_id = before + 1
        session.flush()
        self._audit(session, receipt, "activity_template", template.id, "revise", before, template.version_id)
        return CommandResult(result_type="activity_template", result_id=template.id, version_id=template.version_id)

    def record_activity_occurrence(self, command: RecordActivityOccurrence) -> CommandResult:
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            template = session.get(ActivityTemplate, command.template_id)
            if template is None: raise FinanceError("not_found")
            if template.archived_at is not None: raise FinanceError("archived_resource")
            if template.current_revision_id is None: raise FinanceError("persistence_error")
            occurrence = ActivityOccurrence(template_revision_id=template.current_revision_id, occurred_at=_utc(command.occurred_at))
            session.add(occurrence); session.flush()
            self._audit(session, receipt, "activity_occurrence", occurrence.id, "create", None, 1)
            return CommandResult(result_type="activity_occurrence", result_id=occurrence.id, version_id=1)
        return self._execute(command, "record_activity_occurrence", {"template_id": str(command.template_id), "occurred_at": _utc(command.occurred_at).isoformat()}, work)

    def cancel_activity_occurrence(self, command: CancelActivityOccurrence) -> CommandResult:
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            occurrence = session.get(ActivityOccurrence, command.occurrence_id)
            if occurrence is None: raise FinanceError("not_found")
            if occurrence.version_id != command.expected_version: raise FinanceError("concurrent_modification")
            before = occurrence.version_id; occurrence.status = "cancelled"; occurrence.version_id = before + 1; session.flush()
            self._audit(session, receipt, "activity_occurrence", occurrence.id, "cancel", before, occurrence.version_id, command.reason)
            return CommandResult(result_type="activity_occurrence", result_id=occurrence.id, version_id=occurrence.version_id)
        return self._execute(command, "cancel_activity_occurrence", {"occurrence_id": str(command.occurrence_id), "expected_version": command.expected_version, "reason": command.reason}, work)

    def allocate_activity_expense(self, command: AllocateActivityExpense) -> CommandResult:
        amount = parse_minor(command.amount)
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            occurrence = session.get(ActivityOccurrence, command.occurrence_id)
            if occurrence is None: raise FinanceError("not_found")
            if occurrence.status != "active": raise FinanceError("archived_resource")
            entry_stmt = select(TransactionEntry).where(TransactionEntry.id == command.expense_entry_id)
            if session.bind is not None and session.bind.dialect.name == "postgresql": entry_stmt = entry_stmt.with_for_update()
            entry = session.scalar(entry_stmt)
            if entry is None: raise FinanceError("not_found")
            if entry.entry_role != "expense" or entry.amount_minor <= 0: raise FinanceError("validation_error")
            allocated = session.scalar(select(func.coalesce(func.sum(ActivityEntryAllocation.allocated_minor), 0)).where(ActivityEntryAllocation.expense_entry_id == entry.id)) or 0
            if allocated + amount > entry.amount_minor: raise FinanceError("allocation_exceeds_expense")
            if session.scalar(select(ActivityEntryAllocation.id).where(
                ActivityEntryAllocation.occurrence_id == occurrence.id,
                ActivityEntryAllocation.expense_entry_id == entry.id,
            )):
                raise FinanceError("validation_error")
            allocation = ActivityEntryAllocation(occurrence_id=occurrence.id, expense_entry_id=entry.id, allocated_minor=amount)
            session.add(allocation); session.flush()
            self._audit(session, receipt, "activity_entry_allocation", allocation.id, "create")
            return CommandResult(result_type="activity_entry_allocation", result_id=allocation.id)
        payload = {"occurrence_id": str(command.occurrence_id), "expense_entry_id": str(command.expense_entry_id), "amount_minor": amount}
        return self._execute(command, "allocate_activity_expense", payload, work)

    def create_income_schedule(self, command: CreateIncomeSchedule) -> CommandResult:
        return self._create_or_revise_schedule(command, None)

    def revise_income_schedule(self, command: ReviseIncomeSchedule) -> CommandResult:
        return self._create_or_revise_schedule(command, command.schedule_id)

    def _create_or_revise_schedule(self, command: CreateIncomeSchedule | ReviseIncomeSchedule, schedule_id: uuid.UUID | None) -> CommandResult:
        amount = parse_minor(command.amount)
        if command.effective_to is not None and command.effective_to < command.effective_from:
            raise FinanceError("validation_error")
        name = "create_income_schedule" if schedule_id is None else "revise_income_schedule"
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            if schedule_id is None:
                schedule = IncomeSchedule(); session.add(schedule); session.flush(); revision_no = 1; before = None
            else:
                schedule = session.get(IncomeSchedule, schedule_id)
                if schedule is None: raise FinanceError("not_found")
                if schedule.archived_at is not None: raise FinanceError("archived_resource")
                if schedule.version_id != command.expected_version: raise FinanceError("concurrent_modification")  # type: ignore[attr-defined]
                before = schedule.version_id
                revision_no = (session.scalar(select(func.max(IncomeScheduleVersion.revision_no)).where(IncomeScheduleVersion.schedule_id == schedule.id)) or 0) + 1
            version = IncomeScheduleVersion(schedule_id=schedule.id, revision_no=revision_no, amount_minor=amount, effective_from=command.effective_from, effective_to=command.effective_to, due_day=command.due_day)
            session.add(version); session.flush(); schedule.current_version_id = version.id
            if before is not None: schedule.version_id = before + 1
            session.flush()
            self._audit(session, receipt, "income_schedule", schedule.id, "create" if before is None else "revise", before, schedule.version_id)
            return CommandResult(result_type="income_schedule", result_id=schedule.id, version_id=schedule.version_id)
        payload = {"schedule_id": str(schedule_id) if schedule_id else None, "expected_version": getattr(command, "expected_version", None), "amount_minor": amount, "effective_from": command.effective_from.isoformat(), "effective_to": command.effective_to.isoformat() if command.effective_to else None, "due_day": command.due_day}
        return self._execute(command, name, payload, work)

    def generate_income_expectation(self, command: GenerateIncomeExpectation) -> CommandResult:
        period_date, _, _ = _period_bounds(command.period)
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            schedule = session.get(IncomeSchedule, command.schedule_id)
            if schedule is None: raise FinanceError("not_found")
            if schedule.archived_at is not None: raise FinanceError("archived_resource")
            versions = list(session.scalars(select(IncomeScheduleVersion).where(
                IncomeScheduleVersion.schedule_id == schedule.id,
                IncomeScheduleVersion.effective_from <= date(period_date.year, period_date.month, calendar.monthrange(period_date.year, period_date.month)[1]),
                or_(IncomeScheduleVersion.effective_to.is_(None), IncomeScheduleVersion.effective_to >= period_date),
            ).order_by(IncomeScheduleVersion.revision_no.desc())).all())
            version = None
            due = None
            for candidate in versions:
                candidate_day = min(candidate.due_day, calendar.monthrange(period_date.year, period_date.month)[1])
                candidate_due = date(period_date.year, period_date.month, candidate_day)
                if candidate_due >= candidate.effective_from and (candidate.effective_to is None or candidate_due <= candidate.effective_to):
                    version, due = candidate, candidate_due
                    break
            if version is None: raise FinanceError("not_found")
            if session.scalar(select(IncomeExpectation.id).where(
                IncomeExpectation.schedule_version_id == version.id,
                IncomeExpectation.due_date == due,
            )):
                raise FinanceError("validation_error")
            expectation = IncomeExpectation(schedule_version_id=version.id, due_date=due, expected_minor=version.amount_minor)
            session.add(expectation); session.flush()
            self._audit(session, receipt, "income_expectation", expectation.id, "generate")
            return CommandResult(result_type="income_expectation", result_id=expectation.id)
        return self._execute(command, "generate_income_expectation", {"schedule_id": str(command.schedule_id), "period": command.period}, work)

    def match_income_expectation(self, command: MatchIncomeExpectation) -> CommandResult:
        amount = parse_minor(command.amount)
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            expectation_stmt = select(IncomeExpectation).where(IncomeExpectation.id == command.expectation_id)
            if session.bind is not None and session.bind.dialect.name == "postgresql": expectation_stmt = expectation_stmt.with_for_update()
            expectation = session.scalar(expectation_stmt)
            if expectation is None: raise FinanceError("not_found")
            entry = session.get(TransactionEntry, command.income_entry_id)
            if entry is None: raise FinanceError("not_found")
            if entry.entry_role != "income" or entry.amount_minor >= 0: raise FinanceError("validation_error")
            if session.scalar(select(IncomeExpectationMatch.id).where(IncomeExpectationMatch.income_entry_id == entry.id)):
                raise FinanceError("validation_error")
            matched = session.scalar(select(func.coalesce(func.sum(IncomeExpectationMatch.matched_minor), 0)).where(IncomeExpectationMatch.expectation_id == expectation.id)) or 0
            if matched + amount > expectation.expected_minor or amount > -entry.amount_minor:
                raise FinanceError("expectation_match_exceeds_amount")
            match = IncomeExpectationMatch(expectation_id=expectation.id, income_entry_id=entry.id, matched_minor=amount)
            session.add(match); session.flush()
            expectation.status = "matched" if matched + amount == expectation.expected_minor else "partial"
            self._audit(session, receipt, "income_expectation_match", match.id, "create")
            return CommandResult(result_type="income_expectation_match", result_id=match.id)
        payload = {"expectation_id": str(command.expectation_id), "income_entry_id": str(command.income_entry_id), "amount_minor": amount}
        return self._execute(command, "match_income_expectation", payload, work)

    def create_budget_plan(self, command: CreateBudgetPlan) -> CommandResult:
        name = _clean_name(command.name)
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            plan = BudgetPlan(name=name); session.add(plan); session.flush()
            self._audit(session, receipt, "budget_plan", plan.id, "create", None, 1)
            return CommandResult(result_type="budget_plan", result_id=plan.id, version_id=1)
        return self._execute(command, "create_budget_plan", {"name": name}, work)

    def publish_budget_version(self, command: PublishBudgetVersion) -> CommandResult:
        period_date, _, period_end = _period_bounds(command.period)
        local_published = command.published_at.astimezone(SHANGHAI)
        if period_end.astimezone(SHANGHAI).date() <= local_published.date().replace(day=1):
            raise FinanceError("budget_period_closed")
        parsed: list[tuple[BudgetAllocationInput, int]] = [(row, parse_minor(row.limit, allow_zero=True)) for row in command.allocations]
        ensure_aggregate(sum(limit for _, limit in parsed))
        if len({row.category_id for row, _ in parsed}) != len(parsed):
            raise FinanceError("validation_error")
        def work(session: Session, receipt: CommandReceipt) -> CommandResult:
            stmt = select(BudgetPlan).where(BudgetPlan.id == command.plan_id)
            if session.bind is not None and session.bind.dialect.name == "postgresql": stmt = stmt.with_for_update()
            plan = session.scalar(stmt)
            if plan is None: raise FinanceError("not_found")
            if plan.archived_at is not None: raise FinanceError("archived_resource")
            if plan.version_id != command.expected_version: raise FinanceError("concurrent_modification")
            for row, _ in parsed: self._category(session, row.category_id, "expense")
            version_no = (session.scalar(select(func.max(BudgetVersion.version_no)).where(BudgetVersion.plan_id == plan.id, BudgetVersion.period == period_date)) or 0) + 1
            if version_no > 1 and (not command.adjustment_reason or not command.adjustment_reason.strip()): raise FinanceError("validation_error")
            version = BudgetVersion(plan_id=plan.id, period=period_date, version_no=version_no, adjustment_reason=command.adjustment_reason, published_at=_utc(command.published_at))
            session.add(version); session.flush()
            session.add_all(BudgetAllocation(budget_version_id=version.id, category_id=row.category_id, limit_minor=limit) for row, limit in parsed)
            before = plan.version_id; plan.version_id = before + 1; session.flush()
            self._audit(session, receipt, "budget_version", version.id, "publish", before, plan.version_id, command.adjustment_reason)
            return CommandResult(result_type="budget_version", result_id=version.id, version_id=plan.version_id)
        payload = {"plan_id": str(command.plan_id), "expected_version": command.expected_version, "period": command.period, "allocations": sorted([{"category_id": str(row.category_id), "limit_minor": limit} for row, limit in parsed], key=lambda item: item["category_id"]), "adjustment_reason": command.adjustment_reason, "published_at": _utc(command.published_at).isoformat()}
        return self._execute(command, "publish_budget_version", payload, work)

    def list_accounts(self, *, include_archived: bool = False) -> list[AccountView]:
        with self._sessions() as session:
            stmt = select(Account)
            if not include_archived: stmt = stmt.where(Account.archived_at.is_(None))
            rows = session.scalars(stmt.order_by(Account.name, Account.id)).all()
            return [AccountView(id=row.id, name=row.name, currency=row.currency, version_id=row.version_id, archived_at=_aware_utc(row.archived_at), created_at=_aware_utc(row.created_at)) for row in rows]

    def list_categories(self, *, include_archived: bool = False) -> list[CategoryView]:
        with self._sessions() as session:
            stmt = select(Category)
            if not include_archived: stmt = stmt.where(Category.archived_at.is_(None))
            rows = session.scalars(stmt.order_by(Category.kind, Category.name_normalized, Category.id)).all()
            return [CategoryView(id=row.id, kind=row.kind, name=row.name, version_id=row.version_id, archived_at=_aware_utc(row.archived_at), created_at=_aware_utc(row.created_at)) for row in rows]

    def account_balance(self, account_id: uuid.UUID, *, as_of: datetime | None = None) -> int:
        with self._sessions() as session:
            self._account(session, account_id, active=False)
            stmt = select(func.coalesce(func.sum(TransactionEntry.amount_minor), 0)).join(FinancialTransaction).where(TransactionEntry.account_id == account_id)
            if as_of is not None: stmt = stmt.where(FinancialTransaction.occurred_at <= _utc(as_of))
            return ensure_aggregate(int(session.scalar(stmt) or 0))

    def list_transactions(self, *, start: datetime | None = None, end: datetime | None = None) -> list[TransactionView]:
        with self._sessions() as session:
            stmt = select(FinancialTransaction)
            if start is not None: stmt = stmt.where(FinancialTransaction.occurred_at >= _utc(start))
            if end is not None: stmt = stmt.where(FinancialTransaction.occurred_at < _utc(end))
            transactions = session.scalars(stmt.order_by(FinancialTransaction.occurred_at, FinancialTransaction.id)).all()
            views = []
            for transaction in transactions:
                entries = session.scalars(select(TransactionEntry).where(TransactionEntry.transaction_id == transaction.id).order_by(TransactionEntry.line_no, TransactionEntry.id)).all()
                views.append(TransactionView(
                    id=transaction.id,
                    kind=transaction.kind,
                    occurred_at=_aware_utc(transaction.occurred_at),
                    currency=transaction.currency,
                    related_transaction_id=transaction.related_transaction_id,
                    relation_kind=transaction.relation_kind,
                    entries=[TransactionEntryView(id=row.id, line_no=row.line_no, entry_role=row.entry_role, amount_minor=row.amount_minor, account_id=row.account_id, category_id=row.category_id) for row in entries],
                ))
            return views

    def list_budget_versions(self, plan_id: uuid.UUID, *, period: str | None = None) -> list[BudgetVersionView]:
        with self._sessions() as session:
            plan = session.get(BudgetPlan, plan_id)
            if plan is None:
                raise FinanceError("not_found")
            stmt = select(BudgetVersion).where(BudgetVersion.plan_id == plan_id)
            if period is not None:
                period_date, _, _ = _period_bounds(period)
                stmt = stmt.where(BudgetVersion.period == period_date)
            versions = session.scalars(stmt.order_by(BudgetVersion.period, BudgetVersion.version_no, BudgetVersion.id)).all()
            result = []
            for version in versions:
                allocations = session.scalars(select(BudgetAllocation).where(BudgetAllocation.budget_version_id == version.id).order_by(BudgetAllocation.category_id, BudgetAllocation.id)).all()
                result.append(BudgetVersionView(
                    id=version.id,
                    plan_id=version.plan_id,
                    period=version.period,
                    version_no=version.version_no,
                    adjustment_reason=version.adjustment_reason,
                    published_at=_aware_utc(version.published_at),
                    allocations=[BudgetAllocationView(category_id=row.category_id, limit_minor=row.limit_minor) for row in allocations],
                ))
            return result

    def monthly_snapshot(
        self,
        period: str,
        as_of: datetime,
        *,
        account_ids: Iterable[uuid.UUID] | None = None,
        category_ids: Iterable[uuid.UUID] | None = None,
    ) -> MonthlySnapshot:
        period_date, start, end = _period_bounds(period)
        cutoff = min(_utc(as_of), end)
        account_filter = set(account_ids or [])
        category_filter = set(category_ids or [])
        with self._sessions() as session, session.begin():
            if session.bind is not None and session.bind.dialect.name == "postgresql":
                session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"))
            txn_filter = select(FinancialTransaction.id).where(
                FinancialTransaction.occurred_at >= start,
                FinancialTransaction.occurred_at < cutoff,
            )
            if account_filter:
                txn_filter = txn_filter.where(FinancialTransaction.id.in_(
                    select(TransactionEntry.transaction_id).where(TransactionEntry.account_id.in_(account_filter))
                ))
            if category_filter:
                txn_filter = txn_filter.where(FinancialTransaction.id.in_(
                    select(TransactionEntry.transaction_id).where(TransactionEntry.category_id.in_(category_filter))
                ))
            transaction_rows = list(session.execute(select(
                FinancialTransaction.kind,
                TransactionEntry.entry_role,
                TransactionEntry.amount_minor,
                TransactionEntry.account_id,
                TransactionEntry.category_id,
            ).join(TransactionEntry, TransactionEntry.transaction_id == FinancialTransaction.id).where(
                FinancialTransaction.id.in_(txn_filter),
            )).all())
            income = -sum(row.amount_minor for row in transaction_rows if row.entry_role == "income")
            gross = sum(row.amount_minor for row in transaction_rows if row.entry_role == "expense" and row.amount_minor > 0)
            reductions = -sum(row.amount_minor for row in transaction_rows if row.entry_role == "expense" and row.amount_minor < 0)
            transfer_in = sum(row.amount_minor for row in transaction_rows if row.kind == "transfer" and row.entry_role == "account" and row.amount_minor > 0)
            transfer_out = -sum(row.amount_minor for row in transaction_rows if row.kind == "transfer" and row.entry_role == "account" and row.amount_minor < 0)

            budget = session.scalar(select(BudgetVersion).where(
                BudgetVersion.period == period_date,
                BudgetVersion.published_at <= _utc(as_of),
            ).order_by(BudgetVersion.published_at.desc(), BudgetVersion.version_no.desc(), BudgetVersion.id).limit(1))
            limits: dict[uuid.UUID, int] = {}
            if budget is not None:
                allocation_stmt = select(BudgetAllocation.category_id, BudgetAllocation.limit_minor).where(BudgetAllocation.budget_version_id == budget.id)
                if category_filter:
                    allocation_stmt = allocation_stmt.where(BudgetAllocation.category_id.in_(category_filter))
                limits = dict(session.execute(allocation_stmt).all())

            category_totals: dict[uuid.UUID, list[int]] = {}
            for row in transaction_rows:
                if row.entry_role != "expense" or row.category_id is None or (category_filter and row.category_id not in category_filter): continue
                values = category_totals.setdefault(row.category_id, [0, 0])
                if row.amount_minor > 0: values[0] += row.amount_minor
                else: values[1] += -row.amount_minor
            category_keys = set(category_totals) | set(limits)
            categories = []
            for category_id in sorted(category_keys, key=str):
                cat_gross, cat_refund = category_totals.get(category_id, [0, 0])
                limit = limits.get(category_id)
                net = cat_gross - cat_refund
                categories.append(CategorySnapshot(category_id=category_id, gross_expense_minor=cat_gross, refund_minor=cat_refund, net_expense_minor=net, limit_minor=limit, remaining_minor=None if limit is None else limit - net))

            account_stmt = select(Account.id)
            if account_filter: account_stmt = account_stmt.where(Account.id.in_(account_filter))
            account_keys = list(session.scalars(account_stmt.order_by(Account.id)).all())
            accounts = []
            for account_id in account_keys:
                opening = int(session.scalar(select(func.coalesce(func.sum(TransactionEntry.amount_minor), 0)).join(FinancialTransaction).where(TransactionEntry.account_id == account_id, FinancialTransaction.occurred_at < start)) or 0)
                period_amounts = [row.amount_minor for row in transaction_rows if row.account_id == account_id]
                inflow = sum(value for value in period_amounts if value > 0)
                outflow = -sum(value for value in period_amounts if value < 0)
                accounts.append(AccountSnapshot(account_id=account_id, opening_balance_minor=opening, inflow_minor=inflow, outflow_minor=outflow, closing_balance_minor=opening + inflow - outflow))

            expected = int(session.scalar(select(func.coalesce(func.sum(IncomeExpectation.expected_minor), 0)).where(
                IncomeExpectation.due_date >= period_date,
                IncomeExpectation.due_date < end.astimezone(SHANGHAI).date(),
                IncomeExpectation.created_at <= _utc(as_of),
            )) or 0)
            received = int(session.scalar(select(func.coalesce(func.sum(IncomeExpectationMatch.matched_minor), 0)).join(IncomeExpectation).where(
                IncomeExpectation.due_date >= period_date,
                IncomeExpectation.due_date < end.astimezone(SHANGHAI).date(),
                IncomeExpectationMatch.created_at <= _utc(as_of),
            )) or 0)
            return MonthlySnapshot(
                period=period,
                as_of=_utc(as_of),
                budget_version_id=budget.id if budget else None,
                income_minor=ensure_aggregate(income),
                gross_expense_minor=ensure_aggregate(gross),
                refund_minor=ensure_aggregate(reductions),
                net_expense_minor=ensure_aggregate(gross - reductions),
                transfer_in_minor=ensure_aggregate(transfer_in),
                transfer_out_minor=ensure_aggregate(transfer_out),
                expected_income_minor=ensure_aggregate(expected),
                received_against_expectation_minor=ensure_aggregate(received),
                categories=categories,
                accounts=accounts,
            )
