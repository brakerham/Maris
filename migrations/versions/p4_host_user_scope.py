"""add trusted user scope to all P0-P3 business and workflow records

Revision ID: p4_host_user_scope
Revises: p4_host_identity
Create Date: 2026-09-20
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "p4_host_user_scope"
down_revision: Union[str, Sequence[str], None] = "p4_host_identity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCOPED_TABLES = (
    "account",
    "category",
    "command_receipt",
    "audit_event",
    "financial_transaction",
    "transaction_entry",
    "activity_template",
    "activity_template_revision",
    "activity_import_batch",
    "activity_import_candidate",
    "activity_occurrence",
    "activity_entry_allocation",
    "income_schedule",
    "income_schedule_version",
    "income_expectation",
    "income_expectation_match",
    "budget_plan",
    "budget_version",
    "budget_allocation",
    "agent_run",
    "pending_action",
)

# child table, local id column, parent table, parent id column, constraint name
SCOPED_RELATIONSHIPS = (
    ("audit_event", "command_receipt_id", "command_receipt", "id", "fk_audit_user_receipt"),
    ("financial_transaction", "related_transaction_id", "financial_transaction", "id", "fk_transaction_user_related"),
    ("financial_transaction", "command_receipt_id", "command_receipt", "id", "fk_transaction_user_receipt"),
    ("transaction_entry", "transaction_id", "financial_transaction", "id", "fk_entry_user_transaction"),
    ("transaction_entry", "account_id", "account", "id", "fk_entry_user_account"),
    ("transaction_entry", "category_id", "category", "id", "fk_entry_user_category"),
    ("activity_template", "current_revision_id", "activity_template_revision", "id", "fk_template_user_revision"),
    ("activity_template_revision", "template_id", "activity_template", "id", "fk_revision_user_template"),
    ("activity_template_revision", "source_import_candidate_id", "activity_import_candidate", "id", "fk_revision_user_candidate"),
    ("activity_import_batch", "preview_receipt_id", "command_receipt", "id", "fk_import_batch_user_preview"),
    ("activity_import_batch", "commit_receipt_id", "command_receipt", "id", "fk_import_batch_user_commit"),
    ("activity_import_candidate", "batch_id", "activity_import_batch", "id", "fk_candidate_user_batch"),
    ("activity_import_candidate", "target_template_id", "activity_template", "id", "fk_candidate_user_target"),
    ("activity_import_candidate", "result_template_id", "activity_template", "id", "fk_candidate_user_result"),
    ("activity_occurrence", "template_revision_id", "activity_template_revision", "id", "fk_occurrence_user_revision"),
    ("activity_entry_allocation", "occurrence_id", "activity_occurrence", "id", "fk_allocation_user_occurrence"),
    ("activity_entry_allocation", "expense_entry_id", "transaction_entry", "id", "fk_allocation_user_entry"),
    ("income_schedule", "current_version_id", "income_schedule_version", "id", "fk_schedule_user_version"),
    ("income_schedule_version", "schedule_id", "income_schedule", "id", "fk_schedule_version_user_schedule"),
    ("income_expectation", "schedule_version_id", "income_schedule_version", "id", "fk_expectation_user_schedule_ver"),
    ("income_expectation_match", "expectation_id", "income_expectation", "id", "fk_match_user_expectation"),
    ("income_expectation_match", "income_entry_id", "transaction_entry", "id", "fk_match_user_entry"),
    ("budget_version", "plan_id", "budget_plan", "id", "fk_budget_version_user_plan"),
    ("budget_allocation", "budget_version_id", "budget_version", "id", "fk_budget_alloc_user_version"),
    ("budget_allocation", "category_id", "category", "id", "fk_budget_alloc_user_category"),
    ("pending_action", "run_id", "agent_run", "id", "fk_pending_user_run"),
)

SCOPED_NATURAL_UNIQUES = (
    ("category", "uq_category_kind_name_normalized", "uq_category_user_kind_name", ("user_id", "kind", "name_normalized")),
    ("command_receipt", "uq_command_receipt_source_digest", "uq_receipt_user_source_digest", ("user_id", "source_system", "key_digest")),
    ("activity_template", "uq_activity_template_name_normalized", "uq_template_user_name", ("user_id", "name_normalized")),
    ("agent_run", "uq_agent_run_actor_source_event", "uq_run_user_source_event", ("user_id", "source_system", "source_event_digest")),
)


def _recreate_mode() -> str:
    return "always" if op.get_bind().dialect.name == "sqlite" else "auto"


def _bootstrap_user_id(connection: sa.Connection):
    rows = connection.execute(
        sa.text("SELECT id FROM app_user WHERE bootstrap_marker='bootstrap-owner' AND status='pending_setup'")
    ).scalars().all()
    if len(rows) != 1:
        raise RuntimeError("P4 user-scope migration requires exactly one pending bootstrap owner")
    return rows[0]


def _count(connection: sa.Connection, statement: str, **params: object) -> int:
    return int(connection.scalar(sa.text(statement), params) or 0)


def _validate_legacy_graph(connection: sa.Connection, bootstrap_user_id: object) -> None:
    legacy_owners: set[str] = set()
    for table, owner_column in (
        ("agent_run", "actor_id"),
        ("pending_action", "actor_id"),
        ("activity_import_batch", "owner_id"),
    ):
        legacy_owners.update(
            str(value)
            for value in connection.execute(
                sa.text(f"SELECT DISTINCT {owner_column} FROM {table} WHERE {owner_column} IS NOT NULL")
            ).scalars()
        )
    if len(legacy_owners) > 1:
        raise RuntimeError("P4 user-scope migration rejected contradictory legacy owners")
    for child, local_column, parent, remote_column, _ in SCOPED_RELATIONSHIPS:
        orphan_count = _count(
            connection,
            f"SELECT COUNT(*) FROM {child} c LEFT JOIN {parent} p "
            f"ON c.{local_column}=p.{remote_column} "
            f"WHERE c.{local_column} IS NOT NULL AND p.{remote_column} IS NULL",
        )
        if orphan_count:
            raise RuntimeError("P4 user-scope migration rejected orphaned legacy relationships")


def _validate_scoped_graph(connection: sa.Connection) -> None:
    for table in SCOPED_TABLES:
        if _count(connection, f"SELECT COUNT(*) FROM {table} WHERE user_id IS NULL"):
            raise RuntimeError("P4 user-scope migration could not safely backfill all rows")
    for child, local_column, parent, remote_column, _ in SCOPED_RELATIONSHIPS:
        mismatch_count = _count(
            connection,
            f"SELECT COUNT(*) FROM {child} c JOIN {parent} p "
            f"ON c.{local_column}=p.{remote_column} "
            f"WHERE c.{local_column} IS NOT NULL AND c.user_id <> p.user_id",
        )
        if mismatch_count:
            raise RuntimeError("P4 user-scope migration rejected cross-user legacy relationships")


def upgrade() -> None:
    connection = op.get_bind()
    bootstrap_user_id = _bootstrap_user_id(connection)
    _validate_legacy_graph(connection, bootstrap_user_id)

    # P0-P3 actor/owner values were local compatibility identities rather than
    # authenticated users. A single coherent legacy identity can be mapped to
    # the one frozen bootstrap owner; conflicting identities were rejected above.
    for table, owner_column in (
        ("agent_run", "actor_id"),
        ("pending_action", "actor_id"),
        ("activity_import_batch", "owner_id"),
    ):
        connection.execute(
            sa.text(f"UPDATE {table} SET {owner_column}=:user_id"),
            {"user_id": bootstrap_user_id},
        )

    for table in SCOPED_TABLES:
        op.add_column(table, sa.Column("user_id", sa.Uuid(), nullable=True))
        connection.execute(sa.text(f"UPDATE {table} SET user_id=:user_id"), {"user_id": bootstrap_user_id})
    _validate_scoped_graph(connection)

    recreate = _recreate_mode()
    replaced_by_table = {item[0]: item for item in SCOPED_NATURAL_UNIQUES}
    for table in SCOPED_TABLES:
        with op.batch_alter_table(table, recreate=recreate) as batch:
            batch.alter_column("user_id", existing_type=sa.Uuid(), nullable=False)
            batch.create_unique_constraint(f"uq_{table}_user_id", ["user_id", "id"])
            batch.create_foreign_key(
                f"fk_{table}_user", "app_user", ["user_id"], ["id"], ondelete="RESTRICT"
            )
            if table in replaced_by_table:
                _, old_name, new_name, columns = replaced_by_table[table]
                batch.drop_constraint(old_name, type_="unique")
                batch.create_unique_constraint(new_name, list(columns))
            if table == "activity_import_batch":
                batch.create_check_constraint("ck_import_batch_owner_user", "owner_id = user_id")
            elif table in {"agent_run", "pending_action"}:
                batch.create_check_constraint(f"ck_{table}_actor_user", "actor_id = user_id")

    for child, local_column, parent, remote_column, name in SCOPED_RELATIONSHIPS:
        with op.batch_alter_table(child, recreate=recreate) as batch:
            batch.create_foreign_key(
                name,
                parent,
                ["user_id", local_column],
                ["user_id", remote_column],
                ondelete="RESTRICT",
            )


def downgrade() -> None:
    recreate = _recreate_mode()
    for child, _, _, _, name in reversed(SCOPED_RELATIONSHIPS):
        with op.batch_alter_table(child, recreate=recreate) as batch:
            batch.drop_constraint(name, type_="foreignkey")

    replaced_by_table = {item[0]: item for item in SCOPED_NATURAL_UNIQUES}
    for table in reversed(SCOPED_TABLES):
        with op.batch_alter_table(table, recreate=recreate) as batch:
            batch.drop_constraint(f"fk_{table}_user", type_="foreignkey")
            if table == "activity_import_batch":
                batch.drop_constraint("ck_import_batch_owner_user", type_="check")
            elif table in {"agent_run", "pending_action"}:
                batch.drop_constraint(f"ck_{table}_actor_user", type_="check")
            if table in replaced_by_table:
                _, old_name, new_name, old_columns = replaced_by_table[table]
                batch.drop_constraint(new_name, type_="unique")
                if table == "category":
                    original_columns = ["kind", "name_normalized"]
                elif table == "command_receipt":
                    original_columns = ["source_system", "key_digest"]
                elif table == "activity_template":
                    original_columns = ["name_normalized"]
                else:
                    original_columns = ["actor_id", "source_system", "source_event_digest"]
                batch.create_unique_constraint(old_name, original_columns)
            batch.drop_constraint(f"uq_{table}_user_id", type_="unique")
            batch.drop_column("user_id")
