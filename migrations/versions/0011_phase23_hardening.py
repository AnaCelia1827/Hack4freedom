"""Persist badge opt-in and local publication request state.

Revision ID: 0011_phase23_hardening
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_phase23_hardening"
down_revision = "0010_learning_persistence"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "auth_challenges",
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_check_constraint(
        "ck_auth_challenges_attempt_count",
        "auth_challenges",
        "attempt_count >= 0",
    )
    op.create_table(
        "badge_definitions",
        sa.Column("id", sa.String(120), primary_key=True),
        sa.Column("identifier", sa.String(120), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("mode", sa.String(12), nullable=False, server_default="SANDBOX"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("identifier", name="uq_badge_definitions_identifier"),
        sa.CheckConstraint(
            "mode IN ('SANDBOX', 'REAL')", name="ck_badge_definitions_mode"
        ),
    )
    op.create_table(
        "badge_consents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "skill_evidence_id",
            sa.String(36),
            sa.ForeignKey("skill_evidence.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "badge_definition_id",
            sa.String(120),
            sa.ForeignKey("badge_definitions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "user_id",
            "skill_evidence_id",
            "badge_definition_id",
            name="uq_badge_consents_user_evidence_definition",
        ),
    )
    op.create_index("ix_badge_consents_user_id", "badge_consents", ["user_id"])
    op.create_table(
        "badge_publications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "consent_id",
            sa.String(36),
            sa.ForeignKey("badge_consents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "status", sa.String(24), nullable=False, server_default="PUBLISH_PENDING"
        ),
        sa.Column("mode", sa.String(12), nullable=False, server_default="SANDBOX"),
        sa.Column("nostr_event_id", sa.String(64), nullable=True),
        sa.Column("relays", sa.JSON, nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column(
            "acknowledged_relays",
            sa.JSON,
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("consent_id", name="uq_badge_publications_consent"),
        sa.CheckConstraint(
            "status IN ('PUBLISH_PENDING', 'PUBLISHED', 'FAILED')",
            name="ck_badge_publications_status",
        ),
        sa.CheckConstraint(
            "mode IN ('SANDBOX', 'REAL')", name="ck_badge_publications_mode"
        ),
    )
    op.execute(
        "GRANT SELECT, INSERT ON badge_definitions, badge_consents, badge_publications TO bluejet_runtime"
    )
    for table_name in ("badge_definitions", "badge_consents"):
        op.execute(
            f"""
            CREATE TRIGGER {table_name}_append_only_mutation
            BEFORE UPDATE OR DELETE ON {table_name}
            FOR EACH ROW EXECUTE FUNCTION bluejet_reject_append_only_mutation()
            """
        )
        op.execute(
            f"""
            CREATE TRIGGER {table_name}_append_only_truncate
            BEFORE TRUNCATE ON {table_name}
            FOR EACH STATEMENT EXECUTE FUNCTION bluejet_reject_append_only_mutation()
            """
        )


def downgrade():
    raise RuntimeError("phase 2/3 hardening is forward-only; use a corrective migration")
