"""Integration tests that must run against a real PostgreSQL database."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import hashlib
import os
from time import monotonic

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from bluejet_api import create_app
from bluejet_api.auth import NostrAuth
from bluejet_api.config import Config
from bluejet_api.database import (
    ActivePayoutAttempt,
    Assignment,
    AssignmentReservation,
    AssignmentUnavailable,
    AuthChallenge,
    AuditEvent,
    BadgeConsent,
    BadgeDefinition,
    BadgePublication,
    Company,
    CompanyMembership,
    DatabaseManager,
    Contribution,
    ContributionAllocation,
    ContributionReceipt,
    DonorProfile,
    IdempotencyConflict,
    IdempotencyLockTimeout,
    InboxEvent,
    LedgerEntry,
    LedgerTransaction,
    LearningActivitySubmission,
    LearningEnrollment,
    LearningNote,
    ObligationNotOpen,
    OnboardingDraft,
    OutboxEvent,
    PaidTask,
    PaymentObligation,
    PaymentReceipt,
    ParticipantSession,
    PayoutAttempt,
    ProviderEvent,
    ProviderPayment,
    QuizAttempt,
    Review,
    ReviewConflict,
    SkillEvidence,
    StoredObject,
    Submission,
    SubmissionDraft,
    TaskFundingLine,
    TaskFundingReservation,
    UnbalancedLedgerTransaction,
    User,
    UserRole,
)
from bluejet_api.outbox import OutboxWorker
from bluejet_api.workers import AssignmentExpiryWorker
from nostr_test_utils import pubkey_for_private_key, signed_auth_payload


DATABASE_URL = os.getenv("TEST_DATABASE_URL")
MIGRATION_DATABASE_URL = os.getenv("TEST_MIGRATION_DATABASE_URL", DATABASE_URL)
pytestmark = pytest.mark.skipif(
    not DATABASE_URL or not MIGRATION_DATABASE_URL,
    reason="TEST_DATABASE_URL and TEST_MIGRATION_DATABASE_URL require real PostgreSQL",
)


@pytest.fixture()
def database():
    manager = DatabaseManager(DATABASE_URL)
    migration_engine = create_engine(MIGRATION_DATABASE_URL)
    with migration_engine.begin() as connection:
        connection.execute(text("SET LOCAL session_replication_role = replica"))
        connection.execute(
            text(
                "TRUNCATE contribution_receipts, contribution_allocations, contributions, donor_profiles, "
                "moderation_decisions, content_reports, community_post_references, opportunity_listings, "
                "payment_receipts, provider_events, provider_payments, company_memberships, user_roles, reviews, submissions, submission_drafts, stored_objects, assignment_reservations, assignments, "
                "task_funding_lines, task_funding_reservations, paid_tasks, companies, "
                "participant_sessions, users, auth_challenges, ledger_entries, "
                "ledger_transactions, payout_attempts, payment_obligations, outbox_events, "
                "inbox_events, onboarding_drafts, audit_events, learning_activity_submissions, "
                "learning_notes, badge_publications, badge_consents, badge_definitions, "
                "skill_evidence, quiz_attempts, learning_enrollments RESTART IDENTITY CASCADE"
            )
        )
    migration_engine.dispose()
    return manager


def test_runtime_role_has_minimum_privileges(database):
    with database.engine.connect() as connection:
        current_user = connection.execute(text("SELECT current_user")).scalar_one()
        assert connection.execute(
            text("SELECT pg_has_role(current_user, 'bluejet_runtime', 'member')")
        ).scalar_one()
        assert connection.execute(
            text("SELECT has_table_privilege(current_user, 'ledger_entries', 'SELECT,INSERT')")
        ).scalar_one()
        assert not connection.execute(
            text("SELECT has_table_privilege(current_user, 'ledger_entries', 'DELETE,TRUNCATE')")
        ).scalar_one()
        assert not connection.execute(
            text("SELECT has_schema_privilege(current_user, 'public', 'CREATE')")
        ).scalar_one()
        assert current_user != connection.execute(
            text(
                "SELECT tableowner FROM pg_tables "
                "WHERE schemaname='public' AND tablename='ledger_entries'"
            )
        ).scalar_one()
        for table_name in ("users", "auth_challenges", "participant_sessions", "onboarding_drafts"):
            assert connection.execute(
                text("SELECT has_table_privilege(current_user, :table_name, 'SELECT,INSERT,UPDATE')"),
                {"table_name": table_name},
            ).scalar_one()

        for table_name in ("user_roles", "company_memberships"):
            assert connection.execute(
                text("SELECT has_table_privilege(current_user, :table_name, 'SELECT')"),
                {"table_name": table_name},
            ).scalar_one()
            assert not connection.execute(
                text(
                    "SELECT has_table_privilege(current_user, :table_name, "
                    "'INSERT,UPDATE,DELETE,TRUNCATE')"
                ),
                {"table_name": table_name},
            ).scalar_one()

        for table_name in ("learning_enrollments", "learning_notes"):
            assert connection.execute(
                text("SELECT has_table_privilege(current_user, :table_name, 'SELECT,INSERT,UPDATE')"),
                {"table_name": table_name},
            ).scalar_one()
            assert not connection.execute(
                text("SELECT has_table_privilege(current_user, :table_name, 'DELETE,TRUNCATE')"),
                {"table_name": table_name},
            ).scalar_one()
        for table_name in ("quiz_attempts", "skill_evidence", "learning_activity_submissions"):
            assert connection.execute(
                text("SELECT has_table_privilege(current_user, :table_name, 'SELECT,INSERT')"),
                {"table_name": table_name},
            ).scalar_one()
            assert not connection.execute(
                text("SELECT has_table_privilege(current_user, :table_name, 'UPDATE,DELETE,TRUNCATE')"),
                {"table_name": table_name},
            ).scalar_one()
        assert connection.execute(
            text("SELECT has_table_privilege(current_user, 'reviews', 'SELECT,INSERT')")
        ).scalar_one()
        assert not connection.execute(
            text("SELECT has_table_privilege(current_user, 'reviews', 'UPDATE,DELETE,TRUNCATE')")
        ).scalar_one()
        for table_name in ("badge_definitions", "badge_consents", "badge_publications"):
            assert connection.execute(
                text("SELECT has_table_privilege(current_user, :table_name, 'SELECT,INSERT')"),
                {"table_name": table_name},
            ).scalar_one()
            assert not connection.execute(
                text("SELECT has_table_privilege(current_user, :table_name, 'UPDATE,DELETE,TRUNCATE')"),
                {"table_name": table_name},
            ).scalar_one()
        for table_name in ("task_funding_reservations", "task_funding_lines", "submissions"):
            assert connection.execute(
                text("SELECT has_table_privilege(current_user, :table_name, 'SELECT,INSERT')"),
                {"table_name": table_name},
            ).scalar_one()
            assert not connection.execute(
                text("SELECT has_table_privilege(current_user, :table_name, 'UPDATE,DELETE,TRUNCATE')"),
                {"table_name": table_name},
            ).scalar_one()
        for table_name in ("paid_tasks", "assignments", "assignment_reservations", "stored_objects", "submission_drafts"):
            assert connection.execute(
                text("SELECT has_table_privilege(current_user, :table_name, 'SELECT,INSERT,UPDATE')"),
                {"table_name": table_name},
            ).scalar_one()
            assert not connection.execute(
                text("SELECT has_table_privilege(current_user, :table_name, 'DELETE,TRUNCATE')"),
                {"table_name": table_name},
            ).scalar_one()
        assert connection.execute(
            text("SELECT has_table_privilege(current_user, 'provider_payments', 'SELECT,INSERT,UPDATE')")
        ).scalar_one()
        assert not connection.execute(
            text("SELECT has_table_privilege(current_user, 'provider_payments', 'DELETE,TRUNCATE')")
        ).scalar_one()
        for table_name in (
            "provider_events",
            "payment_receipts",
            "contributions",
            "contribution_allocations",
            "contribution_receipts",
        ):
            assert connection.execute(
                text("SELECT has_table_privilege(current_user, :table_name, 'SELECT,INSERT')"),
                {"table_name": table_name},
            ).scalar_one()
            assert not connection.execute(
                text(
                    "SELECT has_table_privilege(current_user, :table_name, "
                    "'UPDATE,DELETE,TRUNCATE')"
                ),
                {"table_name": table_name},
            ).scalar_one()


def _eligible_participant(database, pubkey):
    NostrAuth(database).authenticate_demo(pubkey)
    database.record_quiz_attempt(
        pubkey,
        "bluejet-basics",
        "1",
        "bluejet-basics-quiz",
        "1",
        100,
        hashlib.sha256(pubkey.encode()).hexdigest(),
    )


def _funded_published_task(database):
    company = database.create_company("Acme", "Contratante")
    task = database.create_paid_task(
        company["id"], "Tarefa paga", "Entregue uma evidência", 1000, "bluejet-basics-quiz"
    )
    funding = database.reserve_task_funding(
        task["id"],
        1000,
        [
            {"account": "COMPANY_FUNDS", "amount_sats": 600},
            {"account": "MATCHING_POOL", "amount_sats": 400},
        ],
    )
    return database.publish_paid_task(task["id"]), funding


def _submitted_assignment(database, participant_pubkey="a" * 64):
    task, funding = _funded_published_task(database)
    _eligible_participant(database, participant_pubkey)
    assignment = database.reserve_assignment(task["id"], participant_pubkey)
    submission = database.create_submission(
        assignment["id"], participant_pubkey, "Entrega privada"
    )
    return task, funding, assignment, submission


def test_paid_task_survives_restart_and_funding_is_balanced(database):
    task, funding = _funded_published_task(database)
    restarted = DatabaseManager(DATABASE_URL)
    persisted = restarted.get_paid_task(task["id"])
    assert persisted["status"] == "PUBLISHED"
    assert persisted["funded_sats"] == 1000
    with restarted.sessions() as session:
        entries = list(
            session.scalars(
                select(LedgerEntry).where(
                    LedgerEntry.transaction_id == funding["ledger_transaction_id"]
                )
            )
        )
        assert sum(item.amount_sats for item in entries if item.direction == "DEBIT") == 1000
        assert sum(item.amount_sats for item in entries if item.direction == "CREDIT") == 1000
        assert {item.account for item in entries} == {
            "COMPANY_FUNDS",
            "MATCHING_POOL",
            "TASK_RESERVED",
        }


def test_two_concurrent_participants_create_only_one_active_assignment(database):
    task, _ = _funded_published_task(database)
    pubkeys = ("1" * 64, "2" * 64)
    for pubkey in pubkeys:
        _eligible_participant(database, pubkey)

    def reserve(pubkey):
        try:
            return DatabaseManager(DATABASE_URL).reserve_assignment(task["id"], pubkey)
        except AssignmentUnavailable:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve, pubkeys))
    assert sum(result is not None for result in results) == 1
    with database.sessions() as session:
        assert session.scalar(
            select(func.count()).select_from(AssignmentReservation).where(
                AssignmentReservation.task_id == task["id"],
                AssignmentReservation.status == "ACTIVE",
            )
        ) == 1


def test_expiration_releases_only_slot_and_preserves_task_funding(database):
    task, funding = _funded_published_task(database)
    first_pubkey, second_pubkey = "3" * 64, "4" * 64
    _eligible_participant(database, first_pubkey)
    _eligible_participant(database, second_pubkey)
    first = database.reserve_assignment(task["id"], first_pubkey)
    with database.sessions.begin() as session:
        reservation = session.scalar(
            select(AssignmentReservation).where(
                AssignmentReservation.assignment_id == first["id"]
            )
        )
        reservation.reserved_until = datetime.now(timezone.utc) - timedelta(seconds=1)
    worker = AssignmentExpiryWorker(database)
    assert worker.run_once()["expired"] == 1
    assert worker.run_once()["expired"] == 0
    second = database.reserve_assignment(task["id"], second_pubkey)
    assert second["status"] == "RESERVED"
    with database.sessions() as session:
        persisted_funding = session.scalar(
            select(TaskFundingReservation).where(
                TaskFundingReservation.task_id == task["id"]
            )
        )
        assert persisted_funding.id == funding["id"]
        assert persisted_funding.status == "RESERVED"
        assert persisted_funding.ledger_transaction_id == funding["ledger_transaction_id"]
        assert session.get(Assignment, first["id"]).status == "EXPIRED"


def test_submission_is_private_versioned_hashed_and_requires_clean_owned_object(database):
    task, _ = _funded_published_task(database)
    owner, stranger = "5" * 64, "6" * 64
    _eligible_participant(database, owner)
    _eligible_participant(database, stranger)
    assignment = database.reserve_assignment(task["id"], owner)
    raw_hash = hashlib.sha256(b"private-pdf").hexdigest()
    stored = database.create_stored_object(owner, "evidence.pdf", "application/pdf", 11, raw_hash)
    assert stored["private"] is True
    assert stored["scan_status"] == "QUARANTINED"
    with pytest.raises(ValueError, match="not clean"):
        database.create_submission(assignment["id"], owner, "Minha resposta", stored["id"])
    database.mark_stored_object_scanned(stored["id"], clean=True)
    with pytest.raises(ValueError, match="not owned"):
        database.create_submission(assignment["id"], stranger, "Tentativa indevida", stored["id"])
    submission = database.create_submission(
        assignment["id"], owner, "Minha resposta", stored["id"]
    )
    assert submission["private"] is True
    assert submission["version"] == 1
    assert len(submission["content_hash"]) == 64
    assert "content" not in submission
    assert DatabaseManager(DATABASE_URL).get_assignment(assignment["id"])["status"] == "SUBMITTED"


def test_approval_is_atomic_idempotent_audited_and_balanced(database):
    task, _, assignment, submission = _submitted_assignment(database)
    reviewer_pubkey = "b" * 64
    NostrAuth(database, session_scope="ADMIN").authenticate_demo(reviewer_pubkey)

    def approve():
        return DatabaseManager(DATABASE_URL).review_submission(
            submission["id"], reviewer_pubkey, "APPROVE", mode="SANDBOX"
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: approve(), range(2)))

    assert results[0]["review"]["id"] == results[1]["review"]["id"]
    assert (
        results[0]["payment_obligation"]["id"]
        == results[1]["payment_obligation"]["id"]
    )
    assert database.get_assignment(assignment["id"])["status"] == "PAYMENT_PENDING"
    with database.sessions() as session:
        assert session.scalar(
            select(func.count()).select_from(Review).where(
                Review.assignment_id == assignment["id"]
            )
        ) == 1
        assert session.scalar(
            select(func.count()).select_from(PaymentObligation).where(
                PaymentObligation.assignment_id == assignment["id"]
            )
        ) == 1
        transaction = session.scalar(
            select(LedgerTransaction).where(
                LedgerTransaction.reference_id == f"assignment-approval:{assignment['id']}"
            )
        )
        entries = list(
            session.scalars(
                select(LedgerEntry).where(LedgerEntry.transaction_id == transaction.id)
            )
        )
        assert {(entry.account, entry.direction) for entry in entries} == {
            ("TASK_RESERVED", "DEBIT"),
            ("PARTICIPANT_PAYABLE", "CREDIT"),
        }
        assert sum(entry.amount_sats for entry in entries if entry.direction == "DEBIT") == task["reward_sats"]
        assert sum(entry.amount_sats for entry in entries if entry.direction == "CREDIT") == task["reward_sats"]
        audit = session.scalar(
            select(AuditEvent).where(
                AuditEvent.aggregate_id == assignment["id"],
                AuditEvent.action == "SUBMISSION_APPROVE",
            )
        )
        assert audit.details["previous_status"] == "SUBMITTED"
        assert audit.details["new_status"] == "PAYMENT_PENDING"


def test_single_correction_creates_submission_v2_and_rejects_second_correction(database):
    _, _, assignment, first_submission = _submitted_assignment(database, "c" * 64)
    reviewer_pubkey = "d" * 64
    NostrAuth(database, session_scope="ADMIN").authenticate_demo(reviewer_pubkey)

    with pytest.raises(ValueError, match="justification"):
        database.review_submission(
            first_submission["id"], reviewer_pubkey, "REQUEST_CHANGES"
        )
    requested = database.review_submission(
        first_submission["id"],
        reviewer_pubkey,
        "REQUEST_CHANGES",
        "Inclua a evidência solicitada.",
    )
    assert requested["review"]["new_status"] == "CHANGES_REQUESTED"
    corrected = database.create_submission(
        assignment["id"], "c" * 64, "Entrega privada corrigida"
    )
    assert corrected["version"] == 2
    assert database.get_assignment(assignment["id"])["status"] == "RESUBMITTED"

    with pytest.raises(ReviewConflict, match="single correction"):
        database.review_submission(
            corrected["id"],
            reviewer_pubkey,
            "REQUEST_CHANGES",
            "Uma segunda correção não é permitida.",
        )
    approved = database.review_submission(
        corrected["id"], reviewer_pubkey, "APPROVE", mode="SANDBOX"
    )
    assert approved["payment_obligation"]["assignment_id"] == assignment["id"]


def test_ledger_failure_rolls_back_review_obligation_and_assignment(database):
    _, _, assignment, submission = _submitted_assignment(database, "e" * 64)
    reviewer_pubkey = "f" * 64
    NostrAuth(database, session_scope="ADMIN").authenticate_demo(reviewer_pubkey)
    database.post_ledger_transaction(
        "CONFLICT_FIXTURE",
        f"assignment-approval:{assignment['id']}",
        "SANDBOX",
        [
            {"account": "FIXTURE", "direction": "DEBIT", "amount_sats": 1},
            {"account": "FIXTURE", "direction": "CREDIT", "amount_sats": 1},
        ],
    )

    with pytest.raises(ReviewConflict):
        database.review_submission(
            submission["id"], reviewer_pubkey, "APPROVE", mode="SANDBOX"
        )

    assert database.get_assignment(assignment["id"])["status"] == "SUBMITTED"
    assert database.get_obligation(assignment["id"]) is None
    with database.sessions() as session:
        assert session.scalar(
            select(func.count()).select_from(Review).where(
                Review.assignment_id == assignment["id"]
            )
        ) == 0
        assert session.scalar(
            select(func.count()).select_from(AuditEvent).where(
                AuditEvent.aggregate_id == assignment["id"]
            )
        ) == 0


def test_review_and_obligation_economic_fields_are_append_only(database):
    _, _, assignment, submission = _submitted_assignment(database, "1" * 64)
    reviewer_pubkey = "2" * 64
    NostrAuth(database, session_scope="ADMIN").authenticate_demo(reviewer_pubkey)
    result = database.review_submission(
        submission["id"], reviewer_pubkey, "APPROVE", mode="SANDBOX"
    )

    owner_engine = create_engine(MIGRATION_DATABASE_URL)
    with pytest.raises(DBAPIError):
        with owner_engine.begin() as connection:
            connection.execute(
                text("UPDATE reviews SET reason = 'mutated' WHERE id = :id"),
                {"id": result["review"]["id"]},
            )
    with pytest.raises(DBAPIError):
        with owner_engine.begin() as connection:
            connection.execute(
                text("UPDATE payment_obligations SET amount_sats = amount_sats + 1 WHERE id = :id"),
                {"id": result["payment_obligation"]["id"]},
            )
    with pytest.raises(DBAPIError):
        with owner_engine.begin() as connection:
            connection.execute(
                text("UPDATE payment_obligations SET status = 'CLEARING' WHERE id = :id"),
                {"id": result["payment_obligation"]["id"]},
            )
    assert database.get_obligation(assignment["id"])["status"] == "OPEN"
    owner_engine.dispose()


def test_onboarding_survives_restart_and_completes_atomically(database):
    auth = NostrAuth(database)
    participant = auth.authenticate_demo("d" * 64)
    draft = database.create_onboarding_draft(participant.pubkey)
    restarted = DatabaseManager(DATABASE_URL)
    updated = restarted.update_onboarding_draft(
        draft["id"],
        participant.pubkey,
        {
            "name": "Ada",
            "email": "ada@example.test",
            "identity": {"document": "verified"},
            "skills": ["python"],
            "verification": "manual",
            "consent": True,
        },
    )
    assert updated["name"] == "Ada"

    completed = restarted.complete_onboarding_draft(
        draft["id"],
        participant.pubkey,
        ("name", "email", "identity", "skills", "verification", "consent"),
    )
    assert completed["status"] == "COMPLETED"
    with pytest.raises(ValueError, match="completed onboarding"):
        restarted.update_onboarding_draft(draft["id"], participant.pubkey, {"name": "Changed"})
    other = auth.authenticate_demo("e" * 64)
    assert restarted.get_onboarding_draft(draft["id"], other.pubkey) is None
    with database.sessions() as session:
        assert session.get(OnboardingDraft, draft["id"]).status == "COMPLETED"
        assert session.scalar(
            select(func.count()).select_from(OutboxEvent).where(OutboxEvent.aggregate_id == draft["id"])
        ) == 1
        assert session.scalar(
            select(func.count()).select_from(AuditEvent).where(AuditEvent.aggregate_id == draft["id"])
        ) == 1


def test_concurrent_onboarding_creation_returns_one_active_draft(database):
    pubkey = "c" * 64
    NostrAuth(database).authenticate_demo(pubkey)

    with ThreadPoolExecutor(max_workers=2) as executor:
        drafts = list(executor.map(lambda _: database.create_onboarding_draft(pubkey), range(2)))

    assert drafts[0]["id"] == drafts[1]["id"]
    with database.sessions() as session:
        assert session.scalar(
            select(func.count()).select_from(OnboardingDraft).where(OnboardingDraft.status == "IN_PROGRESS")
        ) == 1


def test_learning_boundaries_retry_and_restart_are_persistent(database):
    pubkey = "7" * 64
    NostrAuth(database).authenticate_demo(pubkey)
    answers_hash = "a" * 64

    failed, evidence = database.record_quiz_attempt(
        pubkey, "course", "v1", "module", "v1", 79, answers_hash
    )
    assert failed["score"] == 79
    assert evidence is None

    restarted = DatabaseManager(DATABASE_URL)
    passed, evidence = restarted.record_quiz_attempt(
        pubkey, "course", "v1", "module", "v1", 80, "b" * 64
    )
    assert passed["attempt_number"] == 2
    assert evidence["score"] == 80
    evidence_id = evidence["id"]

    third, repeated_evidence = DatabaseManager(DATABASE_URL).record_quiz_attempt(
        pubkey, "course", "v1", "module", "v1", 100, "c" * 64
    )
    assert third["attempt_number"] == 3
    assert repeated_evidence["id"] == evidence_id
    enrollment = restarted.enroll_learning(pubkey, "course", "v1")
    assert enrollment["status"] == "COMPLETED"
    assert enrollment["progress"] == 100
    assert enrollment["attempt_count"] == 3
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(QuizAttempt)) == 3
        assert session.scalar(select(func.count()).select_from(SkillEvidence)) == 1
        assert session.scalar(
            select(func.count()).select_from(OutboxEvent).where(
                OutboxEvent.event_type.in_(("QuizPassed", "SkillEvidenceCreated"))
            )
        ) == 2
    migration_engine = create_engine(MIGRATION_DATABASE_URL)
    try:
        with pytest.raises(DBAPIError):
            with migration_engine.begin() as connection:
                connection.execute(
                    text("UPDATE quiz_attempts SET score = 0 WHERE id = :attempt_id"),
                    {"attempt_id": failed["id"]},
                )
        with pytest.raises(DBAPIError):
            with migration_engine.begin() as connection:
                connection.execute(
                    text("DELETE FROM skill_evidence WHERE id = :evidence_id"),
                    {"evidence_id": evidence_id},
                )
    finally:
        migration_engine.dispose()


def test_concurrent_passing_attempts_create_one_skill_evidence(database):
    pubkey = "8" * 64
    NostrAuth(database).authenticate_demo(pubkey)

    def submit(suffix):
        return database.record_quiz_attempt(
            pubkey, "course", "v1", "module", "v1", 80, suffix * 64
        )[1]["id"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        evidence_ids = list(executor.map(submit, ("d", "e")))

    assert evidence_ids[0] == evidence_ids[1]
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(QuizAttempt)) == 2
        assert session.scalar(select(func.count()).select_from(SkillEvidence)) == 1


def test_learning_notes_and_activity_survive_restart(database):
    pubkey = "9" * 64
    NostrAuth(database).authenticate_demo(pubkey)
    database.save_learning_note(pubkey, "course", "lesson", "Minha nota")
    submitted = database.submit_learning_activity(pubkey, "course", "activity", "Entrega")

    restarted = DatabaseManager(DATABASE_URL)
    assert restarted.get_learning_note(pubkey, "course", "lesson")["content"] == "Minha nota"
    assert submitted["status"] == "SUBMITTED"
    with pytest.raises(ValueError, match="already submitted"):
        restarted.submit_learning_activity(pubkey, "course", "activity", "Outra")


def test_badge_consent_is_persistent_idempotent_and_owner_bound(database):
    owner_pubkey = "a" * 64
    other_pubkey = "b" * 64
    NostrAuth(database).authenticate_demo(owner_pubkey)
    NostrAuth(database).authenticate_demo(other_pubkey)
    _, evidence = database.record_quiz_attempt(
        owner_pubkey, "course", "v1", "module", "v1", 80, "f" * 64
    )
    definition = {
        "id": "course-v1",
        "identifier": "course-v1",
        "name": "Curso",
        "description": "Curso concluído.",
    }

    first = database.consent_badge_publication(owner_pubkey, evidence["id"], definition)
    restarted = DatabaseManager(DATABASE_URL)
    repeated = restarted.consent_badge_publication(owner_pubkey, evidence["id"], definition)

    assert repeated["id"] == first["id"]
    assert restarted.get_badge_publication(owner_pubkey, evidence["id"])["status"] == "PUBLISH_PENDING"
    assert restarted.get_badge_publication(other_pubkey, evidence["id"]) is None
    with pytest.raises(ValueError, match="skill evidence not found"):
        restarted.consent_badge_publication(other_pubkey, evidence["id"], definition)
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(BadgeDefinition)) == 1
        assert session.scalar(select(func.count()).select_from(BadgeConsent)) == 1
        assert session.scalar(select(func.count()).select_from(BadgePublication)) == 1
        assert session.scalar(
            select(func.count()).select_from(OutboxEvent).where(
                OutboxEvent.event_type == "BadgePublicationRequested"
            )
        ) == 1


def test_concurrent_badge_consent_creates_one_publication_request(database):
    pubkey = "1" * 64
    NostrAuth(database).authenticate_demo(pubkey)
    _, evidence = database.record_quiz_attempt(
        pubkey, "course", "v1", "module", "v1", 80, "1" * 64
    )
    definition = {
        "id": "course-v1",
        "identifier": "course-v1",
        "name": "Curso",
        "description": "Curso concluído.",
    }

    with ThreadPoolExecutor(max_workers=2) as executor:
        publications = list(
            executor.map(
                lambda _: DatabaseManager(DATABASE_URL).consent_badge_publication(
                    pubkey, evidence["id"], definition
                ),
                range(2),
            )
        )

    assert publications[0]["id"] == publications[1]["id"]
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(BadgeConsent)) == 1
        assert session.scalar(select(func.count()).select_from(BadgePublication)) == 1
        assert session.scalar(
            select(func.count()).select_from(OutboxEvent).where(
                OutboxEvent.event_type == "BadgePublicationRequested"
            )
        ) == 1


def test_inbox_deduplicates_provider_event(database):
    assert database.receive_inbox("lightning-sandbox", "provider-event-1", {"status": "settled"})
    assert not database.receive_inbox("lightning-sandbox", "provider-event-1", {"status": "replayed"})
    assert database.mark_inbox_processed("provider-event-1")
    assert not database.mark_inbox_processed("provider-event-1")
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(InboxEvent)) == 1


def test_outbox_workers_claim_disjoint_batches_and_publish(database):
    for number in range(4):
        obligation = database.create_obligation(f"assignment-outbox-{number}", 1000, "SANDBOX")
        database.create_payout_attempt(obligation["id"], f"idem-outbox-{number}", "SANDBOX")

    def claim(worker_id):
        return database.claim_outbox(worker_id, limit=2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first, second = list(executor.map(claim, ("worker-a", "worker-b")))
    first_ids = {event["event_id"] for event in first}
    second_ids = {event["event_id"] for event in second}
    assert len(first_ids) == len(second_ids) == 2
    assert first_ids.isdisjoint(second_ids)

    handled = []
    worker = OutboxWorker(database, "worker-c", lambda event: handled.append(event["event_id"]))
    assert worker.run_once()["claimed"] == 0
    for event in first:
        assert database.mark_outbox_published(event["event_id"], "worker-a")
    for event in second:
        assert database.mark_outbox_published(event["event_id"], "worker-b")
    with database.sessions() as session:
        assert session.scalar(
            select(func.count()).select_from(OutboxEvent).where(OutboxEvent.published_at.is_not(None))
        ) == 4


def test_runtime_and_owner_cannot_truncate_append_only_tables(database):
    for table_name in ("ledger_entries", "ledger_transactions", "audit_events", "quiz_attempts", "skill_evidence", "badge_definitions", "badge_consents"):
        with pytest.raises(DBAPIError):
            with database.engine.begin() as connection:
                connection.execute(text(f"TRUNCATE {table_name}"))

    migration_engine = create_engine(MIGRATION_DATABASE_URL)
    try:
        for table_name in ("ledger_entries", "ledger_transactions", "audit_events", "quiz_attempts", "skill_evidence", "badge_definitions", "badge_consents"):
            with pytest.raises(DBAPIError):
                with migration_engine.begin() as connection:
                    connection.execute(text(f"TRUNCATE {table_name}"))
    finally:
        migration_engine.dispose()


def test_obligation_survives_repository_restart(database):
    created = database.create_obligation("assignment-persistent", 1000, "SANDBOX")
    restarted = DatabaseManager(DATABASE_URL)
    assert restarted.get_obligation("assignment-persistent") == created


def test_nostr_session_survives_restart_without_storing_bearer_material(database):
    auth = NostrAuth(database)
    challenge = auth.issue_challenge()
    challenge_response = {
        "challenge": challenge.value,
        "signing": auth.signing_contract(challenge.value),
    }
    payload = signed_auth_payload(challenge_response)
    created = auth.authenticate(
        payload["challenge"], payload["pubkey"], payload["signature"], payload["event"]
    )

    restarted = NostrAuth(DatabaseManager(DATABASE_URL))
    current = restarted.current(created.token)
    assert current is not None
    assert current.pubkey == payload["pubkey"]

    challenge_hash = hashlib.sha256(challenge.value.encode()).hexdigest()
    token_hash = hashlib.sha256(created.token.encode()).hexdigest()
    with database.sessions() as session:
        assert session.get(AuthChallenge, challenge_hash) is not None
        assert session.get(ParticipantSession, token_hash) is not None
        assert session.get(AuthChallenge, challenge.value) is None
        assert session.get(ParticipantSession, created.token) is None

    with pytest.raises(ValueError, match="invalid, expired, or exhausted challenge"):
        restarted.authenticate(
            payload["challenge"], payload["pubkey"], payload["signature"], payload["event"]
        )
    restarted.revoke(created.token)
    assert NostrAuth(DatabaseManager(DATABASE_URL)).current(created.token) is None


def test_nostr_attempt_limit_survives_restart(database):
    auth = NostrAuth(database, max_attempts_per_challenge=2)
    challenge = auth.issue_challenge()
    challenge_response = {
        "challenge": challenge.value,
        "signing": auth.signing_contract(challenge.value),
    }
    valid = signed_auth_payload(challenge_response, 4)
    invalid = {
        **valid,
        "signature": "00" * 64,
        "event": {**valid["event"], "sig": "00" * 64},
    }

    for _ in range(2):
        with pytest.raises(ValueError, match="invalid Nostr signature"):
            auth.authenticate(
                invalid["challenge"],
                invalid["pubkey"],
                invalid["signature"],
                invalid["event"],
            )

    restarted = NostrAuth(DatabaseManager(DATABASE_URL), max_attempts_per_challenge=2)
    with pytest.raises(ValueError, match="exhausted challenge"):
        restarted.authenticate(
            valid["challenge"], valid["pubkey"], valid["signature"], valid["event"]
        )

def test_readiness_reports_real_postgres(database):
    class PostgresTestConfig(Config):
        TESTING = True
        DATABASE_URL = DATABASE_URL

    response = create_app(PostgresTestConfig).test_client().get("/health/ready")
    assert response.status_code == 200
    assert response.json["dependencies"]["database"] == "ready"


def test_attempt_and_outbox_are_atomic_and_idempotent(database):
    obligation = database.create_obligation("assignment-atomic", 1000, "SANDBOX")
    first = database.create_payout_attempt(obligation["id"], "idem-atomic", "SANDBOX")
    repeated = database.create_payout_attempt(obligation["id"], "idem-atomic", "SANDBOX")
    assert repeated == first
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(PayoutAttempt)) == 1
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
        assert database.get_obligation("assignment-atomic")["status"] == "CLEARING"


def test_terminal_idempotency_returns_original_and_blocks_new_key(database):
    obligation = database.create_obligation("assignment-terminal", 1000, "SANDBOX")
    first = database.create_payout_attempt(
        obligation["id"],
        "idem-terminal",
        "SANDBOX",
        invoice_metadata=_sandbox_invoice_metadata(1000, "4"),
    )
    database.mark_payout_processing(first["id"], provider="SANDBOX")
    database.reconcile_payout_attempt(
        first["id"],
        outcome="FAILED",
        provider_event_id="terminal-failed",
    )
    assert database.create_payout_attempt(obligation["id"], "idem-terminal", "SANDBOX") == {
        **first,
        "status": "FAILED",
        "failure_code": "PROVIDER_FAILED",
    }
    replacement = database.create_payout_attempt(
        obligation["id"],
        "idem-terminal-new",
        "SANDBOX",
        invoice_metadata=_sandbox_invoice_metadata(1000, "5"),
    )
    assert replacement["id"] != first["id"]


def test_settled_obligation_cannot_be_reopened(database):
    obligation = database.create_obligation("assignment-settled", 1000, "SANDBOX")
    attempt = database.create_payout_attempt(
        obligation["id"],
        "idem-settled",
        "SANDBOX",
        invoice_metadata=_sandbox_invoice_metadata(1000, "6"),
    )
    database.mark_payout_processing(attempt["id"], provider="SANDBOX")
    database.reconcile_payout_attempt(
        attempt["id"],
        outcome="SETTLED",
        provider_event_id="terminal-settled",
    )
    with pytest.raises(ObligationNotOpen):
        database.create_payout_attempt(obligation["id"], "idem-after-settlement", "SANDBOX")


def test_idempotency_key_cannot_cross_obligations(database):
    first = database.create_obligation("assignment-idem-first", 1000, "SANDBOX")
    second = database.create_obligation("assignment-idem-second", 1000, "SANDBOX")
    database.create_payout_attempt(first["id"], "idem-global", "SANDBOX")
    with pytest.raises(IdempotencyConflict):
        database.create_payout_attempt(second["id"], "idem-global", "SANDBOX")


def test_concurrent_idempotency_key_across_obligations_returns_controlled_conflict(database):
    first = database.create_obligation("assignment-idem-race-first", 1000, "SANDBOX")
    second = database.create_obligation("assignment-idem-race-second", 1000, "SANDBOX")

    def create(obligation_id):
        try:
            database.create_payout_attempt(obligation_id, "idem-global-race", "SANDBOX")
            return "created"
        except IdempotencyConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(create, (first["id"], second["id"])))
    assert sorted(results) == ["conflict", "created"]
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(PayoutAttempt)) == 1
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1


def test_idempotency_lock_timeout_is_bounded_and_recoverable(database):
    obligation = database.create_obligation("assignment-lock-timeout", 1000, "SANDBOX")
    key = "idem-lock-timeout"
    migration_engine = create_engine(MIGRATION_DATABASE_URL)
    try:
        with migration_engine.connect() as blocker:
            transaction = blocker.begin()
            blocker.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:idempotency_key, 0))"),
                {"idempotency_key": key},
            )
            started_at = monotonic()
            with pytest.raises(IdempotencyLockTimeout):
                DatabaseManager(DATABASE_URL, idempotency_lock_timeout_ms=100).create_payout_attempt(
                    obligation["id"], key, "SANDBOX"
                )
            assert monotonic() - started_at < 1.0
            transaction.rollback()
    finally:
        migration_engine.dispose()
    assert database.get_obligation("assignment-lock-timeout")["status"] == "OPEN"


def test_concurrent_attempts_allow_only_one_active(database):
    obligation = database.create_obligation("assignment-race", 1000, "SANDBOX")

    def create(key):
        try:
            return ("created", database.create_payout_attempt(obligation["id"], key, "SANDBOX")["id"])
        except ActivePayoutAttempt:
            return ("blocked", key)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(create, ("idem-race-a", "idem-race-b")))
    assert sorted(result[0] for result in results) == ["blocked", "created"]
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(PayoutAttempt)) == 1
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1


def test_partial_unique_index_blocks_bypass_of_repository(database):
    obligation = database.create_obligation("assignment-constraint", 1000, "SANDBOX")
    with pytest.raises(IntegrityError):
        with database.sessions.begin() as session:
            session.add_all(
                [
                    PayoutAttempt(id="attempt-a", payment_obligation_id=obligation["id"], idempotency_key="constraint-a", status="VALIDATED", mode="SANDBOX"),
                    PayoutAttempt(id="attempt-b", payment_obligation_id=obligation["id"], idempotency_key="constraint-b", status="AMBIGUOUS", mode="SANDBOX"),
                ]
            )


def test_outbox_and_state_roll_back_together(database):
    obligation = database.create_obligation("assignment-rollback", 1000, "SANDBOX")
    with pytest.raises(IntegrityError):
        database.create_payout_attempt(obligation["id"], "idem-rollback", "INVALID")
    assert database.get_obligation("assignment-rollback")["status"] == "OPEN"
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(PayoutAttempt)) == 0
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0


def test_ledger_requires_balance_and_is_append_only(database):
    with pytest.raises(UnbalancedLedgerTransaction):
        database.post_ledger_transaction(
            "Invalid",
            "unbalanced-reference",
            "SANDBOX",
            [
                {"account": "TASK_RESERVED", "direction": "DEBIT", "amount_sats": 1000},
                {"account": "PARTICIPANT_PAYABLE", "direction": "CREDIT", "amount_sats": 999},
            ],
        )
    transaction_id = database.post_ledger_transaction(
        "SubmissionApproved",
        "balanced-reference",
        "SANDBOX",
        [
            {"account": "TASK_RESERVED", "direction": "DEBIT", "amount_sats": 1000},
            {"account": "PARTICIPANT_PAYABLE", "direction": "CREDIT", "amount_sats": 1000},
        ],
    )
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(LedgerEntry).where(LedgerEntry.transaction_id == transaction_id)) == 2
    with pytest.raises(DBAPIError):
        with database.engine.begin() as connection:
            connection.execute(text("UPDATE ledger_transactions SET event_type='Tampered' WHERE id=:id"), {"id": transaction_id})
    with database.sessions() as session:
        assert session.get(LedgerTransaction, transaction_id).event_type == "SubmissionApproved"


def test_database_rejects_unbalanced_ledger_when_repository_is_bypassed(database):
    with pytest.raises(DBAPIError):
        with database.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO ledger_transactions (id, event_type, reference_id, mode) "
                    "VALUES ('direct-unbalanced', 'Bypass', 'direct-unbalanced', 'SANDBOX')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO ledger_entries (id, transaction_id, account, direction, amount_sats) "
                    "VALUES ('direct-debit', 'direct-unbalanced', 'TASK_RESERVED', 'DEBIT', 999)"
                )
            )


def test_database_rejects_entries_added_after_ledger_commit(database):
    transaction_id = database.post_ledger_transaction(
        "SubmissionApproved",
        "closed-ledger-reference",
        "SANDBOX",
        [
            {"account": "TASK_RESERVED", "direction": "DEBIT", "amount_sats": 1000},
            {"account": "PARTICIPANT_PAYABLE", "direction": "CREDIT", "amount_sats": 1000},
        ],
    )
    with pytest.raises(DBAPIError):
        with database.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO ledger_entries (id, transaction_id, account, direction, amount_sats) VALUES "
                    "('late-debit', :transaction_id, 'TASK_RESERVED', 'DEBIT', 100), "
                    "('late-credit', :transaction_id, 'PARTICIPANT_PAYABLE', 'CREDIT', 100)"
                ),
                {"transaction_id": transaction_id},
            )
    with database.sessions() as session:
        assert session.scalar(
            select(func.count()).select_from(LedgerEntry).where(LedgerEntry.transaction_id == transaction_id)
        ) == 2


def test_anonymous_payout_attempt_requests_are_rejected(database):
    first = database.create_obligation("assignment-http-race-first", 1000, "SANDBOX")
    second = database.create_obligation("assignment-http-race-second", 1000, "SANDBOX")

    class PostgresTestConfig(Config):
        TESTING = True
        DATABASE_URL = DATABASE_URL
        FINANCIAL_MODE = "SANDBOX"

    def create(obligation_id):
        client = create_app(PostgresTestConfig).test_client()
        response = client.post(
            f"/payment-obligations/{obligation_id}/payout-attempts",
            json={"invoice": _sandbox_invoice_token(1000, "1")},
            headers={"Idempotency-Key": "idem-http-global-race"},
        )
        return response.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(create, (first["id"], second["id"])))
    assert statuses == [401, 401]
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(PayoutAttempt)) == 0
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0


def test_financial_http_reads_persisted_data_after_app_restart(database):
    participant_key = 13
    participant_pubkey = pubkey_for_private_key(participant_key)
    task, _ = _funded_published_task(database)
    _eligible_participant(database, participant_pubkey)
    assignment = database.reserve_assignment(task["id"], participant_pubkey)
    obligation = database.create_obligation(assignment["id"], 1000, "SANDBOX")

    class PostgresTestConfig(Config):
        TESTING = True
        DATABASE_URL = DATABASE_URL
        FINANCIAL_MODE = "SANDBOX"

    first_client = create_app(PostgresTestConfig).test_client()
    challenge = first_client.post("/auth/nostr/challenges").json
    assert first_client.post(
        "/auth/nostr/sessions",
        json=signed_auth_payload(challenge, participant_key),
    ).status_code == 201
    assert first_client.get(
        f"/assignments/{assignment['id']}/payment-obligation"
    ).status_code == 200
    created = first_client.post(
        f"/payment-obligations/{obligation['id']}/payout-attempts",
        json={"invoice": _sandbox_invoice_token(1000, "2")},
        headers={"Idempotency-Key": "idem-http-persistent"},
    )
    assert created.status_code == 201

    restarted_app = create_app(PostgresTestConfig)
    restarted_client = restarted_app.test_client()
    challenge = restarted_client.post("/auth/nostr/challenges").json
    assert restarted_client.post(
        "/auth/nostr/sessions",
        json=signed_auth_payload(challenge, participant_key),
    ).status_code == 201
    obligation_response = restarted_client.get(
        f"/assignments/{assignment['id']}/payment-obligation"
    )
    assert obligation_response.status_code == 200
    assert obligation_response.json["status"] == "CLEARING"
    assert restarted_app.config["DATABASE"].get_attempt_for_obligation(obligation["id"])["id"] == created.json["id"]


def test_paid_work_http_flow_is_persistent_and_keeps_upload_quarantined(database):
    admin_key, participant_key = 11, 12
    admin_pubkey = pubkey_for_private_key(admin_key)
    owner = DatabaseManager(MIGRATION_DATABASE_URL)
    owner.grant_role(admin_pubkey, "ADMIN")
    owner.grant_role(admin_pubkey, "REVIEWER")

    class PostgresWorkConfig(Config):
        TESTING = True
        DATABASE_URL = DATABASE_URL
        ADMIN_PUBKEYS = {admin_pubkey}

    app = create_app(PostgresWorkConfig)
    admin = app.test_client()
    challenge = admin.post("/admin/auth/nostr/challenges").json
    assert admin.post(
        "/admin/auth/nostr/sessions", json=signed_auth_payload(challenge, admin_key)
    ).status_code == 201
    company = admin.post("/admin/companies", json={"name": "Acme"}).json
    task = admin.post(
        "/admin/paid-tasks",
        json={"company_id": company["id"], "title": "Tarefa", "reward_sats": 1000},
    ).json
    assert admin.post(f"/admin/paid-tasks/{task['id']}/publish").status_code == 409
    assert admin.post(
        f"/admin/paid-tasks/{task['id']}/funding-reservations",
        json={
            "amount_sats": 1000,
            "sources": [{"account": "COMPANY_FUNDS", "amount_sats": 1000}],
        },
    ).status_code == 201
    assert admin.post(f"/admin/paid-tasks/{task['id']}/publish").status_code == 200

    restarted = create_app(PostgresWorkConfig)
    participant = restarted.test_client()
    challenge = participant.post("/auth/nostr/challenges").json
    assert participant.post(
        "/auth/nostr/sessions", json=signed_auth_payload(challenge, participant_key)
    ).status_code == 201
    assert participant.post(
        "/modules/bluejet-basics-quiz/quiz-attempts",
        json={
            "answers": {
                "q1": "planejar",
                "q2": "evidencia",
                "q3": "revisor",
                "q4": "80",
                "q5": "competencia",
            }
        },
    ).status_code == 201
    eligible = participant.get("/paid-tasks?eligible=true").json["items"]
    assert [item["id"] for item in eligible] == [task["id"]]
    assignment = participant.post(
        f"/paid-tasks/{task['id']}/assignment-reservations"
    ).json
    saved_draft = participant.put(
        f"/assignments/{assignment['id']}/submissions/draft",
        json={"content": "Rascunho privado"},
    )
    assert saved_draft.status_code == 200
    assert saved_draft.json["private"] is True
    assert participant.get(
        f"/assignments/{assignment['id']}/submissions/draft"
    ).json["content"] == "Rascunho privado"
    upload = participant.post(
        "/uploads",
        json={
            "filename": "evidence.pdf",
            "mime_type": "application/pdf",
            "size": 11,
            "content_hash": hashlib.sha256(b"private-pdf").hexdigest(),
        },
    )
    assert upload.status_code == 201
    assert upload.json["scan_status"] == "QUARANTINED"
    assert participant.post(
        f"/assignments/{assignment['id']}/submissions",
        json={"stored_object_id": upload.json["id"]},
    ).status_code == 409
    submitted = participant.post(
        f"/assignments/{assignment['id']}/submissions",
        json={"content": "Resposta privada"},
    )
    assert submitted.status_code == 201
    assert submitted.json["private"] is True
    assert restarted.config["DATABASE"].get_assignment(assignment["id"])["status"] == "SUBMITTED"

    queue = admin.get("/admin/review-queue")
    assert queue.status_code == 200
    assert [item["id"] for item in queue.json["items"]] == [submitted.json["id"]]
    detail = admin.get(f"/admin/submissions/{submitted.json['id']}")
    assert detail.status_code == 200
    assert detail.json["content"] == "Resposta privada"
    approved = admin.post(
        f"/admin/submissions/{submitted.json['id']}/reviews",
        json={"decision": "APPROVE"},
    )
    assert approved.status_code == 201
    repeated = admin.post(
        f"/admin/submissions/{submitted.json['id']}/reviews",
        json={"decision": "APPROVE"},
    )
    assert repeated.status_code == 201
    assert (
        approved.json["payment_obligation"]["id"]
        == repeated.json["payment_obligation"]["id"]
    )
    obligation = participant.get(
        f"/assignments/{assignment['id']}/payment-obligation"
    )
    assert obligation.status_code == 200
    assert obligation.json["status"] == "OPEN"
    assert obligation.json["mode"] == "SANDBOX"


class PostgresRbacConfig(Config):
    TESTING = True
    DATABASE_URL = DATABASE_URL
    ADMIN_PUBKEYS = set()


def _public_only_session(app, client, pubkey, *, administrative=False):
    auth_key = "ADMIN_NOSTR_AUTH" if administrative else "NOSTR_AUTH"
    cookie_key = "ADMIN_SESSION_COOKIE_NAME" if administrative else "SESSION_COOKIE_NAME"
    session = app.config[auth_key].authenticate_demo(pubkey)
    client.set_cookie(
        app.config[cookie_key],
        session.token,
        path="/admin" if administrative else "/",
    )


def test_rbac_participant_accesses_participant_route(database):
    participant_pubkey = "1" * 64
    app = create_app(PostgresRbacConfig)
    client = app.test_client()
    _public_only_session(app, client, participant_pubkey)

    response = client.get("/me")
    assert response.status_code == 200
    assert response.json["roles"] == ["PARTICIPANT"]
    assert database.roles_for_pubkey(participant_pubkey) == {"PARTICIPANT"}


def test_rbac_participant_is_blocked_from_organization_route(database):
    participant_pubkey = "2" * 64
    company = DatabaseManager(MIGRATION_DATABASE_URL).create_company("Org RBAC")
    app = create_app(PostgresRbacConfig)
    client = app.test_client()
    _public_only_session(app, client, participant_pubkey)

    assert client.get(f"/organization/companies/{company['id']}").status_code == 403


def test_rbac_organization_accesses_its_company(database):
    organization_pubkey = "3" * 64
    owner = DatabaseManager(MIGRATION_DATABASE_URL)
    company = owner.create_company("Organização autorizada")
    other_company = owner.create_company("Organização de outro tenant")
    owner.grant_role(organization_pubkey, "ORGANIZATION")
    owner.add_company_membership(organization_pubkey, company["id"])
    app = create_app(PostgresRbacConfig)
    client = app.test_client()
    _public_only_session(app, client, organization_pubkey)

    response = client.get(f"/organization/companies/{company['id']}")
    assert response.status_code == 200
    assert response.json["id"] == company["id"]
    assert client.get(
        f"/organization/companies/{other_company['id']}"
    ).status_code == 403


def test_rbac_organization_is_blocked_from_admin_route(database):
    organization_pubkey = "4" * 64
    owner = DatabaseManager(MIGRATION_DATABASE_URL)
    owner.grant_role(organization_pubkey, "ORGANIZATION")
    app = create_app(PostgresRbacConfig)
    client = app.test_client()
    _public_only_session(app, client, organization_pubkey)

    assert client.get("/admin/review-queue").status_code == 403


def test_rbac_admin_reviewer_accesses_administrative_route(database):
    admin_pubkey = "5" * 64
    owner = DatabaseManager(MIGRATION_DATABASE_URL)
    owner.grant_role(admin_pubkey, "ADMIN")
    owner.grant_role(admin_pubkey, "REVIEWER")
    app = create_app(PostgresRbacConfig)
    client = app.test_client()
    _public_only_session(app, client, admin_pubkey, administrative=True)

    assert client.get("/admin/review-queue").status_code == 200
    assert database.roles_for_pubkey(admin_pubkey) == {
        "PARTICIPANT",
        "ADMIN",
        "REVIEWER",
    }


def test_rbac_unknown_pubkey_receives_403_for_specific_role(database):
    unknown_pubkey = "6" * 64
    owner = DatabaseManager(MIGRATION_DATABASE_URL)
    company = owner.create_company("Organização restrita")
    app = create_app(PostgresRbacConfig)
    client = app.test_client()
    _public_only_session(app, client, unknown_pubkey)

    assert client.get(f"/organization/companies/{company['id']}").status_code == 403


def test_rbac_client_role_injection_is_rejected_without_persistence(database):
    attacker_pubkey = "7" * 64
    app = create_app(PostgresRbacConfig)
    client = app.test_client()

    response = client.post(
        "/auth/nostr/sessions",
        json={"pubkey": attacker_pubkey, "role": "ADMIN"},
    )
    assert response.status_code == 422
    assert database.roles_for_pubkey(attacker_pubkey) == set()


def test_rbac_runtime_connection_cannot_grant_privileged_role(database):
    with pytest.raises(DBAPIError):
        database.grant_role("8" * 64, "ADMIN")


def test_rbac_owner_seed_is_idempotent_and_role_revocation_is_one_way(database):
    organization_pubkey = "9" * 64
    owner = DatabaseManager(MIGRATION_DATABASE_URL)
    company = owner.create_company("Seed idempotente")

    first_role = owner.grant_role(organization_pubkey, "ORGANIZATION")
    second_role = owner.grant_role(organization_pubkey, "ORGANIZATION")
    first_membership = owner.add_company_membership(
        organization_pubkey, company["id"]
    )
    second_membership = owner.add_company_membership(
        organization_pubkey, company["id"]
    )

    assert first_role["id"] == second_role["id"]
    assert first_membership["id"] == second_membership["id"]
    assert owner.revoke_role(organization_pubkey, "ORGANIZATION") is True
    assert owner.revoke_role(organization_pubkey, "ORGANIZATION") is False
    assert owner.roles_for_pubkey(organization_pubkey) == {"PARTICIPANT"}


def _sandbox_invoice_metadata(amount_sats=1000, marker="a"):
    return {
        "invoice_hash": marker * 64,
        "payment_hash": marker.upper() * 64,
        "network": "regtest",
        "amount_sats": amount_sats,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
    }


def _sandbox_invoice_token(amount_sats=1000, marker="a"):
    expires_at = int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp())
    return f"lnsbx:regtest:{amount_sats}:{expires_at}:{marker * 64}"


def test_phase6_attempt_persists_only_sanitized_invoice_metadata_and_clearing_ledger(database):
    obligation = database.create_obligation("assignment-phase6-metadata", 1000, "SANDBOX")
    attempt = database.create_payout_attempt(
        obligation["id"],
        "idem-phase6-metadata",
        "SANDBOX",
        invoice_metadata=_sandbox_invoice_metadata(),
    )

    assert attempt["status"] == "VALIDATED"
    assert attempt["invoice_network"] == "regtest"
    assert attempt["invoice_amount_sats"] == 1000
    assert "invoice" not in attempt
    with database.sessions() as session:
        stored = session.get(PayoutAttempt, attempt["id"])
        assert stored.invoice_hash == "a" * 64
        assert stored.payment_hash == "a" * 64
        transaction = session.scalar(
            select(LedgerTransaction).where(
                LedgerTransaction.reference_id == f"payout-dispatch:{attempt['id']}"
            )
        )
        entries = session.scalars(
            select(LedgerEntry).where(LedgerEntry.transaction_id == transaction.id)
        ).all()
        assert {(entry.account, entry.direction, entry.amount_sats) for entry in entries} == {
            ("PARTICIPANT_PAYABLE", "DEBIT", 1000),
            ("LIGHTNING_CLEARING", "CREDIT", 1000),
        }


def test_phase6_ambiguous_blocks_retry_and_reconciles_once_to_receipt(database):
    obligation = database.create_obligation("assignment-phase6-ambiguous", 1200, "SANDBOX")
    attempt = database.create_payout_attempt(
        obligation["id"],
        "idem-phase6-ambiguous",
        "SANDBOX",
        invoice_metadata=_sandbox_invoice_metadata(1200, "b"),
    )
    database.mark_payout_processing(attempt["id"], provider="SANDBOX")
    ambiguous = database.mark_payout_ambiguous(
        attempt["id"], provider_event_id="sandbox-timeout-1"
    )
    assert ambiguous["status"] == "AMBIGUOUS"
    with pytest.raises(ActivePayoutAttempt):
        database.create_payout_attempt(
            obligation["id"],
            "idem-phase6-retry-blocked",
            "SANDBOX",
            invoice_metadata=_sandbox_invoice_metadata(1200, "c"),
        )

    receipt = database.reconcile_payout_attempt(
        attempt["id"],
        outcome="SETTLED",
        provider_event_id="sandbox-settled-1",
        provider_reference="sandbox-reference-1",
    )
    repeated = database.reconcile_payout_attempt(
        attempt["id"],
        outcome="SETTLED",
        provider_event_id="sandbox-settled-1",
        provider_reference="sandbox-reference-1",
    )
    assert repeated == receipt
    assert receipt["mode"] == "SANDBOX"
    assert receipt["amount_sats"] == 1200
    assert database.get_obligation_by_id(obligation["id"])["status"] == "SETTLED"
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(PaymentReceipt)) == 1
        assert session.scalar(select(func.count()).select_from(ProviderPayment)) == 1
        assert session.scalar(select(func.count()).select_from(ProviderEvent)) == 2


def test_phase6_failed_reconciliation_compensates_and_reopens_obligation(database):
    obligation = database.create_obligation("assignment-phase6-failed", 900, "SANDBOX")
    attempt = database.create_payout_attempt(
        obligation["id"],
        "idem-phase6-failed",
        "SANDBOX",
        invoice_metadata=_sandbox_invoice_metadata(900, "d"),
    )
    database.mark_payout_processing(attempt["id"], provider="SANDBOX")
    result = database.reconcile_payout_attempt(
        attempt["id"],
        outcome="FAILED",
        provider_event_id="sandbox-failed-1",
        provider_reference="sandbox-reference-failed",
    )
    assert result["status"] == "FAILED"
    assert database.get_obligation_by_id(obligation["id"])["status"] == "OPEN"
    replacement = database.create_payout_attempt(
        obligation["id"],
        "idem-phase6-replacement",
        "SANDBOX",
        invoice_metadata=_sandbox_invoice_metadata(900, "e"),
    )
    assert replacement["id"] != attempt["id"]
    with database.sessions() as session:
        compensation = session.scalar(
            select(LedgerTransaction).where(
                LedgerTransaction.reference_id == f"payout-failed:{attempt['id']}"
            )
        )
        assert compensation is not None


def test_phase6_database_rejects_invalid_obligation_transitions(database):
    obligation = database.create_obligation("assignment-phase6-transitions", 700, "SANDBOX")
    with pytest.raises(DBAPIError):
        with DatabaseManager(MIGRATION_DATABASE_URL).sessions.begin() as session:
            session.execute(
                text("UPDATE payment_obligations SET status='SETTLED' WHERE id=:id"),
                {"id": obligation["id"]},
            )


def test_phase6_database_rejects_attempt_without_atomic_ledger_and_outbox(database):
    obligation = database.create_obligation("assignment-phase6-bypass", 700, "SANDBOX")
    with pytest.raises(DBAPIError):
        with DatabaseManager(MIGRATION_DATABASE_URL).sessions.begin() as session:
            session.add(
                PayoutAttempt(
                    id="attempt-phase6-bypass",
                    payment_obligation_id=obligation["id"],
                    idempotency_key="phase6-bypass",
                    status="VALIDATED",
                    mode="SANDBOX",
                )
            )
            session.flush()
            session.get(PaymentObligation, obligation["id"]).status = "CLEARING"


def test_phase7_donor_contribution_is_idempotent_separated_and_balanced(database):
    donor_pubkey = "a" * 64
    owner = DatabaseManager(MIGRATION_DATABASE_URL)
    owner.grant_role(donor_pubkey, "DONOR")
    first = database.create_donor_contribution(
        donor_pubkey,
        idempotency_key="donor-idem-1",
        amount_sats=10_000,
        impact_percentage_bps=6000,
        liquidity_percentage_bps=4000,
        terms_version="2026-07",
        terms_accepted=True,
        mode="SANDBOX",
    )
    repeated = database.create_donor_contribution(
        donor_pubkey,
        idempotency_key="donor-idem-1",
        amount_sats=10_000,
        impact_percentage_bps=6000,
        liquidity_percentage_bps=4000,
        terms_version="2026-07",
        terms_accepted=True,
        mode="SANDBOX",
    )

    assert repeated == first
    assert first["contribution"]["mode"] == "SANDBOX"
    assert first["receipt"]["impact_sats"] == 6000
    assert first["receipt"]["liquidity_sats"] == 4000
    assert {item["allocation_type"] for item in first["allocations"]} == {
        "IMPACT_FUND",
        "LIQUIDITY_CAPITAL",
    }
    dashboard = database.get_donor_dashboard(donor_pubkey)
    assert dashboard == {
        "mode": "SANDBOX",
        "impact_fund_sats": 6000,
        "liquidity_principal_sats": 4000,
        "contribution_count": 1,
    }
    with database.sessions() as session:
        transaction = session.scalar(
            select(LedgerTransaction).where(
                LedgerTransaction.reference_id
                == f"donor-contribution:{first['contribution']['id']}"
            )
        )
        entries = session.scalars(
            select(LedgerEntry).where(LedgerEntry.transaction_id == transaction.id)
        ).all()
        assert sum(e.amount_sats for e in entries if e.direction == "DEBIT") == 10_000
        assert sum(e.amount_sats for e in entries if e.direction == "CREDIT") == 10_000


def test_phase7_rejects_invalid_allocation_and_non_donor(database):
    donor_pubkey = "b" * 64
    owner = DatabaseManager(MIGRATION_DATABASE_URL)
    owner.grant_role(donor_pubkey, "DONOR")
    with pytest.raises(ValueError, match="10000 basis points"):
        database.create_donor_contribution(
            donor_pubkey,
            idempotency_key="donor-invalid-composition",
            amount_sats=1000,
            impact_percentage_bps=5000,
            liquidity_percentage_bps=4000,
            terms_version="2026-07",
            terms_accepted=True,
            mode="SANDBOX",
        )


def test_phase7_database_rejects_incomplete_composition_and_receipt_mutation(database):
    donor_pubkey = "7" * 64
    owner = DatabaseManager(MIGRATION_DATABASE_URL)
    owner.grant_role(donor_pubkey, "DONOR")
    with owner.sessions() as session:
        user_id = session.scalar(select(User.id).where(User.nostr_pubkey == donor_pubkey))
    with pytest.raises(DBAPIError):
        with owner.sessions.begin() as session:
            profile = DonorProfile(
                id="donor-profile-invalid-composition",
                user_id=user_id,
                display_name=None,
                terms_version="2026-07",
                created_at=datetime.now(timezone.utc),
            )
            session.add(profile)
            session.add(
                Contribution(
                    id="contribution-invalid-composition",
                    donor_profile_id=profile.id,
                    idempotency_key="invalid-direct-composition",
                    input_amount_sats=1000,
                    input_currency="SAT",
                    terms_version="2026-07",
                    terms_accepted_at=datetime.now(timezone.utc),
                    status="ALLOCATED",
                    mode="SANDBOX",
                    created_at=datetime.now(timezone.utc),
                )
            )

    created = database.create_donor_contribution(
        donor_pubkey,
        idempotency_key="donor-immutable-receipt",
        amount_sats=1000,
        impact_percentage_bps=10000,
        liquidity_percentage_bps=0,
        terms_version="2026-07",
        terms_accepted=True,
        mode="SANDBOX",
    )
    with pytest.raises(DBAPIError):
        with owner.sessions.begin() as session:
            session.execute(
                text(
                    "UPDATE contribution_receipts SET total_sats = total_sats + 1 "
                    "WHERE id = :receipt_id"
                ),
                {"receipt_id": created["receipt"]["id"]},
            )
    with pytest.raises(PermissionError):
        database.create_donor_contribution(
            "c" * 64,
            idempotency_key="not-a-donor",
            amount_sats=1000,
            impact_percentage_bps=10000,
            liquidity_percentage_bps=0,
            terms_version="2026-07",
            terms_accepted=True,
            mode="SANDBOX",
        )


def test_phase7_participant_is_blocked_and_donor_accesses_http_routes(database):
    participant_pubkey = "d" * 64
    donor_pubkey = "e" * 64
    owner = DatabaseManager(MIGRATION_DATABASE_URL)
    owner.grant_role(donor_pubkey, "DONOR")
    app = create_app(PostgresRbacConfig)
    participant_client = app.test_client()
    donor_client = app.test_client()
    _public_only_session(app, participant_client, participant_pubkey)
    _public_only_session(app, donor_client, donor_pubkey)

    payload = {
        "amount_sats": 5000,
        "impact_percentage_bps": 10000,
        "liquidity_percentage_bps": 0,
        "terms_version": "2026-07",
        "terms_accepted": True,
    }
    assert participant_client.post(
        "/donor/contributions",
        json=payload,
        headers={"Idempotency-Key": "participant-denied"},
    ).status_code == 403
    created = donor_client.post(
        "/donor/contributions",
        json=payload,
        headers={"Idempotency-Key": "donor-http-1"},
    )
    assert created.status_code == 201
    assert created.json["receipt"]["mode"] == "SANDBOX"
    history = donor_client.get("/donor/contributions")
    assert history.status_code == 200
    assert len(history.json["items"]) == 1


def test_phase6_http_enforces_owner_admin_reconciliation_and_private_receipt(database):
    participant_pubkey = "f" * 64
    other_pubkey = "0" * 64
    admin_pubkey = "1" * 64
    task, _ = _funded_published_task(database)
    _eligible_participant(database, participant_pubkey)
    assignment = database.reserve_assignment(task["id"], participant_pubkey)
    obligation = database.create_obligation(assignment["id"], 1000, "SANDBOX")
    owner = DatabaseManager(MIGRATION_DATABASE_URL)
    owner.grant_role(admin_pubkey, "ADMIN")

    app = create_app(PostgresRbacConfig)
    participant_client = app.test_client()
    other_client = app.test_client()
    admin_client = app.test_client()
    _public_only_session(app, participant_client, participant_pubkey)
    _public_only_session(app, other_client, other_pubkey)
    _public_only_session(app, admin_client, admin_pubkey, administrative=True)

    created = participant_client.post(
        f"/payment-obligations/{obligation['id']}/payout-attempts",
        json={"invoice": _sandbox_invoice_token(1000, "3")},
        headers={"Idempotency-Key": "phase6-http-owner"},
    )
    assert created.status_code == 201
    assert "invoice" not in created.json
    assert "invoice_hash" not in created.json
    assert other_client.get(
        f"/payment-obligations/{obligation['id']}/payout-status"
    ).status_code == 403

    database.mark_payout_processing(created.json["id"], provider="SANDBOX")
    reconciled = admin_client.post(
        f"/admin/payout-attempts/{created.json['id']}/reconcile",
        json={
            "outcome": "SETTLED",
            "provider_event_id": "phase6-http-settled",
            "provider_reference": "phase6-http-reference",
        },
    )
    assert reconciled.status_code == 200
    assert reconciled.json["mode"] == "SANDBOX"
    assert participant_client.get(
        f"/receipts/{reconciled.json['id']}"
    ).status_code == 200
    assert other_client.get(
        f"/receipts/{reconciled.json['id']}"
    ).status_code == 403


def test_phase8_external_opportunity_is_persistent_and_non_financial(database):
    participant_pubkey = "c" * 64
    app = create_app(PostgresRbacConfig)
    client = app.test_client()
    _public_only_session(app, client, participant_pubkey)

    created = client.post(
        "/opportunities/external",
        json={
            "title": "Curso comunitário",
            "category": "FREE_COURSE",
            "description": "Curso gratuito para a comunidade.",
            "organization_name": "Instituto aberto",
            "external_url": "https://example.org/curso",
            "format": "ONLINE",
            "starts_at": "2026-08-10T12:00:00Z",
            "application_deadline": "2026-08-09T12:00:00Z",
            "tags": ["educacao", "gratuito"],
            "requirements": "Inscrição no site externo.",
            "non_remunerated_ack": True,
        },
        headers={"Idempotency-Key": "phase8-external-course"},
    )
    assert created.status_code == 201
    assert created.json["type"] == "EXTERNAL_OPPORTUNITY"
    assert created.json["remunerated"] is False
    assert created.json["format"] == "ONLINE"
    assert created.json["non_remunerated_ack"] is True
    assert created.json["publisher_pubkey"] == participant_pubkey
    assert client.get(f"/opportunities/external/{created.json['id']}").status_code == 200
    assert client.get("/opportunities").json["external_opportunities"][0]["id"] == created.json["id"]
    repeated = client.post(
        "/opportunities/external",
        json={
            "title": "Curso comunitário", "category": "FREE_COURSE",
            "description": "Curso gratuito para a comunidade.",
            "organization_name": "Instituto aberto", "external_url": "https://example.org/curso",
            "format": "ONLINE", "starts_at": "2026-08-10T12:00:00Z",
            "application_deadline": "2026-08-09T12:00:00Z", "tags": ["educacao", "gratuito"],
            "requirements": "Inscrição no site externo.", "non_remunerated_ack": True,
        },
        headers={"Idempotency-Key": "phase8-external-course"},
    )
    assert repeated.json["id"] == created.json["id"]

    http_created = client.post(
        "/opportunities/external",
        json={
            "title": "Encontro por origem HTTP", "category": "MEETUP",
            "description": "Divulgação externa sem fluxo financeiro.",
            "organization_name": "Comunidade aberta", "external_url": "http://example.org/encontro",
            "format": "ONLINE", "starts_at": "2026-09-10T12:00:00Z", "tags": [],
            "requirements": "", "non_remunerated_ack": True,
        },
        headers={"Idempotency-Key": "phase8-external-http"},
    )
    assert http_created.status_code == 201
    assert http_created.json["external_url"] == "http://example.org/encontro"

    dangerous_url = client.post(
        "/opportunities/external",
        json={
            "title": "Origem inválida", "category": "OTHER",
            "description": "Esta divulgação deve ser recusada.",
            "organization_name": "Origem desconhecida", "external_url": "javascript:alert(1)",
            "format": "ONLINE", "starts_at": "2026-09-10T12:00:00Z", "tags": [],
            "requirements": "", "non_remunerated_ack": True,
        },
    )
    assert dangerous_url.status_code == 422


def test_phase8_local_flows_do_not_touch_relay_lightning_or_storage(database):
    class ForbiddenLightningGateway:
        calls = 0

        def validate_invoice(self, *args, **kwargs):
            self.calls += 1
            raise AssertionError("Phase 8 must not call Lightning")

    gateway = ForbiddenLightningGateway()
    phase8_config = type(
        "Phase8NoExternalEffectsConfig",
        (PostgresRbacConfig,),
        {"LIGHTNING_GATEWAY": gateway},
    )
    participant_pubkey = "9" * 64
    app = create_app(phase8_config)
    client = app.test_client()
    _public_only_session(app, client, participant_pubkey)

    post = client.post(
        "/community/posts",
        json={"category": "question", "content": "Como praticar testes?", "public_acknowledged": True},
        headers={"Idempotency-Key": "phase8-no-external-post"},
    )
    opportunity = client.post(
        "/opportunities/external",
        json={
            "title": "Encontro local", "category": "MEETUP", "description": "Encontro gratuito.",
            "organization_name": "Comunidade", "external_url": "https://example.org/encontro",
            "format": "ONLINE", "starts_at": "2026-11-10T12:00:00Z", "tags": [],
            "requirements": "", "non_remunerated_ack": True,
        },
        headers={"Idempotency-Key": "phase8-no-external-listing"},
    )

    assert post.status_code == 201
    assert post.json["relay_status"] == "LOCAL_ONLY"
    assert post.json["nostr_event_id"] is None
    assert opportunity.status_code == 201
    assert gateway.calls == 0
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(StoredObject)) == 0
        assert session.scalar(select(func.count()).select_from(PayoutAttempt)) == 0
        assert session.scalar(select(func.count()).select_from(BadgePublication)) == 0


def test_phase8_public_post_report_and_moderation_are_persistent(database):
    participant_pubkey = "d" * 64
    reporter_pubkey = "e" * 64
    moderator_pubkey = "f" * 64
    owner = DatabaseManager(MIGRATION_DATABASE_URL)
    owner.grant_role(moderator_pubkey, "REVIEWER")
    app = create_app(PostgresRbacConfig)
    participant = app.test_client()
    reporter = app.test_client()
    moderator = app.test_client()
    _public_only_session(app, participant, participant_pubkey)
    _public_only_session(app, reporter, reporter_pubkey)
    _public_only_session(app, moderator, moderator_pubkey, administrative=True)

    created = participant.post(
        "/community/posts",
        json={"category": "learning", "content": "Aprendi algo novo.", "public_acknowledged": True},
        headers={"Idempotency-Key": "phase8-learning-post"},
    )
    assert created.status_code == 201
    assert created.json["relay_status"] == "LOCAL_ONLY"
    assert participant.get("/community/feed").json["items"][0]["id"] == created.json["id"]
    reported = reporter.post(
        "/community/reports",
        json={
            "subject_type": "POST", "subject_id": created.json["id"],
            "category": "MISLEADING_CONTENT", "details": "Revisar conteúdo",
        },
    )
    assert reported.status_code == 201
    hidden = moderator.post(
        "/admin/moderation-decisions",
        json={
            "subject_type": "POST", "subject_id": created.json["id"],
            "action": "HIDE", "reason": "Violação da política",
        },
    )
    assert hidden.status_code == 201
    assert participant.get("/community/feed").json["items"] == []


def test_phase8_reports_opportunities_and_enforces_moderation_boundaries(database):
    author_pubkey = "1" * 64
    reporter_pubkey = "2" * 64
    reviewer_pubkey = "3" * 64
    owner = DatabaseManager(MIGRATION_DATABASE_URL)
    owner.grant_role(reviewer_pubkey, "REVIEWER")
    app = create_app(PostgresRbacConfig)
    author = app.test_client()
    reporter = app.test_client()
    reviewer = app.test_client()
    _public_only_session(app, author, author_pubkey)
    _public_only_session(app, reporter, reporter_pubkey)
    _public_only_session(app, reviewer, reviewer_pubkey)
    _public_only_session(app, reviewer, reviewer_pubkey, administrative=True)

    created = author.post(
        "/opportunities/external",
        json={
            "title": "Hackathon aberto", "category": "HACKATHON",
            "description": "Evento gratuito e externo.", "organization_name": "Comunidade livre",
            "external_url": "https://example.org/hackathon", "format": "HYBRID",
            "location": "São Paulo", "starts_at": "2026-09-10T12:00:00Z",
            "application_deadline": "2026-09-01T12:00:00Z", "tags": ["hackathon"],
            "requirements": "Consultar regras na origem.", "non_remunerated_ack": True,
        },
    )
    assert created.status_code == 201
    opportunity_id = created.json["id"]
    report = reporter.post(
        "/community/reports",
        json={
            "subject_type": "OPPORTUNITY", "subject_id": opportunity_id,
            "category": "MALICIOUS_LINK", "details": "Origem suspeita",
        },
    )
    assert report.status_code == 201
    assert author.get(f"/opportunities/external/{opportunity_id}").status_code == 200
    assert author.post(
        "/admin/moderation-decisions",
        json={"subject_type": "OPPORTUNITY", "subject_id": opportunity_id, "action": "HIDE", "reason": "x"},
    ).status_code == 403
    own_moderation = reviewer.post(
        "/opportunities/external",
        json={
            "title": "Evento da revisora", "category": "EVENT", "description": "Evento externo.",
            "organization_name": "Organização", "external_url": "https://example.org/evento",
            "format": "ONLINE", "starts_at": "2026-10-10T12:00:00Z", "tags": [],
            "requirements": "", "non_remunerated_ack": True,
        },
    )
    assert own_moderation.status_code == 201
    assert reviewer.post(
        "/admin/moderation-decisions",
        json={
            "subject_type": "OPPORTUNITY", "subject_id": own_moderation.json["id"],
            "action": "HIDE", "reason": "Não permitido",
        },
    ).status_code == 422
    hidden = reviewer.post(
        "/admin/moderation-decisions",
        json={
            "subject_type": "OPPORTUNITY", "subject_id": opportunity_id,
            "action": "HIDE", "reason": "Link malicioso confirmado",
        },
    )
    assert hidden.status_code == 201
    assert author.get(f"/opportunities/external/{opportunity_id}").status_code == 404
    queue = reviewer.get("/admin/community/moderation-queue")
    assert queue.status_code == 200
    assert any(item["subject_id"] == opportunity_id for item in queue.json["items"])
    restored = reviewer.post(
        "/admin/moderation-decisions",
        json={
            "subject_type": "OPPORTUNITY", "subject_id": opportunity_id,
            "action": "RESTORE", "reason": "Revisão concluída",
        },
    )
    assert restored.status_code == 201
