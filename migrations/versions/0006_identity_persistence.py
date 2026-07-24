"""Persist Nostr challenges and participant sessions without bearer material.

Revision ID: 0006_identity_persistence
"""
from alembic import op
import sqlalchemy as sa


revision = "0006_identity_persistence"
down_revision = "0005_runtime_role_hardening"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("nostr_pubkey", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("nostr_pubkey", name="uq_users_nostr_pubkey"),
    )
    op.create_table(
        "auth_challenges",
        sa.Column("challenge_hash", sa.String(64), primary_key=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("length(challenge_hash) = 64", name="ck_auth_challenges_hash_length"),
    )
    op.create_index("ix_auth_challenges_expires_at", "auth_challenges", ["expires_at"])
    op.create_table(
        "participant_sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("length(token_hash) = 64", name="ck_participant_sessions_hash_length"),
    )
    op.create_index("ix_participant_sessions_user_id", "participant_sessions", ["user_id"])
    op.create_index("ix_participant_sessions_expires_at", "participant_sessions", ["expires_at"])
    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON users, auth_challenges, participant_sessions TO bluejet_runtime"
    )


def downgrade():
    raise RuntimeError("identity persistence is forward-only; use a corrective migration")
