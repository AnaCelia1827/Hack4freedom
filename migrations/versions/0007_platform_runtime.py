"""Add persistent onboarding and leased outbox dispatch.

Revision ID: 0007_platform_runtime
"""
from alembic import op
import sqlalchemy as sa


revision = "0007_platform_runtime"
down_revision = "0006_identity_persistence"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("outbox_events", sa.Column("claimed_at", sa.DateTime(timezone=True)))
    op.add_column("outbox_events", sa.Column("claimed_by", sa.String(120)))
    op.add_column("outbox_events", sa.Column("last_error", sa.String(240)))
    op.create_index(
        "ix_outbox_events_dispatchable",
        "outbox_events",
        ["occurred_at", "event_id"],
        postgresql_where=sa.text("published_at IS NULL"),
    )
    op.create_table(
        "onboarding_drafts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="IN_PROGRESS"),
        sa.Column("data", sa.JSON, nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('IN_PROGRESS', 'COMPLETED')", name="ck_onboarding_drafts_status"),
    )
    op.execute("GRANT SELECT, INSERT, UPDATE ON onboarding_drafts TO bluejet_runtime")


def downgrade():
    raise RuntimeError("platform runtime persistence is forward-only; use a corrective migration")
