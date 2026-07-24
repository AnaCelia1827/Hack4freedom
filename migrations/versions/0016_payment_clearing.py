"""Persist SANDBOX payout clearing, reconciliation and receipts.

Revision ID: 0016_payment_clearing
"""

from alembic import op
import sqlalchemy as sa


revision = "0016_payment_clearing"
down_revision = "0015_identity_rbac"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("payout_attempts", sa.Column("invoice_hash", sa.String(64)))
    op.add_column("payout_attempts", sa.Column("invoice_network", sa.String(20)))
    op.add_column("payout_attempts", sa.Column("invoice_amount_sats", sa.BigInteger()))
    op.add_column("payout_attempts", sa.Column("invoice_expires_at", sa.DateTime(timezone=True)))
    op.add_column("payout_attempts", sa.Column("failure_code", sa.String(80)))
    op.add_column(
        "payout_attempts",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_check_constraint(
        "ck_payout_attempts_invoice_hash",
        "payout_attempts",
        "invoice_hash IS NULL OR invoice_hash ~ '^[0-9a-f]{64}$'",
    )
    op.create_check_constraint(
        "ck_payout_attempts_payment_hash",
        "payout_attempts",
        "payment_hash IS NULL OR payment_hash ~ '^[0-9a-f]{64}$'",
    )
    op.create_check_constraint(
        "ck_payout_attempts_invoice_amount",
        "payout_attempts",
        "invoice_amount_sats IS NULL OR invoice_amount_sats > 0",
    )

    op.create_table(
        "provider_payments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "payout_attempt_id",
            sa.String(36),
            sa.ForeignKey("payout_attempts.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("payment_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("provider_reference", sa.String(160)),
        sa.Column("mode", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reconciled_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('PROCESSING', 'AMBIGUOUS', 'SETTLED', 'FAILED')",
            name="ck_provider_payments_status",
        ),
        sa.CheckConstraint(
            "mode IN ('MOCK', 'SANDBOX', 'REAL')",
            name="ck_provider_payments_mode",
        ),
        sa.CheckConstraint(
            "payment_hash ~ '^[0-9a-f]{64}$'",
            name="ck_provider_payments_payment_hash",
        ),
    )
    op.create_index(
        "ix_provider_payments_payout_attempt_id",
        "provider_payments",
        ["payout_attempt_id"],
    )

    op.create_table(
        "provider_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("provider_event_id", sa.String(160), nullable=False),
        sa.Column(
            "payout_attempt_id",
            sa.String(36),
            sa.ForeignKey("payout_attempts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "provider", "provider_event_id", name="uq_provider_events_provider_event"
        ),
        sa.CheckConstraint(
            "event_type IN ('AMBIGUOUS', 'SETTLED', 'FAILED')",
            name="ck_provider_events_type",
        ),
        sa.CheckConstraint(
            "payload_hash ~ '^[0-9a-f]{64}$'",
            name="ck_provider_events_payload_hash",
        ),
    )
    op.create_index(
        "ix_provider_events_payout_attempt_id",
        "provider_events",
        ["payout_attempt_id"],
    )

    op.create_table(
        "payment_receipts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "payment_obligation_id",
            sa.String(36),
            sa.ForeignKey("payment_obligations.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "payout_attempt_id",
            sa.String(36),
            sa.ForeignKey("payout_attempts.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "ledger_transaction_id",
            sa.String(36),
            sa.ForeignKey("ledger_transactions.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column("receipt_number", sa.String(80), nullable=False, unique=True),
        sa.Column("assignment_id", sa.String(36), nullable=False),
        sa.Column("amount_sats", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("mode", sa.String(10), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount_sats > 0", name="ck_payment_receipts_positive_amount"),
        sa.CheckConstraint("status = 'SETTLED'", name="ck_payment_receipts_status"),
        sa.CheckConstraint(
            "mode IN ('MOCK', 'SANDBOX', 'REAL')",
            name="ck_payment_receipts_mode",
        ),
    )
    op.create_index(
        "ix_payment_receipts_payment_obligation_id",
        "payment_receipts",
        ["payment_obligation_id"],
    )
    op.create_index(
        "ix_payment_receipts_payout_attempt_id",
        "payment_receipts",
        ["payout_attempt_id"],
    )

    op.execute("DROP TRIGGER payment_obligations_immutable_fields ON payment_obligations")
    op.execute("DROP FUNCTION bluejet_protect_payment_obligation()")
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
          IF NEW.status IS DISTINCT FROM OLD.status THEN
            IF OLD.status = 'OPEN' AND NEW.status = 'CLEARING' THEN
              IF NOT EXISTS (
                SELECT 1 FROM payout_attempts
                WHERE payment_obligation_id = OLD.id
                  AND status IN ('CREATED', 'VALIDATED', 'PROCESSING', 'AMBIGUOUS')
              ) THEN
                RAISE EXCEPTION 'OPEN to CLEARING requires an active payout attempt';
              END IF;
            ELSIF OLD.status = 'CLEARING' AND NEW.status = 'SETTLED' THEN
              IF NOT EXISTS (
                SELECT 1 FROM payout_attempts
                WHERE payment_obligation_id = OLD.id AND status = 'SETTLED'
              ) THEN
                RAISE EXCEPTION 'CLEARING to SETTLED requires a settled payout attempt';
              END IF;
            ELSIF OLD.status = 'CLEARING' AND NEW.status = 'OPEN' THEN
              IF EXISTS (
                SELECT 1 FROM payout_attempts
                WHERE payment_obligation_id = OLD.id
                  AND status IN ('CREATED', 'VALIDATED', 'PROCESSING', 'AMBIGUOUS')
              ) OR NOT EXISTS (
                SELECT 1 FROM payout_attempts
                WHERE payment_obligation_id = OLD.id AND status = 'FAILED'
              ) THEN
                RAISE EXCEPTION 'CLEARING to OPEN requires a conclusive failed attempt';
              END IF;
            ELSE
              RAISE EXCEPTION 'invalid payment obligation status transition % -> %', OLD.status, NEW.status;
            END IF;
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
    op.execute(
        """
        CREATE FUNCTION bluejet_protect_payout_attempt() RETURNS trigger AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'payout_attempts cannot be deleted';
          END IF;
          IF NEW.payment_obligation_id IS DISTINCT FROM OLD.payment_obligation_id
             OR NEW.idempotency_key IS DISTINCT FROM OLD.idempotency_key
             OR NEW.payment_hash IS DISTINCT FROM OLD.payment_hash
             OR NEW.invoice_hash IS DISTINCT FROM OLD.invoice_hash
             OR NEW.invoice_network IS DISTINCT FROM OLD.invoice_network
             OR NEW.invoice_amount_sats IS DISTINCT FROM OLD.invoice_amount_sats
             OR NEW.invoice_expires_at IS DISTINCT FROM OLD.invoice_expires_at
             OR NEW.mode IS DISTINCT FROM OLD.mode
             OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
            RAISE EXCEPTION 'payout attempt identity and invoice metadata are immutable';
          END IF;
          IF NEW.status IS DISTINCT FROM OLD.status AND NOT (
            (OLD.status = 'VALIDATED' AND NEW.status IN ('PROCESSING', 'FAILED', 'EXPIRED'))
            OR (OLD.status = 'PROCESSING' AND NEW.status IN ('AMBIGUOUS', 'SETTLED', 'FAILED'))
            OR (OLD.status = 'AMBIGUOUS' AND NEW.status IN ('SETTLED', 'FAILED'))
          ) THEN
            RAISE EXCEPTION 'invalid payout attempt status transition % -> %', OLD.status, NEW.status;
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        "CREATE TRIGGER payout_attempts_protected BEFORE UPDATE OR DELETE ON payout_attempts "
        "FOR EACH ROW EXECUTE FUNCTION bluejet_protect_payout_attempt()"
    )
    op.execute(
        """
        CREATE FUNCTION bluejet_validate_payout_attempt_composition() RETURNS trigger AS $$
        DECLARE
          obligation_status varchar(20);
        BEGIN
          SELECT status INTO obligation_status
          FROM payment_obligations WHERE id = NEW.payment_obligation_id;
          IF NOT EXISTS (
            SELECT 1 FROM ledger_transactions
            WHERE reference_id = 'payout-dispatch:' || NEW.id
          ) OR NOT EXISTS (
            SELECT 1 FROM outbox_events
            WHERE aggregate_id = NEW.id AND event_type = 'PayoutDispatchRequested'
          ) THEN
            RAISE EXCEPTION 'payout attempt requires atomic dispatch ledger and outbox';
          END IF;
          IF NEW.status IN ('CREATED', 'VALIDATED', 'PROCESSING', 'AMBIGUOUS')
             AND obligation_status <> 'CLEARING' THEN
            RAISE EXCEPTION 'active payout attempt requires CLEARING obligation';
          ELSIF NEW.status = 'SETTLED' AND obligation_status <> 'SETTLED' THEN
            RAISE EXCEPTION 'settled payout attempt requires SETTLED obligation';
          ELSIF NEW.status IN ('FAILED', 'EXPIRED') AND obligation_status <> 'OPEN' THEN
            RAISE EXCEPTION 'terminal unpaid attempt requires OPEN obligation';
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER payout_attempts_composition_valid "
        "AFTER INSERT OR UPDATE ON payout_attempts DEFERRABLE INITIALLY DEFERRED "
        "FOR EACH ROW EXECUTE FUNCTION bluejet_validate_payout_attempt_composition()"
    )
    op.execute(
        """
        CREATE FUNCTION bluejet_protect_provider_payment() RETURNS trigger AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'provider_payments cannot be deleted';
          END IF;
          IF NEW.payout_attempt_id IS DISTINCT FROM OLD.payout_attempt_id
             OR NEW.provider IS DISTINCT FROM OLD.provider
             OR NEW.payment_hash IS DISTINCT FROM OLD.payment_hash
             OR NEW.mode IS DISTINCT FROM OLD.mode
             OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
            RAISE EXCEPTION 'provider payment identity fields are immutable';
          END IF;
          IF NEW.status IS DISTINCT FROM OLD.status AND NOT (
            (OLD.status = 'PROCESSING' AND NEW.status IN ('AMBIGUOUS', 'SETTLED', 'FAILED'))
            OR (OLD.status = 'AMBIGUOUS' AND NEW.status IN ('SETTLED', 'FAILED'))
          ) THEN
            RAISE EXCEPTION 'invalid provider payment status transition % -> %', OLD.status, NEW.status;
          END IF;
          IF NEW.status IS DISTINCT FROM OLD.status AND NOT EXISTS (
            SELECT 1 FROM payout_attempts
            WHERE id = OLD.payout_attempt_id AND status = NEW.status
          ) THEN
            RAISE EXCEPTION 'provider payment status requires matching payout attempt status';
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        "CREATE TRIGGER provider_payments_protected BEFORE UPDATE OR DELETE ON provider_payments "
        "FOR EACH ROW EXECUTE FUNCTION bluejet_protect_provider_payment()"
    )
    for table in ("provider_events", "payment_receipts"):
        op.execute(
            f"CREATE TRIGGER {table}_append_only_mutation BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION bluejet_reject_append_only_mutation()"
        )
        op.execute(
            f"CREATE TRIGGER {table}_append_only_truncate BEFORE TRUNCATE ON {table} "
            "FOR EACH STATEMENT EXECUTE FUNCTION bluejet_reject_append_only_mutation()"
        )

    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON provider_payments TO bluejet_runtime"
    )
    op.execute("GRANT SELECT, INSERT ON provider_events, payment_receipts TO bluejet_runtime")


def downgrade():
    raise RuntimeError("payment clearing is forward-only; use a corrective migration")
