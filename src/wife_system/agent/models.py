"""Persistent P2 Agent run and pending-action records."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from wife_system.finance.db import Base
from wife_system.finance.models import UserScoped, new_uuid, utc_now


class AgentRunRecord(UserScoped, Base):
    __tablename__ = "agent_run"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "source_system", "source_event_digest",
            name="uq_run_user_source_event",
        ),
        UniqueConstraint("user_id", "id", name="uq_agent_run_user_id"),
        ForeignKeyConstraint(
            ["user_id", "pending_action_id"],
            ["pending_action.user_id", "pending_action.id"],
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
            name="fk_run_user_pending",
        ),
        CheckConstraint(
            "status IN ('running','success','error','paused','cancelled')",
            name="status",
        ),
        CheckConstraint("actor_id = user_id", name="actor_user"),
        CheckConstraint("attempt_no BETWEEN 1 AND 3", name="attempt"),
        CheckConstraint("action_schema_version > 0", name="schema"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    actor_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    source_system: Mapped[str] = mapped_column(String(32), nullable=False)
    source_event_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="running")
    pause_reason: Mapped[str | None] = mapped_column(String(64))
    pending_action_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    answer: Mapped[str | None] = mapped_column(Text)
    error_code: Mapped[str | None] = mapped_column(String(80))
    result_json: Mapped[str | None] = mapped_column(Text)
    events_json: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str | None] = mapped_column(String(120))
    module_id: Mapped[str] = mapped_column(String(64), nullable=False, default="daily_finance")
    module_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    profile_id: Mapped[str] = mapped_column(String(140), nullable=False, default="daily_finance.assistant@1")
    profile_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    action_schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class PendingActionRecord(UserScoped, Base):
    __tablename__ = "pending_action"
    __table_args__ = (
        UniqueConstraint("run_id", name="uq_pending_action_run_id"),
        UniqueConstraint("user_id", "id", name="uq_pending_action_user_id"),
        ForeignKeyConstraint(
            ["user_id", "run_id"],
            ["agent_run.user_id", "agent_run.id"],
            ondelete="RESTRICT",
            name="fk_pending_user_run",
        ),
        UniqueConstraint("confirmation_code", name="uq_pending_action_confirmation_code"),
        CheckConstraint(
            "status IN ('needs_input','needs_confirmation','committing','committed','expired','cancelled')",
            name="status",
        ),
        CheckConstraint("version_id > 0", name="version_positive"),
        CheckConstraint("actor_id = user_id", name="actor_user"),
        CheckConstraint("action_schema_version > 0", name="schema"),
        CheckConstraint("commit_attempt_no >= 0", name="commit_attempt_nonnegative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    actor_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    source_system: Mapped[str] = mapped_column(String(32), nullable=False)
    action_type: Mapped[str] = mapped_column(String(48), nullable=False)
    action_json: Mapped[str] = mapped_column(Text, nullable=False)
    missing_fields_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    resource_versions_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    confirmation_code: Mapped[str] = mapped_column(String(16), nullable=False)
    approval_grant_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    final_result_json: Mapped[str | None] = mapped_column(Text)
    module_id: Mapped[str] = mapped_column(String(64), nullable=False, default="daily_finance")
    profile_id: Mapped[str] = mapped_column(String(140), nullable=False, default="daily_finance.assistant@1")
    action_schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    commit_attempt_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    commit_lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
