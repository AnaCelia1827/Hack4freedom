"""Enforce database-level financial invariants.

Revision ID: 0003_financial_invariants
"""
from alembic import op


revision = "0003_financial_invariants"
down_revision = "0002_financial_foundation"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE FUNCTION bluejet_enforce_balanced_ledger() RETURNS trigger AS $$
        DECLARE
          target_transaction_id varchar(36);
          entry_count bigint;
          debit_total numeric;
          credit_total numeric;
        BEGIN
          IF TG_TABLE_NAME = 'ledger_transactions' THEN
            target_transaction_id := NEW.id;
          ELSE
            target_transaction_id := NEW.transaction_id;
          END IF;

          SELECT
            count(*),
            COALESCE(sum(amount_sats) FILTER (WHERE direction = 'DEBIT'), 0),
            COALESCE(sum(amount_sats) FILTER (WHERE direction = 'CREDIT'), 0)
          INTO entry_count, debit_total, credit_total
          FROM ledger_entries
          WHERE transaction_id = target_transaction_id;

          IF entry_count < 2 OR debit_total <> credit_total THEN
            RAISE EXCEPTION 'ledger transaction % is unbalanced', target_transaction_id;
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE CONSTRAINT TRIGGER ledger_transactions_balanced
        AFTER INSERT ON ledger_transactions
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION bluejet_enforce_balanced_ledger()
        """
    )
    op.execute(
        """
        CREATE CONSTRAINT TRIGGER ledger_entries_balanced
        AFTER INSERT ON ledger_entries
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION bluejet_enforce_balanced_ledger()
        """
    )


def downgrade():
    raise RuntimeError("financial persistence is forward-only; use a corrective migration")
