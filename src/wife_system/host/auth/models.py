from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from wife_system.finance.db import Base
from wife_system.finance.models import new_uuid, utc_now


class AppUser(Base):
    __tablename__ = "app_user"
    __table_args__ = (
        CheckConstraint("status IN ('pending_setup','active','deactivated')", name="status"),
        CheckConstraint("version_id > 0", name="version_positive"),
        UniqueConstraint("bootstrap_marker", name="uq_app_user_bootstrap_marker"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    handle: Mapped[str | None] = mapped_column("handle_normalized", String(32), unique=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending_setup")
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    bootstrap_marker: Mapped[str | None] = mapped_column(String(32))
    initialized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class PasswordCredential(Base):
    __tablename__ = "password_credential"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(32), nullable=False, default="argon2id")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class DeviceSession(Base):
    __tablename__ = "device_session"
    __table_args__ = (
        CheckConstraint("platform IN ('windows_desktop','api_test')", name="platform"),
        CheckConstraint("rotation_counter >= 0", name="rotation_counter_nonnegative"),
        UniqueConstraint("user_id", "id", name="uq_device_session_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False, index=True)
    device_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    device_name: Mapped[str] = mapped_column(String(80), nullable=False)
    platform: Mapped[str] = mapped_column(String(24), nullable=False)
    access_digest: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    access_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    absolute_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rotation_counter: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class SessionRefreshToken(Base):
    __tablename__ = "session_refresh_token"
    __table_args__ = (
        CheckConstraint("status IN ('active','rotated','revoked')", name="status"),
        CheckConstraint("rotation >= 0", name="rotation_nonnegative"),
        ForeignKeyConstraint(
            ["user_id", "session_id"],
            ["device_session.user_id", "device_session.id"],
            ondelete="RESTRICT",
            name="fk_refresh_token_user_session",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    token_digest: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    rotation: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ChannelBindingCode(Base):
    __tablename__ = "channel_binding_code"
    __table_args__ = (
        CheckConstraint("attempts BETWEEN 0 AND 5", name="attempts"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    code_digest: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class ChannelIdentityBinding(Base):
    __tablename__ = "channel_identity_binding"
    __table_args__ = (
        CheckConstraint("status IN ('active','revoked')", name="status"),
        CheckConstraint("version_id > 0", name="version_positive"),
        UniqueConstraint("user_id", "id", name="uq_identity_binding_user_id"),
        Index(
            "uq_channel_identity_active",
            "channel",
            "external_subject_digest",
            unique=True,
            sqlite_where=text("status = 'active'"),
            postgresql_where=text("status = 'active'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_account_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    external_subject_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ChannelBindingAudit(Base):
    __tablename__ = "channel_binding_audit"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "binding_id"],
            ["channel_identity_binding.user_id", "channel_identity_binding.id"],
            ondelete="RESTRICT",
            name="fk_audit_user_binding",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False, index=True)
    binding_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_account_digest: Mapped[str | None] = mapped_column(String(64))
    external_subject_digest: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
