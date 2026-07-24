"""Persist human reviews and atomic payment obligations.

Revision ID: 0013_review_and_obligation
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_review_and_obligation"
down_revision = "0012_work_persistence"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "participant_sessions",
        sa.Column(
            "session_scope",
            sa.String(20),
            nullable=False,
            server_default="PARTICIPANT",
        ),
    )
    op.create_check_constraint(
        "ck_participant_sessions_scope",
        "participant_sessions",
        "session_scope IN ('PARTICIPANT', 'ADMIN')",
    )

    op.drop_constraint("ck_assignments_status", "assignments", type_="check")
    op.create_check_constraint(
        "ck_assignments_status",
        "assignments",
        "status IN ('RESERVED', 'IN_PROGRESS', 'SUBMITTED', 'UNDER_REVIEW', "
        "'CHANGES_REQUESTED', 'RESUBMITTED', 'APPROVED', 'REJECTED', "
        "'PAYMENT_PENDING', 'PAYMENT_PROCESSING', 'PAYMENT_FAILED', 'PAID', 'EXPIRED')",
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "submission_id",
            sa.String(36),
            sa.ForeignKey("submissions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "assignment_id",
            sa.String(36),
            sa.ForeignKey("assignments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("decision", sa.String(24), nullable=False),
        sa.Column("reason", sa.Text, nullable=False, server_default=""),
        sa.Column("previous_status", sa.String(24), nullable=False),
        sa.Column("new_status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("submission_id", name="uq_reviews_submission"),
        sa.CheckConstraint(
            "decision IN ('APPROVE', 'REQUEST_CHANGES', 'REJECT')",
            name="ck_reviews_decision",
        ),
        sa.CheckConstraint(
            "decision = 'APPROVE' OR length(trim(reason)) > 0",
            name="ck_reviews_reason_required",
        ),
    )
    op.create_index("ix_reviews_submission_id", "reviews", ["submission_id"])
    op.create_index("ix_reviews_assignment_id", "reviews", ["assignment_id"])
    op.create_index("ix_reviews_reviewer_user_id", "reviews", ["reviewer_user_id"])
    op.create_index(
        "uq_reviews_one_correction_per_assignment",
        "reviews",
        ["assignment_id"],
        unique=True,
        postgresql_where=sa.text("decision = 'REQUEST_CHANGES'"),
    )

    op.create_index(
        "ix_ledger_entries_transaction_id",
        "ledger_entries",
        ["transaction_id"],
    )
    op.create_index(
        "ix_payout_attempts_payment_obligation_id",
        "payout_attempts",
        ["payment_obligation_id"],
    )

    op.execute("GRANT SELECT, INSERT ON reviews TO bluejet_runtime")
    op.execute(
        "CREATE TRIGGER reviews_append_only_mutation BEFORE UPDATE OR DELETE ON reviews "
        "FOR EACH ROW EXECUTE FUNCTION bluejet_reject_append_only_mutation()"
    )
    op.execute(
        "CREATE TRIGGER reviews_append_only_truncate BEFORE TRUNCATE ON reviews "
        "FOR EACH STATEMENT EXECUTE FUNCTION bluejet_reject_append_only_mutation()"
    )
    op.execute(
        """
        CREATE FUNCTION bluejet_protect_payment_obligation() RETURNS trigger AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'payment_obligations cannot be deleted';
          END IF;
          IF NEW.assignment_id IS DISTINCT FROM OLD.assignment_id
             OR NEW.amount_sats IS DISTINCT FROM OLD.amount_sats
             OR NEW.mode IS DISTINCT FROM OLD.mode
             OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
            RAISE EXCEPTION 'payment obligation economic fields are immutable';
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        "CREATE TRIGGER payment_obligations_immutable_fields "
        "BEFORE UPDATE OR DELETE ON payment_obligations FOR EACH ROW "
        "EXECUTE FUNCTION bluejet_protect_payment_obligation()"
    )


def downgrade():
    raise RuntimeError("review and obligation persistence is forward-only; use a corrective migration")
