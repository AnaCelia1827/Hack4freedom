"""Persist backend-owned Nostr roles and organization memberships.

Revision ID: 0015_identity_rbac
"""

from alembic import op
import sqlalchemy as sa


revision = "0015_identity_rbac"
down_revision = "0013_review_and_obligation"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM users
            WHERE nostr_pubkey !~ '^[0-9a-f]{64}$'
          ) THEN
            RAISE EXCEPTION 'users contains a non-canonical Nostr public key';
          END IF;
        END;
        $$
        """
    )
    op.create_check_constraint(
        "ck_users_nostr_pubkey_hex",
        "users",
        "nostr_pubkey ~ '^[0-9a-f]{64}$'",
    )

    op.create_table(
        "user_roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column(
            "granted_by_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
        ),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "role IN ('PARTICIPANT', 'ORGANIZATION', 'REVIEWER', 'ADMIN')",
            name="ck_user_roles_role",

        ),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index(
        "ix_user_roles_granted_by_user_id", "user_roles", ["granted_by_user_id"]
    )
    op.create_index(
        "uq_user_roles_active_user_role",
        "user_roles",
        ["user_id", "role"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    op.create_index(
        "ix_user_roles_active_role",
        "user_roles",
        ["role"],
        postgresql_where=sa.text("revoked_at IS NULL"),
    )

    op.create_table(
        "company_memberships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "company_id",
            sa.String(36),
            sa.ForeignKey("companies.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("membership_role", sa.String(20), nullable=False),
        sa.Column(
            "granted_by_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "membership_role IN ('OWNER', 'MEMBER')",
            name="ck_company_memberships_role",
        ),
    )
    op.create_index(
        "ix_company_memberships_company_id", "company_memberships", ["company_id"]
    )
    op.create_index(
        "ix_company_memberships_user_id", "company_memberships", ["user_id"]
    )
    op.create_index(
        "ix_company_memberships_granted_by_user_id",
        "company_memberships",
        ["granted_by_user_id"],
    )
    op.create_index(
        "uq_company_memberships_active_company_user",
        "company_memberships",
        ["company_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )

    op.execute(
        """
        INSERT INTO user_roles (id, user_id, role, granted_at)
        SELECT
          substr(md5(id || '-PARTICIPANT'), 1, 8) || '-' ||
          substr(md5(id || '-PARTICIPANT'), 9, 4) || '-' ||
          substr(md5(id || '-PARTICIPANT'), 13, 4) || '-' ||
          substr(md5(id || '-PARTICIPANT'), 17, 4) || '-' ||
          substr(md5(id || '-PARTICIPANT'), 21, 12),
          id,
          'PARTICIPANT',
          CURRENT_TIMESTAMP
        FROM users
        ON CONFLICT (user_id, role) WHERE revoked_at IS NULL DO NOTHING
        """
    )
    op.execute(
        """
        CREATE FUNCTION bluejet_ensure_participant_role(target_user_id varchar)
        RETURNS void AS $$
        BEGIN
          INSERT INTO user_roles (id, user_id, role, granted_at)
          VALUES (
            substr(md5(target_user_id || '-PARTICIPANT'), 1, 8) || '-' ||
            substr(md5(target_user_id || '-PARTICIPANT'), 9, 4) || '-' ||
            substr(md5(target_user_id || '-PARTICIPANT'), 13, 4) || '-' ||
            substr(md5(target_user_id || '-PARTICIPANT'), 17, 4) || '-' ||
            substr(md5(target_user_id || '-PARTICIPANT'), 21, 12),
            target_user_id,
            'PARTICIPANT',
            CURRENT_TIMESTAMP
          )
          ON CONFLICT (user_id, role) WHERE revoked_at IS NULL DO NOTHING;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
        """
    )
    op.execute("REVOKE ALL ON FUNCTION bluejet_ensure_participant_role(varchar) FROM PUBLIC")
    op.execute(
        "GRANT EXECUTE ON FUNCTION bluejet_ensure_participant_role(varchar) TO bluejet_runtime"
    )
    op.execute("GRANT SELECT ON user_roles, company_memberships TO bluejet_runtime")

    op.execute(
        """
        CREATE FUNCTION bluejet_protect_user_role() RETURNS trigger AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'role grants cannot be deleted';
          END IF;
          IF NEW.id IS DISTINCT FROM OLD.id
             OR NEW.user_id IS DISTINCT FROM OLD.user_id
             OR NEW.granted_by_user_id IS DISTINCT FROM OLD.granted_by_user_id
             OR NEW.role IS DISTINCT FROM OLD.role
             OR NEW.granted_at IS DISTINCT FROM OLD.granted_at
          THEN
            RAISE EXCEPTION 'role grant fields are immutable';
          END IF;
          IF OLD.revoked_at IS NOT NULL OR NEW.revoked_at IS NULL THEN
            RAISE EXCEPTION 'only one-way revocation is allowed';
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE FUNCTION bluejet_protect_company_membership() RETURNS trigger AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'company memberships cannot be deleted';
          END IF;
          IF NEW.id IS DISTINCT FROM OLD.id
             OR NEW.company_id IS DISTINCT FROM OLD.company_id
             OR NEW.user_id IS DISTINCT FROM OLD.user_id
             OR NEW.membership_role IS DISTINCT FROM OLD.membership_role
             OR NEW.granted_by_user_id IS DISTINCT FROM OLD.granted_by_user_id
             OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
            RAISE EXCEPTION 'company membership fields are immutable';
          END IF;
          IF OLD.revoked_at IS NOT NULL OR NEW.revoked_at IS NULL THEN
            RAISE EXCEPTION 'only one-way revocation is allowed';
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        "CREATE TRIGGER user_roles_protected BEFORE UPDATE OR DELETE ON user_roles "
        "FOR EACH ROW EXECUTE FUNCTION bluejet_protect_user_role()"
    )
    op.execute(
        "CREATE TRIGGER company_memberships_protected BEFORE UPDATE OR DELETE ON company_memberships "
        "FOR EACH ROW EXECUTE FUNCTION bluejet_protect_company_membership()"
    )
    for table_name in ("user_roles", "company_memberships"):
        op.execute(
            f"CREATE TRIGGER {table_name}_no_truncate BEFORE TRUNCATE ON {table_name} "
            "FOR EACH STATEMENT EXECUTE FUNCTION bluejet_reject_append_only_mutation()"
        )


def downgrade():
    raise RuntimeError("identity RBAC is forward-only; use a corrective migration")
