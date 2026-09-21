from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


BOOTSTRAP_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


def utc_now() -> datetime:
    return datetime.now(UTC)


def _reference_constraints() -> tuple[CheckConstraint, ...]:
    """Preserve exact, range (including equal endpoints), and unknown amounts."""
    shape = CheckConstraint(
        "(reference_minor IS NULL AND reference_min_minor IS NULL AND reference_max_minor IS NULL) OR "
        "(reference_min_minor IS NOT NULL AND reference_max_minor IS NOT NULL "
        "AND reference_min_minor >= 0 AND reference_min_minor <= reference_max_minor "
        "AND reference_max_minor <= 999999999999 "
        "AND (reference_minor IS NULL OR "
        "(reference_minor = reference_min_minor AND reference_minor = reference_max_minor)))",
        name="reference_shape",
    )
    storage = tuple(
        CheckConstraint(
            f"{column} IS NULL OR typeof({column}) = 'integer'",
            name=f"{column}_integer_storage",
        ).ddl_if(dialect="sqlite")
        for column in ("reference_minor", "reference_min_minor", "reference_max_minor")
    )
    return (shape, *storage)


class Versioned:
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class UserScoped:
    """Trusted owner column shared by P4 business persistence records."""

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)


class Account(UserScoped, Base, Versioned):
    __tablename__ = "account"
    __table_args__ = (CheckConstraint("currency = 'CNY'", name="currency_cny"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    __mapper_args__ = {"version_id_col": Versioned.version_id, "version_id_generator": False}


class Category(UserScoped, Base, Versioned):
    __tablename__ = "category"
    __table_args__ = (
        CheckConstraint("kind IN ('income','expense')", name="kind"),
        UniqueConstraint("user_id", "kind", "name_normalized", name="uq_category_user_kind_name"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    name_normalized: Mapped[str] = mapped_column(String(120), nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    __mapper_args__ = {"version_id_col": Versioned.version_id, "version_id_generator": False}


class CommandReceipt(UserScoped, Base):
    __tablename__ = "command_receipt"
    __table_args__ = (UniqueConstraint("user_id", "source_system", "key_digest", name="uq_receipt_user_source_digest"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    source_system: Mapped[str] = mapped_column(String(80), nullable=False)
    key_version: Mapped[int] = mapped_column(Integer, nullable=False)
    key_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    command_name: Mapped[str] = mapped_column(String(80), nullable=False)
    result_type: Mapped[str | None] = mapped_column(String(80))
    result_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    result_json: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class AuditEvent(UserScoped, Base):
    __tablename__ = "audit_event"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    command_receipt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("command_receipt.id", ondelete="RESTRICT"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    before_version: Mapped[int | None] = mapped_column(Integer)
    after_version: Mapped[int | None] = mapped_column(Integer)
    reason: Mapped[str | None] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class FinancialTransaction(UserScoped, Base):
    __tablename__ = "financial_transaction"
    __table_args__ = (
        CheckConstraint("kind IN ('opening_balance','income','expense','transfer','refund','reversal')", name="kind"),
        CheckConstraint("status = 'posted'", name="posted"),
        CheckConstraint("currency = 'CNY'", name="currency_cny"),
        CheckConstraint("relation_kind IS NULL OR relation_kind IN ('refund_of','reversal_of')", name="relation_kind"),
        Index("ix_financial_transaction_occurred_at_kind", "occurred_at", "kind"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="posted")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    related_transaction_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("financial_transaction.id", ondelete="RESTRICT"), index=True)
    relation_kind: Mapped[str | None] = mapped_column(String(24))
    command_receipt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("command_receipt.id", ondelete="RESTRICT"), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class TransactionEntry(UserScoped, Base):
    __tablename__ = "transaction_entry"
    __table_args__ = (
        UniqueConstraint("transaction_id", "line_no", name="uq_transaction_entry_transaction_line"),
        CheckConstraint("amount_minor <> 0", name="amount_nonzero"),
        CheckConstraint("entry_role IN ('account','expense','income','opening_equity')", name="role"),
        CheckConstraint(
            "(entry_role = 'account' AND account_id IS NOT NULL AND category_id IS NULL) OR "
            "(entry_role IN ('expense','income') AND account_id IS NULL AND category_id IS NOT NULL) OR "
            "(entry_role = 'opening_equity' AND account_id IS NULL AND category_id IS NULL)",
            name="target_shape",
        ),
        Index("ix_transaction_entry_account_transaction", "account_id", "transaction_id"),
        Index("ix_transaction_entry_category_transaction", "category_id", "transaction_id"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    transaction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("financial_transaction.id", ondelete="RESTRICT"), nullable=False)
    line_no: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_role: Mapped[str] = mapped_column(String(24), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("account.id", ondelete="RESTRICT"))
    category_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("category.id", ondelete="RESTRICT"))


class ActivityTemplate(UserScoped, Base, Versioned):
    __tablename__ = "activity_template"
    __table_args__ = (
        UniqueConstraint("user_id", "name_normalized", name="uq_template_user_name"),
        CheckConstraint("length(name_normalized) BETWEEN 1 AND 360", name="normalized_name_length"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    name_normalized: Mapped[str] = mapped_column(String(360), nullable=False)
    current_revision_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    __mapper_args__ = {"version_id_col": Versioned.version_id, "version_id_generator": False}


class ActivityTemplateRevision(UserScoped, Base):
    __tablename__ = "activity_template_revision"
    __table_args__ = (
        UniqueConstraint("template_id", "revision_no", name="uq_activity_template_revision_template_revision"),
        CheckConstraint("reference_minor IS NULL OR reference_minor >= 0", name="reference_nonnegative"),
        CheckConstraint("currency = 'CNY'", name="currency_cny"),
        *_reference_constraints(),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activity_template.id", ondelete="RESTRICT"), nullable=False)
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    reference_minor: Mapped[int | None] = mapped_column(BigInteger)
    reference_min_minor: Mapped[int | None] = mapped_column(BigInteger)
    reference_max_minor: Mapped[int | None] = mapped_column(BigInteger)
    source_import_candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("activity_import_candidate.id", ondelete="RESTRICT")
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class ActivityImportBatch(UserScoped, Base, Versioned):
    __tablename__ = "activity_import_batch"
    __table_args__ = (
        CheckConstraint("status IN ('previewed','committed')", name="status"),
        CheckConstraint("parser_version = 'activity-md-v1'", name="parser_version"),
        CheckConstraint("content_key_version > 0", name="content_key_version_positive"),
        CheckConstraint("version_id > 0", name="version_positive"),
        CheckConstraint("source_label IS NULL OR length(source_label) <= 120", name="source_label_length"),
        CheckConstraint("owner_id = user_id", name="owner_user"),
        CheckConstraint(
            "(status = 'previewed' AND commit_receipt_id IS NULL AND committed_at IS NULL "
            "AND selection_fingerprint IS NULL) OR "
            "(status = 'committed' AND commit_receipt_id IS NOT NULL AND committed_at IS NOT NULL "
            "AND selection_fingerprint IS NOT NULL)", name="commit_shape",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    owner_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="previewed")
    parser_version: Mapped[str] = mapped_column(String(32), nullable=False, default="activity-md-v1")
    source_label: Mapped[str | None] = mapped_column(String(120))
    content_key_version: Mapped[int] = mapped_column(Integer, nullable=False)
    content_digest: Mapped[str] = mapped_column(String(128), nullable=False)
    preview_receipt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("command_receipt.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    commit_receipt_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("command_receipt.id", ondelete="RESTRICT"), unique=True
    )
    selection_fingerprint: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __mapper_args__ = {"version_id_col": Versioned.version_id, "version_id_generator": False}


class ActivityImportCandidate(UserScoped, Base):
    __tablename__ = "activity_import_candidate"
    __table_args__ = (
        UniqueConstraint("batch_id", "ordinal", name="uq_activity_import_candidate_batch_ordinal"),
        CheckConstraint("ordinal BETWEEN 1 AND 50", name="ordinal"),
        CheckConstraint("source_line_start >= 1 AND source_line_end >= source_line_start AND source_line_end <= 2000", name="source_lines"),
        CheckConstraint("length(source_heading) BETWEEN 1 AND 120", name="heading_length"),
        CheckConstraint("length(name_normalized) BETWEEN 1 AND 360", name="normalized_name_length"),
        CheckConstraint("currency = 'CNY'", name="currency_cny"),
        CheckConstraint("proposed_action IN ('create','revise','unchanged','conflict','unresolved')", name="proposed_action"),
        CheckConstraint(
            "(target_template_id IS NULL AND target_expected_version IS NULL) OR "
            "(target_template_id IS NOT NULL AND target_expected_version IS NOT NULL AND target_expected_version > 0)",
            name="target_shape",
        ),
        CheckConstraint(
            "(decision IS NULL AND result_template_id IS NULL AND result_template_version IS NULL) OR "
            "(decision = 'skip' AND result_template_id IS NULL AND result_template_version IS NULL) OR "
            "(decision = 'accept' AND result_template_id IS NOT NULL "
            "AND result_template_version IS NOT NULL AND result_template_version > 0)",
            name="decision_shape",
        ),
        *_reference_constraints(),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    batch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activity_import_batch.id", ondelete="RESTRICT"), nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    source_heading: Mapped[str] = mapped_column(String(120), nullable=False)
    source_line_start: Mapped[int] = mapped_column(Integer, nullable=False)
    source_line_end: Mapped[int] = mapped_column(Integer, nullable=False)
    block_digest: Mapped[str] = mapped_column(String(128), nullable=False)
    name_normalized: Mapped[str] = mapped_column(String(360), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    reference_minor: Mapped[int | None] = mapped_column(BigInteger)
    reference_min_minor: Mapped[int | None] = mapped_column(BigInteger)
    reference_max_minor: Mapped[int | None] = mapped_column(BigInteger)
    proposed_action: Mapped[str] = mapped_column(String(16), nullable=False)
    target_template_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("activity_template.id", ondelete="RESTRICT"))
    target_expected_version: Mapped[int | None] = mapped_column(Integer)
    issues_json: Mapped[str] = mapped_column(Text, nullable=False)
    decision: Mapped[str | None] = mapped_column(String(8))
    result_template_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("activity_template.id", ondelete="RESTRICT"))
    result_template_version: Mapped[int | None] = mapped_column(Integer)


class ActivityOccurrence(UserScoped, Base, Versioned):
    __tablename__ = "activity_occurrence"
    __table_args__ = (CheckConstraint("status IN ('active','cancelled')", name="status"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    template_revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activity_template_revision.id", ondelete="RESTRICT"), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    __mapper_args__ = {"version_id_col": Versioned.version_id, "version_id_generator": False}


class ActivityEntryAllocation(UserScoped, Base):
    __tablename__ = "activity_entry_allocation"
    __table_args__ = (
        UniqueConstraint("occurrence_id", "expense_entry_id", name="uq_activity_allocation_occurrence_entry"),
        CheckConstraint("allocated_minor > 0", name="amount_positive"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    occurrence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activity_occurrence.id", ondelete="RESTRICT"), nullable=False)
    expense_entry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transaction_entry.id", ondelete="RESTRICT"), nullable=False, index=True)
    allocated_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class IncomeSchedule(UserScoped, Base, Versioned):
    __tablename__ = "income_schedule"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    __mapper_args__ = {"version_id_col": Versioned.version_id, "version_id_generator": False}


class IncomeScheduleVersion(UserScoped, Base):
    __tablename__ = "income_schedule_version"
    __table_args__ = (
        UniqueConstraint("schedule_id", "revision_no", name="uq_income_schedule_version_schedule_revision"),
        CheckConstraint("amount_minor > 0", name="amount_positive"),
        CheckConstraint("currency = 'CNY'", name="currency_cny"),
        CheckConstraint("due_day BETWEEN 1 AND 31", name="due_day"),
        CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="effective_range"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    schedule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("income_schedule.id", ondelete="RESTRICT"), nullable=False)
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    due_day: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class IncomeExpectation(UserScoped, Base):
    __tablename__ = "income_expectation"
    __table_args__ = (
        UniqueConstraint("schedule_version_id", "due_date", name="uq_income_expectation_version_due_date"),
        CheckConstraint("expected_minor > 0", name="amount_positive"),
        CheckConstraint("status IN ('pending','partial','matched')", name="status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    schedule_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("income_schedule_version.id", ondelete="RESTRICT"), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    expected_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class IncomeExpectationMatch(UserScoped, Base):
    __tablename__ = "income_expectation_match"
    __table_args__ = (CheckConstraint("matched_minor > 0", name="amount_positive"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    expectation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("income_expectation.id", ondelete="RESTRICT"), nullable=False, index=True)
    income_entry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transaction_entry.id", ondelete="RESTRICT"), nullable=False, unique=True)
    matched_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class BudgetPlan(UserScoped, Base, Versioned):
    __tablename__ = "budget_plan"
    __table_args__ = (
        CheckConstraint("currency = 'CNY'", name="currency_cny"),
        CheckConstraint("timezone = 'Asia/Shanghai'", name="timezone"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    timezone: Mapped[str] = mapped_column(String(40), nullable=False, default="Asia/Shanghai")
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    __mapper_args__ = {"version_id_col": Versioned.version_id, "version_id_generator": False}


class BudgetVersion(UserScoped, Base):
    __tablename__ = "budget_version"
    __table_args__ = (
        UniqueConstraint("plan_id", "period", "version_no", name="uq_budget_version_plan_period_version"),
        CheckConstraint("version_no > 0", name="version_positive"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("budget_plan.id", ondelete="RESTRICT"), nullable=False)
    period: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    adjustment_reason: Mapped[str | None] = mapped_column(String(240))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class BudgetAllocation(UserScoped, Base):
    __tablename__ = "budget_allocation"
    __table_args__ = (
        UniqueConstraint("budget_version_id", "category_id", name="uq_budget_allocation_version_category"),
        CheckConstraint("limit_minor >= 0", name="limit_nonnegative"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    budget_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("budget_version.id", ondelete="RESTRICT"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("category.id", ondelete="RESTRICT"), nullable=False)
    limit_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)


# Cyclic current-version pointers are explicit but added after both tables exist.
ActivityTemplate.__table__.append_constraint(
    ForeignKeyConstraint(
        ["current_revision_id"],
        ["activity_template_revision.id"],
        name="fk_activity_template_current_revision",
        use_alter=True,
    )
)
IncomeSchedule.__table__.append_constraint(
    ForeignKeyConstraint(
        ["current_version_id"],
        ["income_schedule_version.id"],
        name="fk_income_schedule_current_version",
        use_alter=True,
    )
)
