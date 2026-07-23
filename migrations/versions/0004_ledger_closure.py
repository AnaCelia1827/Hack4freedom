"""Close ledger transactions against late entries.

Revision ID: 0004_ledger_closure
"""
from alembic import op


revision = "0004_ledger_closure"
down_revision = "0003_financial_invariants"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE FUNCTION bluejet_reject_late_ledger_entry() RETURNS trigger AS $$
        DECLARE
          parent_created_in_current_transaction boolean;
        BEGIN
          SELECT xmin = pg_current_xact_id()::text::xid
          INTO parent_created_in_current_transaction
          FROM ledger_transactions
          WHERE id = NEW.transaction_id;

          IF NOT COALESCE(parent_created_in_current_transaction, false) THEN
            RAISE EXCEPTION 'ledger transaction % is already closed', NEW.transaction_id;
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER ledger_entries_same_transaction
        BEFORE INSERT ON ledger_entries
        FOR EACH ROW EXECUTE FUNCTION bluejet_reject_late_ledger_entry()
        """
    )


def downgrade():
    raise RuntimeError("financial persistence is forward-only; use a corrective migration")
