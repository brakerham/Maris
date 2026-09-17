"""add agent run and pending action

Revision ID: 7f3e2d1c9a4b
Revises: 1377551283d0
Create Date: 2026-09-16 23:58:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from wife_system.agent import models as agent_models  # noqa: F401 - autogenerate metadata


revision: str = "7f3e2d1c9a4b"
down_revision: Union[str, Sequence[str], None] = "1377551283d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_run",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("source_system", sa.String(length=32), nullable=False),
        sa.Column("source_event_digest", sa.String(length=64), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("pause_reason", sa.String(length=64), nullable=True),
        sa.Column("pending_action_id", sa.Uuid(), nullable=True),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("events_json", sa.Text(), nullable=True),
        sa.Column("model_name", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('running','success','error','paused')",
            name=op.f("ck_agent_run_status"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_run")),
        sa.UniqueConstraint(
            "actor_id", "source_system", "source_event_digest",
            name="uq_agent_run_actor_source_event",
        ),
    )
    op.create_index(op.f("ix_agent_run_actor_id"), "agent_run", ["actor_id"], unique=False)
    op.create_index(op.f("ix_agent_run_conversation_id"), "agent_run", ["conversation_id"], unique=False)
    op.create_table(
        "pending_action",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("source_system", sa.String(length=32), nullable=False),
        sa.Column("action_type", sa.String(length=48), nullable=False),
        sa.Column("action_json", sa.Text(), nullable=False),
        sa.Column("missing_fields_json", sa.Text(), nullable=False),
        sa.Column("resource_versions_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.Column("confirmation_code", sa.String(length=16), nullable=False),
        sa.Column("approval_grant_id", sa.Uuid(), nullable=True),
        sa.Column("final_result_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('needs_input','needs_confirmation','committing','committed','expired','cancelled')",
            name=op.f("ck_pending_action_status"),
        ),
        sa.CheckConstraint("version_id > 0", name=op.f("ck_pending_action_version_positive")),
        sa.ForeignKeyConstraint(
            ["run_id"], ["agent_run.id"],
            name=op.f("fk_pending_action_run_id_agent_run"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pending_action")),
        sa.UniqueConstraint("run_id", name="uq_pending_action_run_id"),
        sa.UniqueConstraint("confirmation_code", name="uq_pending_action_confirmation_code"),
    )
    op.create_index(op.f("ix_pending_action_actor_id"), "pending_action", ["actor_id"], unique=False)
    op.create_index(op.f("ix_pending_action_conversation_id"), "pending_action", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_pending_action_run_id"), "pending_action", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_pending_action_run_id"), table_name="pending_action")
    op.drop_index(op.f("ix_pending_action_conversation_id"), table_name="pending_action")
    op.drop_index(op.f("ix_pending_action_actor_id"), table_name="pending_action")
    op.drop_table("pending_action")
    op.drop_index(op.f("ix_agent_run_conversation_id"), table_name="agent_run")
    op.drop_index(op.f("ix_agent_run_actor_id"), table_name="agent_run")
    op.drop_table("agent_run")
