"""Add financial persistence and append-only controls.

Revision ID: 0002_financial_foundation
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_financial_foundation"
down_revision = "0001_platform"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "payment_obligations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("assignment_id", sa.String(36), nullable=False, unique=True),
        sa.Column("amount_sats", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("mode", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("amount_sats > 0", name="ck_payment_obligations_positive_amount"),
        sa.CheckConstraint("status IN ('OPEN', 'CLEARING', 'SETTLED')", name="ck_payment_obligations_status"),
        sa.CheckConstraint("mode IN ('MOCK', 'SANDBOX', 'REAL')", name="ck_payment_obligations_mode"),
    )
    op.create_table(
        "payout_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("payment_obligation_id", sa.String(36), sa.ForeignKey("payment_obligations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False, unique=True),
        sa.Column("payment_hash", sa.String(128), unique=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("mode", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("status IN ('CREATED', 'VALIDATED', 'PROCESSING', 'AMBIGUOUS', 'SETTLED', 'FAILED', 'EXPIRED')", name="ck_payout_attempts_status"),
        sa.CheckConstraint("mode IN ('MOCK', 'SANDBOX', 'REAL')", name="ck_payout_attempts_mode"),
    )
    op.create_index(
        "uq_payout_attempts_one_active_per_obligation",
        "payout_attempts",
        ["payment_obligation_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('CREATED', 'VALIDATED', 'PROCESSING', 'AMBIGUOUS')"),
    )
    op.create_table(
        "ledger_transactions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("reference_id", sa.String(255), nullable=False, unique=True),
        sa.Column("mode", sa.String(10), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("mode IN ('MOCK', 'SANDBOX', 'REAL')", name="ck_ledger_transactions_mode"),
    )
    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("transaction_id", sa.String(36), sa.ForeignKey("ledger_transactions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("account", sa.String(120), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("amount_sats", sa.BigInteger(), nullable=False),
        sa.Column("source_id", sa.String(36)),
        sa.CheckConstraint("direction IN ('DEBIT', 'CREDIT')", name="ck_ledger_entries_direction"),
        sa.CheckConstraint("amount_sats > 0", name="ck_ledger_entries_positive_amount"),
    )
    op.execute(
        """
        CREATE FUNCTION bluejet_reject_append_only_mutation() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION '% is append-only', TG_TABLE_NAME;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    for table in ("audit_events", "ledger_transactions", "ledger_entries"):
        op.execute(
            f"CREATE TRIGGER {table}_append_only BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION bluejet_reject_append_only_mutation()"
        )


def downgrade():
    raise RuntimeError("financial and audit persistence is forward-only; use a corrective migration")
