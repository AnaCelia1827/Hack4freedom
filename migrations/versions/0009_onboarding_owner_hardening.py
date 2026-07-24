"""Require one owner and at most one active onboarding draft per user.

Revision ID: 0009_onboarding_owner_hardening
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_onboarding_owner_hardening"
down_revision = "0008_identity_phase2"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM onboarding_drafts WHERE user_id IS NULL) THEN
            RAISE EXCEPTION 'legacy onboarding drafts require an explicit owner backfill';
          END IF;
        END
        $$
        """
    )
    op.alter_column("onboarding_drafts", "user_id", existing_type=sa.String(36), nullable=False)
    op.create_index(
        "uq_onboarding_drafts_active_user",
        "onboarding_drafts",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'IN_PROGRESS'"),
    )


def downgrade():
    raise RuntimeError("onboarding owner hardening is forward-only; use a corrective migration")
