"""create P4 host identity records and the pending bootstrap owner

Revision ID: p4_host_identity
Revises: c82d7a4f901e
Create Date: 2026-09-20
"""

from __future__ import annotations

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from wife_system.finance.models import BOOTSTRAP_USER_ID


revision: str = "p4_host_identity"
down_revision: Union[str, Sequence[str], None] = "c82d7a4f901e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_owner_ids(connection: sa.Connection) -> set[uuid.UUID]:
    """Return legacy owner identities without exposing row contents in errors."""
    owners: set[uuid.UUID] = set()
    for table_name, column_name in (
        ("agent_run", "actor_id"),
        ("pending_action", "actor_id"),
        ("activity_import_batch", "owner_id"),
    ):
        rows = connection.execute(
            sa.text(f"SELECT DISTINCT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL")
        ).scalars()
        owners.update(uuid.UUID(str(value)) for value in rows)
    return owners


def upgrade() -> None:
    connection = op.get_bind()
    owners = _existing_owner_ids(connection)
    if len(owners) > 1:
        raise RuntimeError("P4 identity migration rejected contradictory legacy owners")
    bootstrap_user_id = BOOTSTRAP_USER_ID

    op.create_table(
        "app_user",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("handle_normalized", sa.String(32), nullable=True),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("bootstrap_marker", sa.String(32), nullable=True),
        sa.Column("initialized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending_setup','active','deactivated')",
            name=op.f("ck_app_user_status"),
        ),
        sa.CheckConstraint("version_id > 0", name=op.f("ck_app_user_version_positive")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_app_user")),
        sa.UniqueConstraint("handle_normalized", name="uq_app_user_handle"),
        sa.UniqueConstraint("bootstrap_marker", name="uq_app_user_bootstrap"),
        sa.UniqueConstraint("id", "status", name="uq_app_user_id_status"),
    )
    user_table = sa.table(
        "app_user",
        sa.column("id", sa.Uuid()),
        sa.column("handle_normalized", sa.String()),
        sa.column("status", sa.String()),
        sa.column("bootstrap_marker", sa.String()),
        sa.column("version_id", sa.Integer()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    connection.execute(
        user_table.insert().values(
            id=bootstrap_user_id,
            handle_normalized=None,
            status="pending_setup",
            bootstrap_marker="bootstrap-owner",
            version_id=1,
            created_at=sa.func.now(),
        )
    )

    op.create_table(
        "password_credential",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("algorithm", sa.String(32), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="RESTRICT", name="fk_credential_user"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_password_credential")),
        sa.UniqueConstraint("user_id", name="uq_credential_user"),
    )
    op.create_table(
        "device_session",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("device_name", sa.String(80), nullable=False),
        sa.Column("platform", sa.String(24), nullable=False),
        sa.Column("access_digest", sa.String(64), nullable=False),
        sa.Column("access_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rotation_counter", sa.Integer(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("platform IN ('windows_desktop','api_test')", name=op.f("ck_device_session_platform")),
        sa.CheckConstraint("rotation_counter >= 0", name=op.f("ck_device_session_rotation")),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="RESTRICT", name="fk_device_session_user"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_device_session")),
        sa.UniqueConstraint("access_digest", name="uq_device_session_access"),
        sa.UniqueConstraint("user_id", "id", name="uq_device_session_user_id"),
    )
    op.create_index("ix_device_session_user", "device_session", ["user_id"])
    op.create_table(
        "session_refresh_token",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("token_digest", sa.String(64), nullable=False),
        sa.Column("rotation", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("rotation >= 0", name=op.f("ck_session_refresh_token_rotation")),
        sa.CheckConstraint("status IN ('active','rotated','revoked')", name=op.f("ck_session_refresh_token_status")),
        sa.ForeignKeyConstraint(
            ["user_id", "session_id"], ["device_session.user_id", "device_session.id"],
            ondelete="RESTRICT", name="fk_refresh_user_session",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_session_refresh_token")),
        sa.UniqueConstraint("token_digest", name="uq_refresh_token_digest"),
    )
    op.create_index("ix_refresh_session", "session_refresh_token", ["session_id"])
    op.create_index("ix_refresh_user", "session_refresh_token", ["user_id"])
    op.create_table(
        "channel_binding_code",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("code_digest", sa.String(64), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("attempts BETWEEN 0 AND 5", name=op.f("ck_channel_binding_code_attempts")),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="RESTRICT", name="fk_binding_code_user"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_channel_binding_code")),
        sa.UniqueConstraint("code_digest", name="uq_binding_code_digest"),
    )
    op.create_index("ix_binding_code_user", "channel_binding_code", ["user_id"])
    op.create_table(
        "channel_identity_binding",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("provider_account_digest", sa.String(64), nullable=False),
        sa.Column("external_subject_digest", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('active','revoked')", name=op.f("ck_channel_identity_binding_status")),
        sa.CheckConstraint("version_id > 0", name=op.f("ck_channel_identity_binding_version")),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="RESTRICT", name="fk_identity_binding_user"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_channel_identity_binding")),
        sa.UniqueConstraint("user_id", "id", name="uq_identity_binding_user_id"),
    )
    op.create_index("ix_identity_binding_user", "channel_identity_binding", ["user_id"])
    active = sa.text("status = 'active'")
    op.create_index(
        "uq_binding_active_subject", "channel_identity_binding",
        ["channel", "external_subject_digest"], unique=True,
        sqlite_where=active, postgresql_where=active,
    )
    op.create_table(
        "channel_binding_audit",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("binding_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("provider_account_digest", sa.String(64), nullable=True),
        sa.Column("external_subject_digest", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="RESTRICT", name="fk_binding_audit_user"),
        sa.ForeignKeyConstraint(
            ["user_id", "binding_id"],
            ["channel_identity_binding.user_id", "channel_identity_binding.id"],
            ondelete="RESTRICT", name="fk_audit_user_binding",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_channel_binding_audit")),
    )
    op.create_index("ix_binding_audit_user", "channel_binding_audit", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_binding_audit_user", table_name="channel_binding_audit")
    op.drop_table("channel_binding_audit")
    op.drop_index("uq_binding_active_subject", table_name="channel_identity_binding")
    op.drop_index("ix_identity_binding_user", table_name="channel_identity_binding")
    op.drop_table("channel_identity_binding")
    op.drop_index("ix_binding_code_user", table_name="channel_binding_code")
    op.drop_table("channel_binding_code")
    op.drop_index("ix_refresh_user", table_name="session_refresh_token")
    op.drop_index("ix_refresh_session", table_name="session_refresh_token")
    op.drop_table("session_refresh_token")
    op.drop_index("ix_device_session_user", table_name="device_session")
    op.drop_table("device_session")
    op.drop_table("password_credential")
    op.drop_table("app_user")
