"""role based authentication and results workflow

Revision ID: 9f2a1c7d6e11
Revises: 4dc4f1df9355
"""
from alembic import op
import sqlalchemy as sa

revision = "9f2a1c7d6e11"
down_revision = "4dc4f1df9355"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "email",
            existing_type=sa.String(length=200),
            nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "email",
            existing_type=sa.String(length=200),
            nullable=False,
        )
