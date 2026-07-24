"""Bind onboarding to users and persist authentication provenance.

Revision ID: 0008_identity_phase2
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_identity_phase2"
down_revision = "0007_platform_runtime"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "participant_sessions",
        sa.Column("auth_mode", sa.String(12), nullable=False, server_default="REAL"),
    )
    op.create_check_constraint(
        "ck_participant_sessions_auth_mode",
        "participant_sessions",
        "auth_mode IN ('REAL', 'DEMO')",
    )
    op.add_column(
        "onboarding_drafts",
        sa.Column("user_id", sa.String(36), nullable=True),
    )
    op.create_foreign_key(
        "fk_onboarding_drafts_user_id",
        "onboarding_drafts",
        "users",
        ["user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_onboarding_drafts_user_id", "onboarding_drafts", ["user_id"])


def downgrade():
    raise RuntimeError("identity phase 2 is forward-only; use a corrective migration")
