"""allow student script per assessment component

Revision ID: 6e1b7c94a230
Revises: 7ac41e2d930b
Create Date: 2026-10-02 00:00:00.000000

"""
from alembic import op


revision = "6e1b7c94a230"
down_revision = "7ac41e2d930b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_exam_student_script", "student_examination_scripts", type_="unique")
    op.create_unique_constraint(
        "uq_exam_student_assessment_script",
        "student_examination_scripts",
        ["examination_id", "student_id", "assessment_type_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_exam_student_assessment_script", "student_examination_scripts", type_="unique")
    op.create_unique_constraint(
        "uq_exam_student_script",
        "student_examination_scripts",
        ["examination_id", "student_id"],
    )
