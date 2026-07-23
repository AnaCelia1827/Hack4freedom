"""Harden runtime privileges and append-only tables.

Revision ID: 0005_runtime_role_hardening
"""
from alembic import op


revision = "0005_runtime_role_hardening"
down_revision = "0004_ledger_closure"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bluejet_runtime') THEN
            CREATE ROLE bluejet_runtime NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
          END IF;
        END
        $$
        """
    )
    op.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
    op.execute("REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM bluejet_runtime")
    op.execute("GRANT USAGE ON SCHEMA public TO bluejet_runtime")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON outbox_events, inbox_events, payment_obligations, payout_attempts "
        "TO bluejet_runtime"
    )
    op.execute(
        "GRANT SELECT, INSERT ON audit_events, ledger_transactions, ledger_entries TO bluejet_runtime"
    )
    op.execute(
        """
        CREATE TRIGGER audit_events_append_only_truncate
        BEFORE TRUNCATE ON audit_events
        FOR EACH STATEMENT EXECUTE FUNCTION bluejet_reject_append_only_mutation()
        """
    )
    op.execute(
        """
        CREATE TRIGGER ledger_transactions_append_only_truncate
        BEFORE TRUNCATE ON ledger_transactions
        FOR EACH STATEMENT EXECUTE FUNCTION bluejet_reject_append_only_mutation()
        """
    )
    op.execute(
        """
        CREATE TRIGGER ledger_entries_append_only_truncate
        BEFORE TRUNCATE ON ledger_entries
        FOR EACH STATEMENT EXECUTE FUNCTION bluejet_reject_append_only_mutation()
        """
    )


def downgrade():
    raise RuntimeError("financial and audit persistence is forward-only; use a corrective migration")
