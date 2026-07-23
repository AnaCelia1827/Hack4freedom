"""Integration tests that must run against a real PostgreSQL database."""
from concurrent.futures import ThreadPoolExecutor
import os
from time import monotonic

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from bluejet_api import create_app
from bluejet_api.config import Config
from bluejet_api.database import (
    ActivePayoutAttempt,
    DatabaseManager,
    IdempotencyConflict,
    IdempotencyLockTimeout,
    LedgerEntry,
    LedgerTransaction,
    ObligationNotOpen,
    OutboxEvent,
    PaymentObligation,
    PayoutAttempt,
    UnbalancedLedgerTransaction,
)


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
                "TRUNCATE ledger_entries, ledger_transactions, payout_attempts, payment_obligations, "
                "outbox_events, audit_events RESTART IDENTITY CASCADE"
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


def test_runtime_and_owner_cannot_truncate_append_only_tables(database):
    for table_name in ("ledger_entries", "ledger_transactions", "audit_events"):
        with pytest.raises(DBAPIError):
            with database.engine.begin() as connection:
                connection.execute(text(f"TRUNCATE {table_name}"))

    migration_engine = create_engine(MIGRATION_DATABASE_URL)
    try:
        for table_name in ("ledger_entries", "ledger_transactions", "audit_events"):
            with pytest.raises(DBAPIError):
                with migration_engine.begin() as connection:
                    connection.execute(text(f"TRUNCATE {table_name}"))
    finally:
        migration_engine.dispose()


def test_obligation_survives_repository_restart(database):
    created = database.create_obligation("assignment-persistent", 1000, "SANDBOX")
    restarted = DatabaseManager(DATABASE_URL)
    assert restarted.get_obligation("assignment-persistent") == created


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
    first = database.create_payout_attempt(obligation["id"], "idem-terminal", "SANDBOX")
    with database.sessions.begin() as session:
        session.get(PayoutAttempt, first["id"]).status = "FAILED"
    assert database.create_payout_attempt(obligation["id"], "idem-terminal", "SANDBOX") == {
        **first,
        "status": "FAILED",
    }
    with pytest.raises(ObligationNotOpen):
        database.create_payout_attempt(obligation["id"], "idem-terminal-new", "SANDBOX")


def test_settled_obligation_cannot_be_reopened(database):
    obligation = database.create_obligation("assignment-settled", 1000, "SANDBOX")
    attempt = database.create_payout_attempt(obligation["id"], "idem-settled", "SANDBOX")
    with database.sessions.begin() as session:
        session.get(PayoutAttempt, attempt["id"]).status = "SETTLED"
        stored = session.get(PaymentObligation, obligation["id"])
        stored.status = "SETTLED"
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


def test_concurrent_idempotency_key_across_http_requests_returns_409(database):
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
            json={"invoice": "sandbox-invoice-not-stored"},
            headers={"Idempotency-Key": "idem-http-global-race"},
        )
        return response.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(create, (first["id"], second["id"])))
    assert sorted(statuses) == [201, 409]
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(PayoutAttempt)) == 1
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1


def test_financial_http_reads_persisted_data_after_app_restart(database):
    obligation = database.create_obligation("assignment-http-persistent", 1000, "SANDBOX")

    class PostgresTestConfig(Config):
        TESTING = True
        DATABASE_URL = DATABASE_URL
        FINANCIAL_MODE = "SANDBOX"

    first_client = create_app(PostgresTestConfig).test_client()
    assert first_client.get("/assignments/assignment-http-persistent/payment-obligation").status_code == 200
    created = first_client.post(
        f"/payment-obligations/{obligation['id']}/payout-attempts",
        json={"invoice": "sandbox-invoice-not-stored"},
        headers={"Idempotency-Key": "idem-http-persistent"},
    )
    assert created.status_code == 201

    restarted_app = create_app(PostgresTestConfig)
    restarted_client = restarted_app.test_client()
    obligation_response = restarted_client.get("/assignments/assignment-http-persistent/payment-obligation")
    assert obligation_response.status_code == 200
    assert obligation_response.json["status"] == "CLEARING"
    assert restarted_app.config["DATABASE"].get_attempt_for_obligation(obligation["id"])["id"] == created.json["id"]
