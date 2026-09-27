"""P4-A conversation, memory, setting, and host idempotency records."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from wife_system.finance.db import Base
from wife_system.finance.models import new_uuid, utc_now


class ConversationRecord(Base):
    __tablename__ = "conversation"
    __table_args__ = (
        UniqueConstraint("user_id", "id", name="uq_conversation_user_id"),
        CheckConstraint("status IN ('active','archived')", name="status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    module_id: Mapped[str] = mapped_column(String(64), nullable=False)
    profile_id: Mapped[str] = mapped_column(String(140), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class ConversationMessageRecord(Base):
    __tablename__ = "conversation_message"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "conversation_id"],
            ["conversation.user_id", "conversation.id"],
            ondelete="RESTRICT",
            name="fk_message_user_conversation",
        ),
        ForeignKeyConstraint(
            ["user_id", "run_id"],
            ["agent_run.user_id", "agent_run.id"],
            ondelete="RESTRICT",
            name="fk_message_user_run",
        ),
        UniqueConstraint(
            "user_id", "run_id", "run_sequence",
            name="uq_message_user_run_sequence",
        ),
        CheckConstraint(
            "(run_id IS NULL AND run_sequence IS NULL) OR "
            "(run_id IS NOT NULL AND run_sequence IS NOT NULL)",
            name="run_sequence_shape",
        ),
        CheckConstraint("role IN ('user','assistant','tool','system')", name="role"),
        CheckConstraint("sensitivity IN ('private','restricted')", name="sensitivity"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    run_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), index=True)
    run_sequence: Mapped[int | None] = mapped_column(Integer)
    tool_call_id: Mapped[str | None] = mapped_column(String(140))
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    sensitivity: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MemoryCandidateRecord(Base):
    __tablename__ = "memory_candidate"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "memory_item_id"],
            ["memory_item.user_id", "memory_item.id"],
            ondelete="RESTRICT",
            name="fk_memory_candidate_user_item",
        ),
        CheckConstraint("kind IN ('preference','constraint','goal','communication_style')", name="kind"),
        CheckConstraint("sensitivity IN ('private','restricted')", name="sensitivity"),
        CheckConstraint("status IN ('pending','confirmed','rejected','expired')", name="status"),
        CheckConstraint("version_id > 0", name="version_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_namespace: Mapped[str] = mapped_column(String(140), nullable=False)
    target_namespace: Mapped[str] = mapped_column(String(140), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)
    tags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    source_type: Mapped[str] = mapped_column(String(48), nullable=False)
    source_ref_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    sensitivity: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    proposed_by_profile_id: Mapped[str] = mapped_column(String(140), nullable=False)
    proposed_by_profile_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    memory_item_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    audit_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class MemoryItemRecord(Base):
    __tablename__ = "memory_item"
    __table_args__ = (
        UniqueConstraint("user_id", "id", name="uq_memory_item_user_id"),
        ForeignKeyConstraint(
            ["user_id", "superseded_by_id"],
            ["memory_item.user_id", "memory_item.id"],
            ondelete="RESTRICT",
            name="fk_memory_item_user_superseded",
        ),
        CheckConstraint("kind IN ('preference','constraint','goal','communication_style')", name="kind"),
        CheckConstraint("sensitivity IN ('private','restricted')", name="sensitivity"),
        CheckConstraint(
            "status IN ('active','deleted','superseded','invalidated')", name="status"
        ),
        CheckConstraint("version_id > 0", name="version_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    namespace: Mapped[str] = mapped_column(String(140), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)
    tags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    source_type: Mapped[str] = mapped_column(String(48), nullable=False)
    source_ref_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    sensitivity: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_by_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    audit_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class ModuleSettingRecord(Base):
    __tablename__ = "module_setting"
    __table_args__ = (
        UniqueConstraint("user_id", "module_id", "key", name="uq_setting_user_module_key"),
        CheckConstraint("version_id > 0", name="version_positive"),
        CheckConstraint("schema_version > 0", name="schema_version_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    module_id: Mapped[str] = mapped_column(String(64), nullable=False)
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class HostRequestReceiptRecord(Base):
    __tablename__ = "host_request_receipt"
    __table_args__ = (
        UniqueConstraint("user_id", "operation", "key_digest", name="uq_host_receipt_user_operation_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    operation: Mapped[str] = mapped_column(String(80), nullable=False)
    key_version: Mapped[int] = mapped_column(Integer, nullable=False)
    key_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    result_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
