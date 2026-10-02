"""add examination marking infrastructure

Revision ID: 7b3e9a1c2d44
Revises: 9f2a1c7d6e11
"""
from alembic import op
import sqlalchemy as sa

revision = "7b3e9a1c2d44"
down_revision = "9f2a1c7d6e11"
branch_labels = None
depends_on = None


def _enum(name, values):
    return sa.Enum(*values, name=name, native_enum=False, length=max(map(len, values)))


def _timestamps():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "examinations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("academic_session_id", sa.Integer(), nullable=False),
        sa.Column("term_id", sa.Integer(), nullable=False),
        sa.Column("school_class_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("instructions", sa.Text()),
        sa.Column("examination_date", sa.Date()),
        sa.Column("duration_minutes", sa.Integer()),
        sa.Column("maximum_score", sa.Numeric(7, 2), nullable=False),
        sa.Column("status", _enum("examinationstatus", ["DRAFT", "PUBLISHED", "CLOSED"]), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["academic_session_id"], ["academic_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["term_id"], ["terms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_class_id"], ["classes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("school_id", "academic_session_id", "term_id", "school_class_id", "subject_id", "title", name="uq_exam_context_title"),
    )
    for col in ("school_id", "academic_session_id", "term_id", "school_class_id", "subject_id", "created_by_id"):
        op.create_index(f"ix_examinations_{col}", "examinations", [col])
    op.create_index("ix_examinations_status", "examinations", ["status"])

    op.create_table(
        "examination_questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("examination_id", sa.Integer(), nullable=False),
        sa.Column("question_number", sa.String(length=30), nullable=False),
        sa.Column("section", sa.String(length=100)),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", _enum("questiontype", ["OBJECTIVE", "SUBJECTIVE"]), nullable=False),
        sa.Column("maximum_marks", sa.Numeric(7, 2), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("instructions", sa.Text()),
        sa.Column("correct_option", sa.String(length=50)),
        sa.Column("expected_concepts", sa.Text()),
        sa.Column("key_points", sa.Text()),
        sa.Column("acceptable_alternatives", sa.Text()),
        sa.Column("partial_credit_guidance", sa.Text()),
        sa.Column("marking_guidance", sa.Text()),
        sa.Column("teacher_notes", sa.Text()),
        *_timestamps(),
        sa.ForeignKeyConstraint(["examination_id"], ["examinations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("examination_id", "question_number", name="uq_exam_question_number"),
        sa.UniqueConstraint("examination_id", "display_order", name="uq_exam_question_order"),
    )
    op.create_index("ix_examination_questions_examination_id", "examination_questions", ["examination_id"])

    op.create_table(
        "question_reference_materials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("material_type", _enum("referencematerialtype", ["TYPED_ANSWER", "MARKING_GUIDANCE", "UPLOAD", "HANDWRITTEN", "WORKED_SOLUTION"]), nullable=False),
        sa.Column("title", sa.String(length=200)),
        sa.Column("text_content", sa.Text()),
        sa.Column("original_file_path", sa.String(length=500)),
        sa.Column("original_filename", sa.String(length=255)),
        sa.Column("content_type", sa.String(length=120)),
        sa.Column("file_size", sa.Integer()),
        sa.Column("notes", sa.Text()),
        *_timestamps(),
        sa.ForeignKeyConstraint(["question_id"], ["examination_questions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_question_reference_materials_question_id", "question_reference_materials", ["question_id"])

    op.create_table(
        "examination_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("examination_id", sa.Integer(), nullable=False),
        sa.Column("file_type", _enum("examinationfiletype", ["QUESTION_PAPER"]), nullable=False),
        sa.Column("original_file_path", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120)),
        sa.Column("file_size", sa.Integer()),
        sa.Column("title", sa.String(length=200)),
        *_timestamps(),
        sa.ForeignKeyConstraint(["examination_id"], ["examinations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_examination_files_examination_id", "examination_files", ["examination_id"])

    op.create_table(
        "student_examination_scripts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("examination_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("original_file_path", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120)),
        sa.Column("file_size", sa.Integer()),
        sa.Column("status", _enum("scriptstatus", ["UPLOADED", "PROCESSING", "READY_FOR_MARKING", "AI_MARKED", "TEACHER_REVIEW", "APPROVED", "PROCESSING_FAILED", "MARKING_FAILED"]), nullable=False),
        sa.Column("processing_error", sa.Text()),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("approved_by_id", sa.Integer()),
        *_timestamps(),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["examination_id"], ["examinations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approved_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("examination_id", "student_id", name="uq_exam_student_script"),
    )
    for col in ("school_id", "examination_id", "student_id"):
        op.create_index(f"ix_student_examination_scripts_{col}", "student_examination_scripts", [col])
    op.create_index("ix_student_examination_scripts_status", "student_examination_scripts", ["status"])

    op.create_table(
        "student_question_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("script_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("extracted_text", sa.Text()),
        sa.Column("original_answer_image_path", sa.String(length=500)),
        sa.Column("page_number", sa.Integer()),
        sa.Column("answer_position", sa.String(length=100)),
        sa.Column("extraction_status", sa.String(length=30)),
        sa.Column("ai_proposed_score", sa.Numeric(7, 2)),
        sa.Column("ai_evidence", sa.Text()),
        sa.Column("ai_confidence", sa.Numeric(5, 4)),
        sa.Column("teacher_final_score", sa.Numeric(7, 2)),
        sa.Column("teacher_adjustment", sa.Numeric(7, 2)),
        sa.Column("teacher_review_notes", sa.Text()),
        sa.Column("review_status", _enum("reviewstatus", ["PENDING", "REVIEWED", "APPROVED"]), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["script_id"], ["student_examination_scripts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["examination_questions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("script_id", "question_id", name="uq_script_question_answer"),
    )
    op.create_index("ix_student_question_answers_script_id", "student_question_answers", ["script_id"])
    op.create_index("ix_student_question_answers_question_id", "student_question_answers", ["question_id"])
    op.create_index("ix_student_question_answers_review_status", "student_question_answers", ["review_status"])


def downgrade() -> None:
    op.drop_index("ix_student_question_answers_review_status", table_name="student_question_answers")
    op.drop_index("ix_student_question_answers_question_id", table_name="student_question_answers")
    op.drop_index("ix_student_question_answers_script_id", table_name="student_question_answers")
    op.drop_table("student_question_answers")
    op.drop_index("ix_student_examination_scripts_status", table_name="student_examination_scripts")
    for col in ("student_id", "examination_id", "school_id"):
        op.drop_index(f"ix_student_examination_scripts_{col}", table_name="student_examination_scripts")
    op.drop_table("student_examination_scripts")
    op.drop_index("ix_examination_files_examination_id", table_name="examination_files")
    op.drop_table("examination_files")
    op.drop_index("ix_question_reference_materials_question_id", table_name="question_reference_materials")
    op.drop_table("question_reference_materials")
    op.drop_index("ix_examination_questions_examination_id", table_name="examination_questions")
    op.drop_table("examination_questions")
    op.drop_index("ix_examinations_status", table_name="examinations")
    for col in ("created_by_id", "subject_id", "school_class_id", "term_id", "academic_session_id", "school_id"):
        op.drop_index(f"ix_examinations_{col}", table_name="examinations")
    op.drop_table("examinations")
