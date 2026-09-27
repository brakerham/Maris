"""create P4 conversations, memory, settings, receipts, and workflow state

Revision ID: p4_host_state
Revises: p4_host_user_scope
Create Date: 2026-09-20
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "p4_host_state"
down_revision: Union[str, Sequence[str], None] = "p4_host_user_scope"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _recreate_mode() -> str:
    return "always" if op.get_bind().dialect.name == "sqlite" else "auto"


def _assert_sqlite_foreign_keys(connection: sa.Connection) -> None:
    """Fail the migration if a paired SQLite rebuild leaves any broken edge."""
    if connection.dialect.name != "sqlite":
        return
    violations = connection.execute(sa.text("PRAGMA foreign_key_check")).fetchall()
    if violations:
        raise RuntimeError("P4 workflow rebuild left invalid foreign-key references")


def _create_state_tables() -> None:
    op.create_table(
        "conversation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("module_id", sa.String(64), nullable=False),
        sa.Column("profile_id", sa.String(140), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('active','archived')", name=op.f("ck_conversation_status")),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="RESTRICT", name="fk_conversation_user"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation")),
        sa.UniqueConstraint("user_id", "id", name="uq_conversation_user_id"),
    )
    op.create_index("ix_conversation_user", "conversation", ["user_id"])
    op.create_index("ix_conversation_recent", "conversation", ["user_id", "module_id", "profile_id", "last_message_at"])

    op.create_table(
        "conversation_message",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("run_sequence", sa.Integer(), nullable=True),
        sa.Column("tool_call_id", sa.String(140), nullable=True),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_digest", sa.String(64), nullable=False),
        sa.Column("sensitivity", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("role IN ('user','assistant','tool','system')", name=op.f("ck_conversation_message_role")),
        sa.CheckConstraint("sensitivity IN ('private','restricted')", name=op.f("ck_conversation_message_sensitivity")),
        sa.CheckConstraint(
            "(run_id IS NULL AND run_sequence IS NULL) OR "
            "(run_id IS NOT NULL AND run_sequence IS NOT NULL)",
            name="ck_conversation_message_run_sequence_shape",
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "conversation_id"], ["conversation.user_id", "conversation.id"],
            ondelete="RESTRICT", name="fk_message_user_conversation",
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "run_id"], ["agent_run.user_id", "agent_run.id"],
            ondelete="RESTRICT", name="fk_message_user_run",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation_message")),
        sa.UniqueConstraint(
            "user_id", "run_id", "run_sequence",
            name="uq_message_user_run_sequence",
        ),
    )
    op.create_index("ix_message_user", "conversation_message", ["user_id"])
    op.create_index("ix_message_conversation", "conversation_message", ["conversation_id", "created_at", "id"])

    op.create_table(
        "memory_candidate",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("source_namespace", sa.String(140), nullable=False),
        sa.Column("target_namespace", sa.String(140), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("value_json", sa.Text(), nullable=False),
        sa.Column("tags_json", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(48), nullable=False),
        sa.Column("source_ref_digest", sa.String(64), nullable=False),
        sa.Column("sensitivity", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("proposed_by_profile_id", sa.String(140), nullable=False),
        sa.Column("proposed_by_profile_version", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("memory_item_id", sa.Uuid(), nullable=True),
        sa.Column("audit_id", sa.Uuid(), nullable=True),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.CheckConstraint("kind IN ('preference','constraint','goal','communication_style')", name=op.f("ck_memory_candidate_kind")),
        sa.CheckConstraint("sensitivity IN ('private','restricted')", name=op.f("ck_memory_candidate_sensitivity")),
        sa.CheckConstraint("status IN ('pending','confirmed','rejected','expired')", name=op.f("ck_memory_candidate_status")),
        sa.CheckConstraint("version_id > 0", name=op.f("ck_memory_candidate_version_positive")),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="RESTRICT", name="fk_memory_candidate_user"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memory_candidate")),
    )
    op.create_index("ix_memory_candidate_user", "memory_candidate", ["user_id", "status", "expires_at"])

    op.create_table(
        "memory_item",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("namespace", sa.String(140), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("value_json", sa.Text(), nullable=False),
        sa.Column("tags_json", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(48), nullable=False),
        sa.Column("source_ref_digest", sa.String(64), nullable=False),
        sa.Column("sensitivity", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_by_id", sa.Uuid(), nullable=True),
        sa.Column("audit_id", sa.Uuid(), nullable=False),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.CheckConstraint("kind IN ('preference','constraint','goal','communication_style')", name=op.f("ck_memory_item_kind")),
        sa.CheckConstraint("sensitivity IN ('private','restricted')", name=op.f("ck_memory_item_sensitivity")),
        sa.CheckConstraint(
            "status IN ('active','deleted','superseded','invalidated')",
            name=op.f("ck_memory_item_status"),
        ),
        sa.CheckConstraint("version_id > 0", name=op.f("ck_memory_item_version_positive")),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="RESTRICT", name="fk_memory_item_user"),
        sa.ForeignKeyConstraint(
            ["user_id", "superseded_by_id"], ["memory_item.user_id", "memory_item.id"],
            ondelete="RESTRICT", name="fk_memory_item_user_superseded",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memory_item")),
        sa.UniqueConstraint("user_id", "id", name="uq_memory_item_user_id"),
    )
    op.create_index("ix_memory_item_namespace", "memory_item", ["namespace"])
    op.create_index("ix_memory_item_lookup", "memory_item", ["user_id", "namespace", "status", "kind"])
    with op.batch_alter_table("memory_candidate", recreate=_recreate_mode()) as batch:
        batch.create_foreign_key(
            "fk_memory_candidate_user_item",
            "memory_item",
            ["user_id", "memory_item_id"],
            ["user_id", "id"],
            ondelete="RESTRICT",
        )

    op.create_table(
        "module_setting",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("module_id", sa.String(64), nullable=False),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("value_json", sa.Text(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version_id > 0", name=op.f("ck_module_setting_version_positive")),
        sa.CheckConstraint("schema_version > 0", name=op.f("ck_module_setting_schema_version_positive")),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="RESTRICT", name="fk_module_setting_user"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_module_setting")),
        sa.UniqueConstraint("user_id", "module_id", "key", name="uq_setting_user_module_key"),
    )
    op.create_index("ix_module_setting_user", "module_setting", ["user_id"])

    op.create_table(
        "host_request_receipt",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("operation", sa.String(80), nullable=False),
        sa.Column("key_version", sa.Integer(), nullable=False),
        sa.Column("key_digest", sa.String(64), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="RESTRICT", name="fk_host_receipt_user"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_host_request_receipt")),
        sa.UniqueConstraint("user_id", "operation", "key_digest", name="uq_host_receipt_user_operation_key"),
    )
    op.create_index("ix_host_receipt_user", "host_request_receipt", ["user_id"])


def _backfill_legacy_conversations(connection: sa.Connection) -> None:
    rows = connection.execute(sa.text(
        "SELECT user_id, conversation_id, MIN(source_system) AS channel, MIN(created_at) AS created_at "
        "FROM ("
        "SELECT user_id, conversation_id, source_system, created_at FROM agent_run "
        "UNION ALL "
        "SELECT user_id, conversation_id, source_system, created_at FROM pending_action"
        ") legacy GROUP BY user_id, conversation_id"
    )).mappings()
    for row in rows:
        connection.execute(
            sa.text(
                "INSERT INTO conversation "
                "(id,user_id,channel,module_id,profile_id,status,last_message_at,created_at) "
                "VALUES (:id,:user_id,:channel,'daily_finance','daily_finance.assistant@1','active',NULL,:created_at)"
            ),
            {
                "id": str(row["conversation_id"]),
                "user_id": str(row["user_id"]),
                "channel": row["channel"],
                "created_at": row["created_at"],
            },
        )


def upgrade() -> None:
    _create_state_tables()
    connection = op.get_bind()
    _backfill_legacy_conversations(connection)

    for column in (
        sa.Column("module_id", sa.String(64), nullable=True),
        sa.Column("module_version", sa.String(32), nullable=True),
        sa.Column("profile_id", sa.String(140), nullable=True),
        sa.Column("profile_version", sa.String(32), nullable=True),
        sa.Column("attempt_no", sa.Integer(), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("action_schema_version", sa.Integer(), nullable=True),
    ):
        op.add_column("agent_run", column)
    for column in (
        sa.Column("module_id", sa.String(64), nullable=True),
        sa.Column("profile_id", sa.String(140), nullable=True),
        sa.Column("action_schema_version", sa.Integer(), nullable=True),
        sa.Column("commit_attempt_no", sa.Integer(), nullable=True),
        sa.Column("commit_lease_expires_at", sa.DateTime(timezone=True), nullable=True),
    ):
        op.add_column("pending_action", column)

    connection.execute(sa.text(
        "UPDATE agent_run SET module_id='daily_finance', module_version='1.0.0', "
        "profile_id='daily_finance.assistant@1', "
        "profile_version='1.0.0', attempt_no=1, action_schema_version=1"
    ))
    connection.execute(sa.text(
        "UPDATE pending_action SET module_id='daily_finance', profile_id='daily_finance.assistant@1', "
        "action_schema_version=1, commit_attempt_no=0"
    ))
    if connection.dialect.name == "sqlite":
        connection.execute(sa.text(
            "UPDATE agent_run SET lease_expires_at=datetime(updated_at, '+60 seconds') WHERE status='running'"
        ))
    else:
        connection.execute(sa.text(
            "UPDATE agent_run SET lease_expires_at=updated_at + INTERVAL '60 seconds' WHERE status='running'"
        ))

    recreate = _recreate_mode()
    with op.batch_alter_table("agent_run", recreate=recreate) as batch:
        batch.alter_column("module_id", existing_type=sa.String(64), nullable=False)
        batch.alter_column("module_version", existing_type=sa.String(32), nullable=False)
        batch.alter_column("profile_id", existing_type=sa.String(140), nullable=False)
        batch.alter_column("profile_version", existing_type=sa.String(32), nullable=False)
        batch.alter_column("attempt_no", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("action_schema_version", existing_type=sa.Integer(), nullable=False)
        batch.drop_constraint(op.f("ck_agent_run_status"), type_="check")
        batch.create_check_constraint(op.f("ck_agent_run_status"), "status IN ('running','success','error','paused','cancelled')")
        batch.create_check_constraint(op.f("ck_agent_run_attempt"), "attempt_no BETWEEN 1 AND 3")
        batch.create_check_constraint(op.f("ck_agent_run_schema"), "action_schema_version > 0")
        batch.create_foreign_key(
            "fk_run_user_conversation", "conversation",
            ["user_id", "conversation_id"], ["user_id", "id"], ondelete="RESTRICT",
        )
        batch.create_foreign_key(
            "fk_run_user_pending", "pending_action",
            ["user_id", "pending_action_id"], ["user_id", "id"],
            ondelete="RESTRICT", deferrable=True, initially="DEFERRED",
        )
    with op.batch_alter_table("pending_action", recreate=recreate) as batch:
        batch.alter_column("module_id", existing_type=sa.String(64), nullable=False)
        batch.alter_column("profile_id", existing_type=sa.String(140), nullable=False)
        batch.alter_column("action_schema_version", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("commit_attempt_no", existing_type=sa.Integer(), nullable=False)
        batch.create_check_constraint(op.f("ck_pending_action_schema"), "action_schema_version > 0")
        batch.create_check_constraint(
            op.f("ck_pending_action_commit_attempt_nonnegative"),
            "commit_attempt_no >= 0",
        )
        batch.create_foreign_key(
            "fk_pending_user_conversation", "conversation",
            ["user_id", "conversation_id"], ["user_id", "id"], ondelete="RESTRICT",
        )
    _assert_sqlite_foreign_keys(connection)


def downgrade() -> None:
    connection = op.get_bind()
    recreate = _recreate_mode()
    # The reverse edge is removed before pending_action is rebuilt or its
    # compatibility columns are changed.  This is required by PostgreSQL and
    # keeps the SQLite pair free of a dangling circular reference.
    with op.batch_alter_table("agent_run", recreate=recreate) as batch:
        batch.drop_constraint("fk_run_user_pending", type_="foreignkey")

    with op.batch_alter_table("pending_action", recreate=recreate) as batch:
        batch.drop_constraint("fk_pending_user_conversation", type_="foreignkey")
        batch.drop_constraint(op.f("ck_pending_action_commit_attempt_nonnegative"), type_="check")
        batch.drop_constraint(op.f("ck_pending_action_schema"), type_="check")
        batch.drop_column("commit_lease_expires_at")
        batch.drop_column("commit_attempt_no")
        batch.drop_column("action_schema_version")
        batch.drop_column("profile_id")
        batch.drop_column("module_id")
    connection.execute(sa.text(
        "UPDATE agent_run SET status='error', "
        "error_code=CASE WHEN error_code IS NULL THEN 'cancelled' ELSE error_code END, "
        "pause_reason=NULL WHERE status='cancelled'"
    ))
    with op.batch_alter_table("agent_run", recreate=recreate) as batch:
        batch.drop_constraint("fk_run_user_conversation", type_="foreignkey")
        batch.drop_constraint(op.f("ck_agent_run_schema"), type_="check")
        batch.drop_constraint(op.f("ck_agent_run_attempt"), type_="check")
        batch.drop_constraint(op.f("ck_agent_run_status"), type_="check")
        batch.create_check_constraint(op.f("ck_agent_run_status"), "status IN ('running','success','error','paused')")
        batch.drop_column("action_schema_version")
        batch.drop_column("lease_expires_at")
        batch.drop_column("attempt_no")
        batch.drop_column("profile_version")
        batch.drop_column("profile_id")
        batch.drop_column("module_version")
        batch.drop_column("module_id")
    _assert_sqlite_foreign_keys(connection)

    op.drop_index("ix_host_receipt_user", table_name="host_request_receipt")
    op.drop_table("host_request_receipt")
    op.drop_index("ix_module_setting_user", table_name="module_setting")
    op.drop_table("module_setting")
    op.drop_index("ix_memory_item_lookup", table_name="memory_item")
    op.drop_index("ix_memory_item_namespace", table_name="memory_item")
    with op.batch_alter_table("memory_candidate", recreate=recreate) as batch:
        batch.drop_constraint("fk_memory_candidate_user_item", type_="foreignkey")
    op.drop_table("memory_item")
    op.drop_index("ix_memory_candidate_user", table_name="memory_candidate")
    op.drop_table("memory_candidate")
    op.drop_index("ix_message_conversation", table_name="conversation_message")
    op.drop_index("ix_message_user", table_name="conversation_message")
    op.drop_table("conversation_message")
    op.drop_index("ix_conversation_recent", table_name="conversation")
    op.drop_index("ix_conversation_user", table_name="conversation")
    op.drop_table("conversation")
