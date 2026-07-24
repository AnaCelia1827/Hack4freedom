"""Persist the local SANDBOX donor accounting core.

Revision ID: 0017_donor_core
"""

from alembic import op
import sqlalchemy as sa


revision = "0017_donor_core"
down_revision = "0016_payment_clearing"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_user_roles_role", "user_roles", type_="check")
    op.create_check_constraint(
        "ck_user_roles_role",
        "user_roles",
        "role IN ('PARTICIPANT', 'ORGANIZATION', 'DONOR', 'REVIEWER', 'ADMIN')",
    )

    op.create_table(
        "donor_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column("display_name", sa.String(160)),
        sa.Column("terms_version", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_donor_profiles_user_id", "donor_profiles", ["user_id"])

    op.create_table(
        "contributions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "donor_profile_id",
            sa.String(36),
            sa.ForeignKey("donor_profiles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(255), nullable=False, unique=True),
        sa.Column("input_amount_sats", sa.BigInteger(), nullable=False),
        sa.Column("input_currency", sa.String(12), nullable=False),
        sa.Column("terms_version", sa.String(40), nullable=False),
        sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("mode", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("input_amount_sats > 0", name="ck_contributions_positive_amount"),
        sa.CheckConstraint("input_currency = 'SAT'", name="ck_contributions_currency"),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'QUOTED', 'PENDING_PAYMENT', 'CONFIRMED', 'ALLOCATED', 'FAILED', 'CANCELLED')",
            name="ck_contributions_status",
        ),
        sa.CheckConstraint(
            "mode IN ('MOCK', 'SANDBOX', 'REAL')", name="ck_contributions_mode"
        ),
    )
    op.create_index(
        "ix_contributions_donor_profile_id", "contributions", ["donor_profile_id"]
    )

    op.create_table(
        "contribution_allocations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "contribution_id",
            sa.String(36),
            sa.ForeignKey("contributions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("allocation_type", sa.String(24), nullable=False),
        sa.Column("amount_sats", sa.BigInteger(), nullable=False),
        sa.Column("percentage_bps", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "contribution_id",
            "allocation_type",
            name="uq_contribution_allocations_type",
        ),
        sa.CheckConstraint(
            "allocation_type IN ('IMPACT_FUND', 'LIQUIDITY_CAPITAL')",
            name="ck_contribution_allocations_type",
        ),
        sa.CheckConstraint("amount_sats > 0", name="ck_contribution_allocations_amount"),
        sa.CheckConstraint(
            "percentage_bps > 0 AND percentage_bps <= 10000",
            name="ck_contribution_allocations_percentage",
        ),
        sa.CheckConstraint("status = 'ALLOCATED'", name="ck_contribution_allocations_status"),
    )
    op.create_index(
        "ix_contribution_allocations_contribution_id",
        "contribution_allocations",
        ["contribution_id"],
    )

    op.create_table(
        "contribution_receipts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "contribution_id",
            sa.String(36),
            sa.ForeignKey("contributions.id", ondelete="RESTRICT"),
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
        sa.Column("total_sats", sa.BigInteger(), nullable=False),
        sa.Column("impact_sats", sa.BigInteger(), nullable=False),
        sa.Column("liquidity_sats", sa.BigInteger(), nullable=False),
        sa.Column("mode", sa.String(10), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("total_sats > 0", name="ck_contribution_receipts_total"),
        sa.CheckConstraint(
            "impact_sats >= 0 AND liquidity_sats >= 0 AND impact_sats + liquidity_sats = total_sats",
            name="ck_contribution_receipts_composition",
        ),
        sa.CheckConstraint(
            "mode IN ('MOCK', 'SANDBOX', 'REAL')",
            name="ck_contribution_receipts_mode",
        ),
    )
    op.create_index(
        "ix_contribution_receipts_contribution_id",
        "contribution_receipts",
        ["contribution_id"],
    )

    op.execute(
        """
        CREATE FUNCTION bluejet_validate_contribution_composition() RETURNS trigger AS $$
        DECLARE
          target_id varchar(36);
          expected_sats bigint;
          allocated_sats bigint;
          allocated_bps integer;
          contribution_status varchar(24);
        BEGIN
          IF TG_TABLE_NAME = 'contributions' THEN
            target_id := NEW.id;
          ELSE
            target_id := NEW.contribution_id;
          END IF;
          SELECT input_amount_sats, status INTO expected_sats, contribution_status
          FROM contributions WHERE id = target_id;
          IF contribution_status IN ('CONFIRMED', 'ALLOCATED') THEN
            SELECT COALESCE(sum(amount_sats), 0), COALESCE(sum(percentage_bps), 0)
            INTO allocated_sats, allocated_bps
            FROM contribution_allocations WHERE contribution_id = target_id;
            IF allocated_sats <> expected_sats OR allocated_bps <> 10000 THEN
              RAISE EXCEPTION 'contribution allocation must total amount and 10000 basis points';
            END IF;
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER contributions_composition_valid "
        "AFTER INSERT OR UPDATE ON contributions DEFERRABLE INITIALLY DEFERRED "
        "FOR EACH ROW EXECUTE FUNCTION bluejet_validate_contribution_composition()"
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER contribution_allocations_composition_valid "
        "AFTER INSERT OR UPDATE ON contribution_allocations DEFERRABLE INITIALLY DEFERRED "
        "FOR EACH ROW EXECUTE FUNCTION bluejet_validate_contribution_composition()"
    )

    for table in ("contributions", "contribution_allocations", "contribution_receipts"):
        op.execute(
            f"CREATE TRIGGER {table}_append_only_mutation BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION bluejet_reject_append_only_mutation()"
        )
        op.execute(
            f"CREATE TRIGGER {table}_append_only_truncate BEFORE TRUNCATE ON {table} "
            "FOR EACH STATEMENT EXECUTE FUNCTION bluejet_reject_append_only_mutation()"
        )

    op.execute("GRANT SELECT, INSERT, UPDATE ON donor_profiles TO bluejet_runtime")
    op.execute(
        "GRANT SELECT, INSERT ON contributions, contribution_allocations, contribution_receipts TO bluejet_runtime"
    )


def downgrade():
    raise RuntimeError("donor accounting is forward-only; use a corrective migration")
