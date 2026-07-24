"""Idempotent staging/local role seed using public Nostr keys only."""

from __future__ import annotations

import argparse
import json
import os

from sqlalchemy import text

from .auth import normalize_nostr_pubkey
from .database import DatabaseManager


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        description="Seed Bluejet test identities without accepting private key material."
    )
    command.add_argument("--participant-pubkey", required=True)
    command.add_argument("--organization-pubkey", required=True)
    command.add_argument("--admin-reviewer-pubkey", required=True)
    command.add_argument("--donor-pubkey")
    command.add_argument("--company-id", required=True)
    return command


def main() -> int:
    args = parser().parse_args()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    participant_pubkey = normalize_nostr_pubkey(args.participant_pubkey)
    organization_pubkey = normalize_nostr_pubkey(args.organization_pubkey)
    admin_reviewer_pubkey = normalize_nostr_pubkey(args.admin_reviewer_pubkey)
    donor_pubkey = normalize_nostr_pubkey(args.donor_pubkey) if args.donor_pubkey else None
    manager = DatabaseManager(database_url)

    with manager.engine.connect() as connection:
        can_insert_roles = connection.scalar(
            text("SELECT has_table_privilege(current_user, 'user_roles', 'INSERT')")
        )
    if not can_insert_roles:
        raise SystemExit(
            "the seed requires the migration-owner connection, not the runtime role"
        )

    manager.grant_role(participant_pubkey, "PARTICIPANT")
    manager.grant_role(organization_pubkey, "ORGANIZATION")
    membership = manager.add_company_membership(
        organization_pubkey,
        args.company_id,
        "OWNER",
    )
    manager.grant_role(admin_reviewer_pubkey, "ADMIN")
    manager.grant_role(admin_reviewer_pubkey, "REVIEWER")
    if donor_pubkey:
        manager.grant_role(donor_pubkey, "DONOR")

    print(
        json.dumps(
            {
                "status": "seeded",
                "participant_roles": ["PARTICIPANT"],
                "organization_roles": ["PARTICIPANT", "ORGANIZATION"],
                "admin_reviewer_roles": ["PARTICIPANT", "ADMIN", "REVIEWER"],
                "donor_roles": ["PARTICIPANT", "DONOR"] if donor_pubkey else [],
                "company_id": membership["company_id"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
