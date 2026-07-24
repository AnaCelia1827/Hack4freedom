"""Persist paid work, funding, exclusive reservations and private submissions.

Revision ID: 0012_work_persistence
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_work_persistence"
down_revision = "0011_phase23_hardening"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "companies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.String(1000), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "paid_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("instructions", sa.Text, nullable=False, server_default=""),
        sa.Column("module_id", sa.String(120), nullable=False),
        sa.Column("reward_sats", sa.BigInteger, nullable=False),
        sa.Column("slots", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("reward_sats > 0", name="ck_paid_tasks_positive_reward"),
        sa.CheckConstraint("slots = 1", name="ck_paid_tasks_one_slot"),
        sa.CheckConstraint("status IN ('DRAFT', 'PUBLISHED', 'CLOSED')", name="ck_paid_tasks_status"),
    )
    op.create_index("ix_paid_tasks_company_id", "paid_tasks", ["company_id"])
    op.create_table(
        "task_funding_reservations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("paid_tasks.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount_sats", sa.BigInteger, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="RESERVED"),
        sa.Column("ledger_transaction_id", sa.String(36), sa.ForeignKey("ledger_transactions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("task_id", name="uq_task_funding_reservations_task"),
        sa.UniqueConstraint("ledger_transaction_id", name="uq_task_funding_reservations_ledger_transaction_id"),
        sa.CheckConstraint("amount_sats > 0", name="ck_task_funding_reservations_positive_amount"),
        sa.CheckConstraint("status = 'RESERVED'", name="ck_task_funding_reservations_status"),
    )
    op.create_index("ix_task_funding_reservations_task_id", "task_funding_reservations", ["task_id"])
    op.create_table(
        "task_funding_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("reservation_id", sa.String(36), sa.ForeignKey("task_funding_reservations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("account", sa.String(120), nullable=False),
        sa.Column("amount_sats", sa.BigInteger, nullable=False),
        sa.Column("source_id", sa.String(36)),
        sa.CheckConstraint("amount_sats > 0", name="ck_task_funding_lines_positive_amount"),
    )
    op.create_index("ix_task_funding_lines_reservation_id", "task_funding_lines", ["reservation_id"])
    op.create_table(
        "assignments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("paid_tasks.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="RESERVED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('RESERVED', 'SUBMITTED', 'EXPIRED', 'APPROVED')", name="ck_assignments_status"),
    )
    op.create_index("ix_assignments_task_id", "assignments", ["task_id"])
    op.create_index("ix_assignments_user_id", "assignments", ["user_id"])
    op.create_table(
        "assignment_reservations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("assignment_id", sa.String(36), sa.ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("paid_tasks.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("reserved_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expired_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("assignment_id", name="uq_assignment_reservations_assignment"),
        sa.CheckConstraint("status IN ('ACTIVE', 'EXPIRED', 'CONSUMED')", name="ck_assignment_reservations_status"),
    )
    op.create_index("ix_assignment_reservations_task_id", "assignment_reservations", ["task_id"])
    op.create_index("ix_assignment_reservations_reserved_until", "assignment_reservations", ["reserved_until"])
    op.create_index(
        "uq_assignment_reservations_one_active_per_task",
        "assignment_reservations",
        ["task_id"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )
    op.create_table(
        "stored_objects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False, unique=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(80), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("private", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("scan_status", sa.String(20), nullable=False, server_default="QUARANTINED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("size_bytes BETWEEN 0 AND 10485760", name="ck_stored_objects_size"),
        sa.CheckConstraint("length(content_hash) = 64", name="ck_stored_objects_hash_length"),
        sa.CheckConstraint("private = true", name="ck_stored_objects_private"),
        sa.CheckConstraint("scan_status IN ('QUARANTINED', 'CLEAN', 'REJECTED')", name="ck_stored_objects_scan_status"),
    )
    op.create_index("ix_stored_objects_owner_user_id", "stored_objects", ["owner_user_id"])
    op.create_table(
        "submission_drafts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("assignment_id", sa.String(36), sa.ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("content", sa.Text, nullable=False, server_default=""),
        sa.Column("filename", sa.String(255), nullable=False, server_default="submission.txt"),
        sa.Column("mime_type", sa.String(80), nullable=False, server_default="text/plain"),
        sa.Column("private", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("assignment_id", name="uq_submission_drafts_assignment"),
        sa.CheckConstraint("private = true", name="ck_submission_drafts_private"),
    )
    op.create_index("ix_submission_drafts_assignment_id", "submission_drafts", ["assignment_id"])
    op.create_table(
        "submissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("assignment_id", sa.String(36), sa.ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False, server_default=""),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("stored_object_id", sa.String(36), sa.ForeignKey("stored_objects.id", ondelete="RESTRICT")),
        sa.Column("private", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("assignment_id", "version", name="uq_submissions_assignment_version"),
        sa.CheckConstraint("version > 0", name="ck_submissions_positive_version"),
        sa.CheckConstraint("length(content_hash) = 64", name="ck_submissions_hash_length"),
        sa.CheckConstraint("private = true", name="ck_submissions_private"),
    )
    op.create_index("ix_submissions_assignment_id", "submissions", ["assignment_id"])

    op.execute("GRANT SELECT, INSERT ON companies TO bluejet_runtime")
    op.execute("GRANT SELECT, INSERT, UPDATE ON paid_tasks, assignments, assignment_reservations, stored_objects, submission_drafts TO bluejet_runtime")
    op.execute("GRANT SELECT, INSERT ON task_funding_reservations, task_funding_lines, submissions TO bluejet_runtime")
    for table_name in ("task_funding_reservations", "task_funding_lines", "submissions"):
        op.execute(
            f"CREATE TRIGGER {table_name}_append_only_mutation BEFORE UPDATE OR DELETE ON {table_name} "
            "FOR EACH ROW EXECUTE FUNCTION bluejet_reject_append_only_mutation()"
        )
        op.execute(
            f"CREATE TRIGGER {table_name}_append_only_truncate BEFORE TRUNCATE ON {table_name} "
            "FOR EACH STATEMENT EXECUTE FUNCTION bluejet_reject_append_only_mutation()"
        )


def downgrade():
    raise RuntimeError("work persistence is forward-only; use a corrective migration")
