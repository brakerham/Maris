"""enforce sqlite integer minor storage

Revision ID: 1377551283d0
Revises: bfc163b9b8e9
Create Date: 2026-09-16 21:14:59.019553

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '1377551283d0'
down_revision: Union[str, Sequence[str], None] = 'bfc163b9b8e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


MINOR_COLUMNS = (
    ("transaction_entry", "amount_minor", False),
    ("activity_template_revision", "reference_minor", True),
    ("activity_entry_allocation", "allocated_minor", False),
    ("income_schedule_version", "amount_minor", False),
    ("income_expectation", "expected_minor", False),
    ("income_expectation_match", "matched_minor", False),
    ("budget_allocation", "limit_minor", False),
)


def _constraint_name(table: str, column: str) -> str:
    return f"ck_{table}_{column}_integer_storage"


def upgrade() -> None:
    """Reject non-integer SQLite storage classes for every money column."""
    if op.get_bind().dialect.name != "sqlite":
        return
    for table, column, nullable in MINOR_COLUMNS:
        condition = f"typeof({column}) = 'integer'"
        if nullable:
            condition = f"{column} IS NULL OR {condition}"
        with op.batch_alter_table(table, recreate="always") as batch_op:
            batch_op.create_check_constraint(_constraint_name(table, column), condition)


def downgrade() -> None:
    """Remove SQLite-only storage-class guards for development rebuilds."""
    if op.get_bind().dialect.name != "sqlite":
        return
    for table, column, _ in reversed(MINOR_COLUMNS):
        with op.batch_alter_table(table, recreate="always") as batch_op:
            batch_op.drop_constraint(_constraint_name(table, column), type_="check")
