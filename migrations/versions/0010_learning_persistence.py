"""Persist learning progress, append-only attempts and SkillEvidence.

Revision ID: 0010_learning_persistence
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_learning_persistence"
down_revision = "0009_onboarding_owner_hardening"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "learning_enrollments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("course_id", sa.String(120), nullable=False),
        sa.Column("course_version", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="IN_PROGRESS"),
        sa.Column("progress", sa.Integer, nullable=False, server_default="0"),
        sa.Column("attempt_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("user_id", "course_id", "course_version", name="uq_learning_enrollments_user_course_version"),
        sa.CheckConstraint("status IN ('IN_PROGRESS', 'COMPLETED')", name="ck_learning_enrollments_status"),
        sa.CheckConstraint("progress BETWEEN 0 AND 100", name="ck_learning_enrollments_progress"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_learning_enrollments_attempt_count"),
    )
    op.create_index("ix_learning_enrollments_user_id", "learning_enrollments", ["user_id"])
    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("enrollment_id", sa.String(36), sa.ForeignKey("learning_enrollments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("module_id", sa.String(120), nullable=False),
        sa.Column("assessment_version", sa.String(40), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("attempt_number", sa.Integer, nullable=False),
        sa.Column("answers_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("enrollment_id", "attempt_number", name="uq_quiz_attempts_enrollment_number"),
        sa.CheckConstraint("score BETWEEN 0 AND 100", name="ck_quiz_attempts_score"),
        sa.CheckConstraint("length(answers_hash) = 64", name="ck_quiz_attempts_answers_hash"),
    )
    op.create_index("ix_quiz_attempts_enrollment_id", "quiz_attempts", ["enrollment_id"])
    op.create_table(
        "skill_evidence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("module_id", sa.String(120), nullable=False),
        sa.Column("assessment_version", sa.String(40), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("quiz_attempt_id", sa.String(36), sa.ForeignKey("quiz_attempts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "module_id", "assessment_version", name="uq_skill_evidence_user_module_version"),
        sa.UniqueConstraint("quiz_attempt_id", name="uq_skill_evidence_quiz_attempt"),
        sa.CheckConstraint("score BETWEEN 80 AND 100", name="ck_skill_evidence_passing_score"),
    )
    op.create_index("ix_skill_evidence_user_id", "skill_evidence", ["user_id"])
    op.create_table(
        "learning_notes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("course_id", sa.String(120), nullable=False),
        sa.Column("lesson_id", sa.String(120), nullable=False),
        sa.Column("content", sa.Text, nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "course_id", "lesson_id", name="uq_learning_notes_user_lesson"),
    )
    op.create_index("ix_learning_notes_user_id", "learning_notes", ["user_id"])
    op.create_table(
        "learning_activity_submissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("course_id", sa.String(120), nullable=False),
        sa.Column("activity_id", sa.String(120), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="SUBMITTED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "course_id", "activity_id", name="uq_learning_activity_user_activity"),
        sa.CheckConstraint("status = 'SUBMITTED'", name="ck_learning_activity_submitted"),
    )
    op.create_index("ix_learning_activity_submissions_user_id", "learning_activity_submissions", ["user_id"])
    op.execute("GRANT SELECT, INSERT, UPDATE ON learning_enrollments, learning_notes TO bluejet_runtime")
    op.execute("GRANT SELECT, INSERT ON quiz_attempts, skill_evidence, learning_activity_submissions TO bluejet_runtime")
    for table_name in ("quiz_attempts", "skill_evidence"):
        op.execute(
            f"""
            CREATE TRIGGER {table_name}_append_only_mutation
            BEFORE UPDATE OR DELETE ON {table_name}
            FOR EACH ROW EXECUTE FUNCTION bluejet_reject_append_only_mutation()
            """
        )
        op.execute(
            f"""
            CREATE TRIGGER {table_name}_append_only_truncate
            BEFORE TRUNCATE ON {table_name}
            FOR EACH STATEMENT EXECUTE FUNCTION bluejet_reject_append_only_mutation()
            """
        )


def downgrade():
    raise RuntimeError("learning persistence is forward-only; use a corrective migration")
