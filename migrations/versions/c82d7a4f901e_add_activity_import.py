"""add persistent activity import

Revision ID: c82d7a4f901e
Revises: 7f3e2d1c9a4b
Create Date: 2026-09-19 00:00:00
"""

from __future__ import annotations

import unicodedata
from typing import Any, Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c82d7a4f901e"
down_revision: Union[str, Sequence[str], None] = "7f3e2d1c9a4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
MAX_MINOR = 999_999_999_999
POSTGRESQL_IDENTIFIER_MAX_LENGTH = 63
IMPORT_CANDIDATE_FK_NAME = "fk_activity_template_revision_import_candidate"


def _normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split()).casefold()


def _preflight(connection: sa.Connection) -> list[tuple[Any, str]]:
    rows = connection.execute(sa.text(
        "SELECT t.id, r.name, r.reference_minor "
        "FROM activity_template t LEFT JOIN activity_template_revision r "
        "ON r.id = t.current_revision_id ORDER BY t.id"
    )).all()
    values: list[tuple[Any, str]] = []
    seen: set[str] = set()
    for template_id, name, amount in rows:
        if name is None:
            raise RuntimeError("activity import migration preflight failed: missing current revision")
        normalized = _normalized(name)
        if not normalized or len(normalized) > 360 or normalized in seen:
            raise RuntimeError("activity import migration preflight failed: duplicate or invalid normalized name")
        if amount is not None and (not isinstance(amount, int) or amount < 0 or amount > MAX_MINOR):
            raise RuntimeError("activity import migration preflight failed: invalid reference amount")
        seen.add(normalized)
        values.append((template_id, normalized))
    return values


def _reference_checks() -> list[sa.CheckConstraint]:
    return [sa.CheckConstraint(
        "(reference_minor IS NULL AND reference_min_minor IS NULL AND reference_max_minor IS NULL) OR "
        "(reference_min_minor IS NOT NULL AND reference_max_minor IS NOT NULL "
        "AND reference_min_minor >= 0 AND reference_min_minor <= reference_max_minor "
        "AND reference_max_minor <= 999999999999 AND (reference_minor IS NULL OR "
        "(reference_minor = reference_min_minor AND reference_minor = reference_max_minor)))",
        name="reference_shape",
    )]


def upgrade() -> None:
    connection = op.get_bind()
    recreate = "always" if connection.dialect.name == "sqlite" else "auto"
    normalized_rows = _preflight(connection)

    op.create_table(
        "activity_import_batch",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("parser_version", sa.String(32), nullable=False),
        sa.Column("source_label", sa.String(120), nullable=True),
        sa.Column("content_key_version", sa.Integer(), nullable=False),
        sa.Column("content_digest", sa.String(128), nullable=False),
        sa.Column("preview_receipt_id", sa.Uuid(), nullable=False),
        sa.Column("commit_receipt_id", sa.Uuid(), nullable=True),
        sa.Column("selection_fingerprint", sa.String(64), nullable=True),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('previewed','committed')", name=op.f("ck_activity_import_batch_status")),
        sa.CheckConstraint("parser_version = 'activity-md-v1'", name=op.f("ck_activity_import_batch_parser_version")),
        sa.CheckConstraint("content_key_version > 0", name=op.f("ck_activity_import_batch_content_key_version_positive")),
        sa.CheckConstraint("version_id > 0", name=op.f("ck_activity_import_batch_version_positive")),
        sa.CheckConstraint("source_label IS NULL OR length(source_label) <= 120", name=op.f("ck_activity_import_batch_source_label_length")),
        sa.CheckConstraint(
            "(status = 'previewed' AND commit_receipt_id IS NULL AND committed_at IS NULL AND selection_fingerprint IS NULL) OR "
            "(status = 'committed' AND commit_receipt_id IS NOT NULL AND committed_at IS NOT NULL AND selection_fingerprint IS NOT NULL)",
            name=op.f("ck_activity_import_batch_commit_shape"),
        ),
        sa.ForeignKeyConstraint(["preview_receipt_id"], ["command_receipt.id"], ondelete="RESTRICT", name=op.f("fk_activity_import_batch_preview_receipt_id_command_receipt")),
        sa.ForeignKeyConstraint(["commit_receipt_id"], ["command_receipt.id"], ondelete="RESTRICT", name=op.f("fk_activity_import_batch_commit_receipt_id_command_receipt")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_activity_import_batch")),
        sa.UniqueConstraint("preview_receipt_id", name=op.f("uq_activity_import_batch_preview_receipt_id")),
        sa.UniqueConstraint("commit_receipt_id", name=op.f("uq_activity_import_batch_commit_receipt_id")),
    )
    op.create_index(op.f("ix_activity_import_batch_owner_id"), "activity_import_batch", ["owner_id"])

    op.create_table(
        "activity_import_candidate",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("source_heading", sa.String(120), nullable=False),
        sa.Column("source_line_start", sa.Integer(), nullable=False),
        sa.Column("source_line_end", sa.Integer(), nullable=False),
        sa.Column("block_digest", sa.String(128), nullable=False),
        sa.Column("name_normalized", sa.String(360), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("reference_minor", sa.BigInteger(), nullable=True),
        sa.Column("reference_min_minor", sa.BigInteger(), nullable=True),
        sa.Column("reference_max_minor", sa.BigInteger(), nullable=True),
        sa.Column("proposed_action", sa.String(16), nullable=False),
        sa.Column("target_template_id", sa.Uuid(), nullable=True),
        sa.Column("target_expected_version", sa.Integer(), nullable=True),
        sa.Column("issues_json", sa.Text(), nullable=False),
        sa.Column("decision", sa.String(8), nullable=True),
        sa.Column("result_template_id", sa.Uuid(), nullable=True),
        sa.Column("result_template_version", sa.Integer(), nullable=True),
        sa.CheckConstraint("ordinal BETWEEN 1 AND 50", name=op.f("ck_activity_import_candidate_ordinal")),
        sa.CheckConstraint("source_line_start >= 1 AND source_line_end >= source_line_start AND source_line_end <= 2000", name=op.f("ck_activity_import_candidate_source_lines")),
        sa.CheckConstraint("length(source_heading) BETWEEN 1 AND 120", name=op.f("ck_activity_import_candidate_heading_length")),
        sa.CheckConstraint("length(name_normalized) BETWEEN 1 AND 360", name=op.f("ck_activity_import_candidate_normalized_name_length")),
        sa.CheckConstraint("currency = 'CNY'", name=op.f("ck_activity_import_candidate_currency_cny")),
        sa.CheckConstraint("proposed_action IN ('create','revise','unchanged','conflict','unresolved')", name=op.f("ck_activity_import_candidate_proposed_action")),
        sa.CheckConstraint("(target_template_id IS NULL AND target_expected_version IS NULL) OR (target_template_id IS NOT NULL AND target_expected_version IS NOT NULL AND target_expected_version > 0)", name=op.f("ck_activity_import_candidate_target_shape")),
        sa.CheckConstraint("(decision IS NULL AND result_template_id IS NULL AND result_template_version IS NULL) OR (decision = 'skip' AND result_template_id IS NULL AND result_template_version IS NULL) OR (decision = 'accept' AND result_template_id IS NOT NULL AND result_template_version IS NOT NULL AND result_template_version > 0)", name=op.f("ck_activity_import_candidate_decision_shape")),
        sa.CheckConstraint(
            _reference_checks()[0].sqltext,
            name=op.f("ck_activity_import_candidate_reference_shape"),
        ),
        sa.ForeignKeyConstraint(["batch_id"], ["activity_import_batch.id"], ondelete="RESTRICT", name=op.f("fk_activity_import_candidate_batch_id_activity_import_batch")),
        sa.ForeignKeyConstraint(["target_template_id"], ["activity_template.id"], ondelete="RESTRICT", name=op.f("fk_activity_import_candidate_target_template_id_activity_template")),
        sa.ForeignKeyConstraint(["result_template_id"], ["activity_template.id"], ondelete="RESTRICT", name=op.f("fk_activity_import_candidate_result_template_id_activity_template")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_activity_import_candidate")),
        sa.UniqueConstraint("batch_id", "ordinal", name="uq_activity_import_candidate_batch_ordinal"),
    )

    with op.batch_alter_table("activity_template", recreate=recreate) as batch:
        batch.add_column(sa.Column("name_normalized", sa.String(360), nullable=True))
    for template_id, normalized in normalized_rows:
        connection.execute(sa.text("UPDATE activity_template SET name_normalized=:name WHERE id=:id"), {"name": normalized, "id": template_id})
    with op.batch_alter_table("activity_template", recreate=recreate) as batch:
        batch.alter_column("name_normalized", nullable=False, existing_type=sa.String(360))
        batch.create_check_constraint(op.f("ck_activity_template_normalized_name_length"), "length(name_normalized) BETWEEN 1 AND 360")
        batch.create_unique_constraint(op.f("uq_activity_template_name_normalized"), ["name_normalized"])

    with op.batch_alter_table("activity_template_revision", recreate=recreate) as batch:
        batch.add_column(sa.Column("reference_min_minor", sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column("reference_max_minor", sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column("source_import_candidate_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(IMPORT_CANDIDATE_FK_NAME, "activity_import_candidate", ["source_import_candidate_id"], ["id"], ondelete="RESTRICT")
    connection.execute(sa.text(
        "UPDATE activity_template_revision SET reference_min_minor=reference_minor, reference_max_minor=reference_minor WHERE reference_minor IS NOT NULL"
    ))
    with op.batch_alter_table("activity_template_revision", recreate=recreate) as batch:
        batch.create_check_constraint(op.f("ck_activity_template_revision_reference_shape"), _reference_checks()[0].sqltext)
    if connection.dialect.name == "sqlite":
        for table, columns in (
            ("activity_template_revision", ("reference_min_minor", "reference_max_minor")),
            ("activity_import_candidate", ("reference_minor", "reference_min_minor", "reference_max_minor")),
        ):
            for column in columns:
                with op.batch_alter_table(table, recreate="always") as batch:
                    batch.create_check_constraint(op.f(f"ck_{table}_{column}_integer_storage"), f"{column} IS NULL OR typeof({column}) = 'integer'")


def downgrade() -> None:
    recreate = "always" if op.get_bind().dialect.name == "sqlite" else "auto"
    with op.batch_alter_table("activity_template_revision", recreate=recreate) as batch:
        batch.drop_constraint(op.f("ck_activity_template_revision_reference_shape"), type_="check")
        if op.get_bind().dialect.name == "sqlite":
            batch.drop_constraint(op.f("ck_activity_template_revision_reference_max_minor_integer_storage"), type_="check")
            batch.drop_constraint(op.f("ck_activity_template_revision_reference_min_minor_integer_storage"), type_="check")
        batch.drop_constraint(IMPORT_CANDIDATE_FK_NAME, type_="foreignkey")
        batch.drop_column("source_import_candidate_id")
        batch.drop_column("reference_max_minor")
        batch.drop_column("reference_min_minor")
    with op.batch_alter_table("activity_template", recreate=recreate) as batch:
        batch.drop_constraint(op.f("uq_activity_template_name_normalized"), type_="unique")
        batch.drop_constraint(op.f("ck_activity_template_normalized_name_length"), type_="check")
        batch.drop_column("name_normalized")
    op.drop_table("activity_import_candidate")
    op.drop_index(op.f("ix_activity_import_batch_owner_id"), table_name="activity_import_batch")
    op.drop_table("activity_import_batch")
