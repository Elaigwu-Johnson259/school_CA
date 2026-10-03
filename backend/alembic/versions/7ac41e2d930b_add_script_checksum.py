"""store uploaded student script checksum

Revision ID: 7ac41e2d930b
Revises: e9d3f7a1b4c2
Create Date: 2026-10-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "7ac41e2d930b"
down_revision = "e9d3f7a1b4c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("student_examination_scripts", sa.Column("checksum_sha256", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("student_examination_scripts", "checksum_sha256")
