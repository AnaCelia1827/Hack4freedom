"""Complete local community opportunities without enabling external relays.

Revision ID: 0019_community_completion
"""

from alembic import op
import sqlalchemy as sa


revision = "0019_community_completion"
down_revision = "0018_community_local_core"
branch_labels = None
depends_on = None


OPPORTUNITY_TYPES = (
    "HACKATHON",
    "FREE_COURSE",
    "EVENT",
    "TALK",
    "MEETUP",
    "MENTORSHIP",
    "EDUCATIONAL_PROGRAM",
    "OTHER",
)
REPORT_CATEGORIES = (
    "SPAM",
    "FRAUD",
    "PERSONAL_DATA",
    "HARASSMENT",
    "MISLEADING_CONTENT",
    "MALICIOUS_LINK",
    "OUT_OF_SCOPE",
    "OTHER",
)


def upgrade():
    op.add_column("community_post_references", sa.Column("idempotency_key", sa.String(255)))
    op.create_index(
        "uq_community_posts_author_idempotency",
        "community_post_references",
        ["author_user_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )

    op.drop_constraint("ck_opportunity_listings_https", "opportunity_listings", type_="check")
    op.create_check_constraint(
        "ck_opportunity_listings_http_scheme",
        "opportunity_listings",
        "external_url LIKE 'http://%' OR external_url LIKE 'https://%'",
    )
    op.add_column("opportunity_listings", sa.Column("format", sa.String(16), nullable=False, server_default="ONLINE"))
    op.add_column("opportunity_listings", sa.Column("location", sa.String(240)))
    op.add_column("opportunity_listings", sa.Column("starts_at", sa.DateTime(timezone=True)))
    op.add_column("opportunity_listings", sa.Column("application_deadline", sa.DateTime(timezone=True)))
    op.add_column("opportunity_listings", sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")))
    op.add_column("opportunity_listings", sa.Column("requirements", sa.Text(), nullable=False, server_default=""))
    op.add_column("opportunity_listings", sa.Column("non_remunerated_ack", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("opportunity_listings", sa.Column("moderation_status", sa.String(20), nullable=False, server_default="VISIBLE"))
    op.add_column("opportunity_listings", sa.Column("idempotency_key", sa.String(255)))
    op.execute("UPDATE opportunity_listings SET starts_at = created_at WHERE starts_at IS NULL")
    op.alter_column(
        "opportunity_listings", "starts_at", existing_type=sa.DateTime(timezone=True), nullable=False
    )
    op.execute(
        "UPDATE opportunity_listings SET category = 'OTHER' "
        "WHERE category NOT IN (" + ", ".join(f"'{value}'" for value in OPPORTUNITY_TYPES) + ")"
    )
    op.create_check_constraint(
        "ck_opportunity_listings_category",
        "opportunity_listings",
        "category IN (" + ", ".join(f"'{value}'" for value in OPPORTUNITY_TYPES) + ")",
    )
    op.create_check_constraint(
        "ck_opportunity_listings_format",
        "opportunity_listings",
        "format IN ('ONLINE', 'ONSITE', 'HYBRID')",
    )
    op.create_check_constraint(
        "ck_opportunity_listings_location",
        "opportunity_listings",
        "format = 'ONLINE' OR length(trim(location)) > 0",
    )
    op.create_check_constraint(
        "ck_opportunity_listings_starts_at_required",
        "opportunity_listings",
        "starts_at IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_opportunity_listings_dates",
        "opportunity_listings",
        "application_deadline IS NULL OR starts_at IS NULL OR application_deadline <= starts_at",
    )
    op.create_check_constraint(
        "ck_opportunity_listings_non_remunerated",
        "opportunity_listings",
        "non_remunerated_ack IS TRUE",
    )
    op.create_check_constraint(
        "ck_opportunity_listings_moderation_status",
        "opportunity_listings",
        "moderation_status IN ('VISIBLE', 'HIDDEN')",
    )
    op.create_index(
        "uq_opportunity_listings_author_idempotency",
        "opportunity_listings",
        ["author_user_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )
    op.create_index(
        "ix_opportunity_listings_visible_created",
        "opportunity_listings",
        ["moderation_status", "created_at"],
    )
    op.execute("DROP TRIGGER opportunity_listings_append_only_mutation ON opportunity_listings")
    op.execute(
        """
        CREATE FUNCTION bluejet_protect_opportunity_listing() RETURNS trigger AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'opportunity listings cannot be deleted'; END IF;
          IF NEW.author_user_id IS DISTINCT FROM OLD.author_user_id
             OR NEW.title IS DISTINCT FROM OLD.title
             OR NEW.category IS DISTINCT FROM OLD.category
             OR NEW.description IS DISTINCT FROM OLD.description
             OR NEW.organization_name IS DISTINCT FROM OLD.organization_name
             OR NEW.external_url IS DISTINCT FROM OLD.external_url
             OR NEW.format IS DISTINCT FROM OLD.format
             OR NEW.location IS DISTINCT FROM OLD.location
             OR NEW.starts_at IS DISTINCT FROM OLD.starts_at
             OR NEW.application_deadline IS DISTINCT FROM OLD.application_deadline
             OR NEW.tags::jsonb IS DISTINCT FROM OLD.tags::jsonb
             OR NEW.requirements IS DISTINCT FROM OLD.requirements
             OR NEW.non_remunerated_ack IS DISTINCT FROM OLD.non_remunerated_ack
             OR NEW.idempotency_key IS DISTINCT FROM OLD.idempotency_key
             OR NEW.status IS DISTINCT FROM OLD.status
             OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
            RAISE EXCEPTION 'opportunity listing authorship and content are immutable';
          END IF;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        "CREATE TRIGGER opportunity_listings_protected BEFORE UPDATE OR DELETE "
        "ON opportunity_listings FOR EACH ROW EXECUTE FUNCTION bluejet_protect_opportunity_listing()"
    )
    op.execute("GRANT UPDATE ON opportunity_listings TO bluejet_runtime")

    op.add_column("content_reports", sa.Column("opportunity_listing_id", sa.String(36)))
    op.create_foreign_key(
        "fk_content_reports_opportunity_listing_id",
        "content_reports",
        "opportunity_listings",
        ["opportunity_listing_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.add_column("content_reports", sa.Column("category", sa.String(32), nullable=False, server_default="OTHER"))
    op.add_column("content_reports", sa.Column("details", sa.Text(), nullable=False, server_default=""))
    op.execute("UPDATE content_reports SET details = reason WHERE category = 'OTHER' AND details = ''")
    op.alter_column("content_reports", "post_reference_id", existing_type=sa.String(36), nullable=True)
    op.create_check_constraint(
        "ck_content_reports_target",
        "content_reports",
        "(post_reference_id IS NOT NULL)::integer + (opportunity_listing_id IS NOT NULL)::integer = 1",
    )
    op.create_check_constraint(
        "ck_content_reports_category",
        "content_reports",
        "category IN (" + ", ".join(f"'{value}'" for value in REPORT_CATEGORIES) + ")",
    )
    op.create_check_constraint(
        "ck_content_reports_other_details",
        "content_reports",
        "category <> 'OTHER' OR length(trim(details)) > 0",
    )
    op.create_index("ix_content_reports_opportunity_listing_id", "content_reports", ["opportunity_listing_id"])
    op.create_index(
        "uq_content_reports_reporter_opportunity",
        "content_reports",
        ["opportunity_listing_id", "reporter_user_id"],
        unique=True,
        postgresql_where=sa.text("opportunity_listing_id IS NOT NULL"),
    )

    op.add_column("moderation_decisions", sa.Column("opportunity_listing_id", sa.String(36)))
    op.create_foreign_key(
        "fk_moderation_decisions_opportunity_listing_id",
        "moderation_decisions",
        "opportunity_listings",
        ["opportunity_listing_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.alter_column("moderation_decisions", "post_reference_id", existing_type=sa.String(36), nullable=True)
    op.drop_constraint("ck_moderation_decisions_action", "moderation_decisions", type_="check")
    op.create_check_constraint(
        "ck_moderation_decisions_action",
        "moderation_decisions",
        "action IN ('HIDE', 'RESTORE', 'KEEP')",
    )
    op.create_check_constraint(
        "ck_moderation_decisions_target",
        "moderation_decisions",
        "(post_reference_id IS NOT NULL)::integer + (opportunity_listing_id IS NOT NULL)::integer = 1",
    )
    op.create_index(
        "ix_moderation_decisions_opportunity_listing_id",
        "moderation_decisions",
        ["opportunity_listing_id"],
    )


def downgrade():
    raise RuntimeError("community moderation history is forward-only; use a corrective migration")
