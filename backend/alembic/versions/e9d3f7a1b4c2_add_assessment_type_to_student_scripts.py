"""add assessment type to student scripts

Revision ID: e9d3f7a1b4c2
Revises: 7b3e9a1c2d44
Create Date: 2026-10-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e9d3f7a1b4c2"
down_revision = "7b3e9a1c2d44"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("student_examination_scripts", sa.Column("assessment_type_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_student_examination_scripts_assessment_type_id"),
        "student_examination_scripts",
        ["assessment_type_id"],
    )
    op.create_foreign_key(
        "fk_student_scripts_assessment_type",
        "student_examination_scripts",
        "assessment_types",
        ["assessment_type_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_student_scripts_assessment_type",
        "student_examination_scripts",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_student_examination_scripts_assessment_type_id"), table_name="student_examination_scripts")
    op.drop_column("student_examination_scripts", "assessment_type_id")
