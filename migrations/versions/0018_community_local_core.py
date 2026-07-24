"""Persist local community and external opportunity core after RBAC."""

from alembic import op
import sqlalchemy as sa

revision = "0018_community_local_core"
down_revision = "0017_donor_core"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "opportunity_listings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("author_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("organization_name", sa.String(160), nullable=False),
        sa.Column("external_url", sa.String(1000), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PUBLISHED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status = 'PUBLISHED'", name="ck_opportunity_listings_status"),
        sa.CheckConstraint("external_url LIKE 'https://%'", name="ck_opportunity_listings_https"),
    )
    op.create_index("ix_opportunity_listings_author_user_id", "opportunity_listings", ["author_user_id"])
    op.create_table(
        "community_post_references",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("nostr_event_id", sa.String(64), unique=True),
        sa.Column("author_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("category", sa.String(24), nullable=False), sa.Column("content", sa.Text, nullable=False),
        sa.Column("moderation_status", sa.String(20), nullable=False, server_default="VISIBLE"),
        sa.Column("relay_status", sa.String(20), nullable=False, server_default="LOCAL_ONLY"),
        sa.Column("mode", sa.String(12), nullable=False, server_default="SANDBOX"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("category IN ('learning', 'question', 'achievement')", name="ck_community_posts_category"),
        sa.CheckConstraint("moderation_status IN ('VISIBLE', 'HIDDEN')", name="ck_community_posts_moderation_status"),
        sa.CheckConstraint("relay_status IN ('LOCAL_ONLY', 'PUBLISHED')", name="ck_community_posts_relay_status"),
        sa.CheckConstraint("mode IN ('SANDBOX', 'REAL')", name="ck_community_posts_mode"),
    )
    op.create_index("ix_community_post_references_author_user_id", "community_post_references", ["author_user_id"])
    op.create_table(
        "content_reports",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("post_reference_id", sa.String(36), sa.ForeignKey("community_post_references.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reporter_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("reason", sa.Text, nullable=False), sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("post_reference_id", "reporter_user_id", name="uq_content_reports_reporter_post"), sa.CheckConstraint("status = 'OPEN'", name="ck_content_reports_status"), sa.CheckConstraint("length(trim(reason)) > 0", name="ck_content_reports_reason"),
    )
    op.create_index("ix_content_reports_post_reference_id", "content_reports", ["post_reference_id"])
    op.create_index("ix_content_reports_reporter_user_id", "content_reports", ["reporter_user_id"])
    op.create_table(
        "moderation_decisions",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("post_reference_id", sa.String(36), sa.ForeignKey("community_post_references.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("moderator_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("action", sa.String(16), nullable=False), sa.Column("reason", sa.Text, nullable=False), sa.Column("previous_status", sa.String(20), nullable=False), sa.Column("new_status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("action IN ('HIDE', 'RESTORE')", name="ck_moderation_decisions_action"), sa.CheckConstraint("length(trim(reason)) > 0", name="ck_moderation_decisions_reason"),
    )
    op.create_index("ix_moderation_decisions_post_reference_id", "moderation_decisions", ["post_reference_id"])
    op.create_index("ix_moderation_decisions_moderator_user_id", "moderation_decisions", ["moderator_user_id"])
    op.execute("GRANT SELECT, INSERT ON opportunity_listings, content_reports, moderation_decisions TO bluejet_runtime")
    op.execute("GRANT SELECT, INSERT, UPDATE ON community_post_references TO bluejet_runtime")
    for table in ("opportunity_listings", "content_reports", "moderation_decisions"):
        op.execute(f"CREATE TRIGGER {table}_append_only_mutation BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION bluejet_reject_append_only_mutation()")
        op.execute(f"CREATE TRIGGER {table}_append_only_truncate BEFORE TRUNCATE ON {table} FOR EACH STATEMENT EXECUTE FUNCTION bluejet_reject_append_only_mutation()")
    op.execute("""
        CREATE FUNCTION bluejet_protect_community_post() RETURNS trigger AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'community_post_references cannot be deleted'; END IF;
          IF NEW.author_user_id IS DISTINCT FROM OLD.author_user_id OR NEW.category IS DISTINCT FROM OLD.category OR NEW.content IS DISTINCT FROM OLD.content OR NEW.mode IS DISTINCT FROM OLD.mode OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
            RAISE EXCEPTION 'community post authorship and content are immutable';
          END IF;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER community_post_references_protected BEFORE UPDATE OR DELETE ON community_post_references FOR EACH ROW EXECUTE FUNCTION bluejet_protect_community_post()")


def downgrade():
    raise RuntimeError("community local core is forward-only; use a corrective migration")
