
"""PostgreSQL persistence primitives for financial invariants."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable
import uuid

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Integer, JSON, String, create_engine, select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


ACTIVE_ATTEMPT_STATUSES = ("CREATED", "VALIDATED", "PROCESSING", "AMBIGUOUS")


class Base(DeclarativeBase):
    pass


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    aggregate_id: Mapped[str] = mapped_column(String(36), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class PaymentObligation(Base):
    __tablename__ = "payment_obligations"
    __table_args__ = (
        CheckConstraint("amount_sats > 0", name="ck_payment_obligations_positive_amount"),
        CheckConstraint("status IN ('OPEN', 'CLEARING', 'SETTLED')", name="ck_payment_obligations_status"),
        CheckConstraint("mode IN ('MOCK', 'SANDBOX', 'REAL')", name="ck_payment_obligations_mode"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    assignment_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    amount_sats: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class PayoutAttempt(Base):
    __tablename__ = "payout_attempts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('CREATED', 'VALIDATED', 'PROCESSING', 'AMBIGUOUS', 'SETTLED', 'FAILED', 'EXPIRED')",
            name="ck_payout_attempts_status",
        ),
        CheckConstraint("mode IN ('MOCK', 'SANDBOX', 'REAL')", name="ck_payout_attempts_mode"),
        Index(
            "uq_payout_attempts_one_active_per_obligation",
            "payment_obligation_id",
            unique=True,
            postgresql_where=text("status IN ('CREATED', 'VALIDATED', 'PROCESSING', 'AMBIGUOUS')"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    payment_obligation_id: Mapped[str] = mapped_column(ForeignKey("payment_obligations.id", ondelete="RESTRICT"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    payment_hash: Mapped[str | None] = mapped_column(String(128), unique=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class LedgerTransaction(Base):
    __tablename__ = "ledger_transactions"
    __table_args__ = (CheckConstraint("mode IN ('MOCK', 'SANDBOX', 'REAL')", name="ck_ledger_transactions_mode"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (
        CheckConstraint("direction IN ('DEBIT', 'CREDIT')", name="ck_ledger_entries_direction"),
        CheckConstraint("amount_sats > 0", name="ck_ledger_entries_positive_amount"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("ledger_transactions.id", ondelete="RESTRICT"), nullable=False)
    account: Mapped[str] = mapped_column(String(120), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    amount_sats: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(36))


class ActivePayoutAttempt(RuntimeError):
    pass


class ObligationNotOpen(RuntimeError):
    pass


class IdempotencyConflict(RuntimeError):
    pass


class IdempotencyLockTimeout(RuntimeError):
    pass


class UnbalancedLedgerTransaction(ValueError):
    pass


class DatabaseManager:
    def __init__(self, database_url: str, idempotency_lock_timeout_ms: int = 1000):
        if (
            isinstance(idempotency_lock_timeout_ms, bool)
            or not isinstance(idempotency_lock_timeout_ms, int)
            or idempotency_lock_timeout_ms <= 0
        ):
            raise ValueError("idempotency_lock_timeout_ms must be a positive integer")
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)
        self.idempotency_lock_timeout_ms = idempotency_lock_timeout_ms

    def ping(self) -> bool:
        with self.engine.connect() as connection:
            return connection.execute(text("SELECT 1")).scalar_one() == 1

    def create_obligation(self, assignment_id: str, amount_sats: int, mode: str) -> dict[str, Any]:
        if isinstance(amount_sats, bool) or not isinstance(amount_sats, int) or amount_sats <= 0:
            raise ValueError("amount_sats must be a positive integer")
        obligation = PaymentObligation(id=str(uuid.uuid4()), assignment_id=assignment_id, amount_sats=amount_sats, status="OPEN", mode=mode)
        with self.sessions.begin() as session:
            session.add(obligation)
        return self._obligation_dict(obligation)

    def get_obligation(self, assignment_id: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            obligation = session.scalar(select(PaymentObligation).where(PaymentObligation.assignment_id == assignment_id))
            return self._obligation_dict(obligation) if obligation else None

    def get_obligation_by_id(self, obligation_id: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            obligation = session.get(PaymentObligation, obligation_id)
            return self._obligation_dict(obligation) if obligation else None

    def get_attempt_for_obligation(self, obligation_id: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            attempt = session.scalar(
                select(PayoutAttempt)
                .where(PayoutAttempt.payment_obligation_id == obligation_id)
                .order_by(PayoutAttempt.created_at.desc(), PayoutAttempt.id.desc())
                .limit(1)
            )
            return self._attempt_dict(attempt) if attempt else None

    def create_payout_attempt(self, obligation_id: str, idempotency_key: str, mode: str) -> dict[str, Any]:
        if not idempotency_key:
            raise ValueError("idempotency key is required")
        try:
            with self.sessions.begin() as session:
                session.execute(
                    text("SELECT set_config('lock_timeout', :timeout, true)"),
                    {"timeout": f"{self.idempotency_lock_timeout_ms}ms"},
                )
                session.execute(
                    text("SELECT set_config('statement_timeout', :timeout, true)"),
                    {"timeout": f"{max(3000, self.idempotency_lock_timeout_ms * 3)}ms"},
                )
                session.execute(
                    text("SELECT pg_advisory_xact_lock(hashtextextended(:idempotency_key, 0))"),
                    {"idempotency_key": idempotency_key},
                )
                obligation = session.scalar(
                    select(PaymentObligation).where(PaymentObligation.id == obligation_id).with_for_update()
                )
                if not obligation:
                    raise KeyError(obligation_id)
                repeated = session.scalar(select(PayoutAttempt).where(PayoutAttempt.idempotency_key == idempotency_key))
                if repeated:
                    if repeated.payment_obligation_id != obligation_id:
                        raise IdempotencyConflict("idempotency key belongs to another obligation")
                    return self._attempt_dict(repeated)
                active = session.scalar(
                    select(PayoutAttempt).where(
                        PayoutAttempt.payment_obligation_id == obligation_id,
                        PayoutAttempt.status.in_(ACTIVE_ATTEMPT_STATUSES),
                    )
                )
                if active:
                    raise ActivePayoutAttempt("active payout attempt exists")
                if obligation.status != "OPEN":
                    raise ObligationNotOpen(f"obligation is {obligation.status}")
                attempt = PayoutAttempt(
                    id=str(uuid.uuid4()),
                    payment_obligation_id=obligation_id,
                    idempotency_key=idempotency_key,
                    status="VALIDATED",
                    mode=mode,
                )
                obligation.status = "CLEARING"
                session.add(attempt)
                session.add(
                    OutboxEvent(
                        event_id=str(uuid.uuid4()),
                        event_type="PayoutDispatchRequested",
                        version=1,
                        aggregate_id=attempt.id,
                        occurred_at=datetime.now(timezone.utc),
                        payload={"payout_attempt_id": attempt.id, "mode": mode},
                        attempts=0,
                    )
                )
        except OperationalError as error:
            if getattr(error.orig, "sqlstate", None) in {"55P03", "57014"}:
                raise IdempotencyLockTimeout("idempotency lock timed out") from None
            raise
        except IntegrityError:
            with self.sessions() as session:
                repeated = session.scalar(select(PayoutAttempt).where(PayoutAttempt.idempotency_key == idempotency_key))
                if not repeated:
                    raise
                if repeated.payment_obligation_id != obligation_id:
                    raise IdempotencyConflict("idempotency key belongs to another obligation") from None
                return self._attempt_dict(repeated)
        return self._attempt_dict(attempt)

    def post_ledger_transaction(
        self,
        event_type: str,
        reference_id: str,
        mode: str,
        entries: Iterable[dict[str, Any]],
    ) -> str:
        normalized = list(entries)
        if len(normalized) < 2:
            raise UnbalancedLedgerTransaction("at least two entries are required")
        for entry in normalized:
            amount = entry.get("amount_sats")
            if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
                raise ValueError("ledger amounts must be positive integers")
            if entry.get("direction") not in {"DEBIT", "CREDIT"}:
                raise ValueError("invalid ledger direction")
        debits = sum(entry["amount_sats"] for entry in normalized if entry["direction"] == "DEBIT")
        credits = sum(entry["amount_sats"] for entry in normalized if entry["direction"] == "CREDIT")
        if debits != credits:
            raise UnbalancedLedgerTransaction("debits and credits must balance")
        transaction_id = str(uuid.uuid4())
        with self.sessions.begin() as session:
            session.add(LedgerTransaction(id=transaction_id, event_type=event_type, reference_id=reference_id, mode=mode))
            session.flush()
            session.add_all(
                LedgerEntry(
                    id=str(uuid.uuid4()),
                    transaction_id=transaction_id,
                    account=entry["account"],
                    direction=entry["direction"],
                    amount_sats=entry["amount_sats"],
                    source_id=entry.get("source_id"),
                )
                for entry in normalized
            )
        return transaction_id

    @staticmethod
    def _obligation_dict(obligation: PaymentObligation) -> dict[str, Any]:
        return {
            "id": obligation.id,
            "assignment_id": obligation.assignment_id,
            "amount_sats": obligation.amount_sats,
            "status": obligation.status,
            "mode": obligation.mode,
        }

    @staticmethod
    def _attempt_dict(attempt: PayoutAttempt) -> dict[str, Any]:
        return {
            "id": attempt.id,
            "obligation_id": attempt.payment_obligation_id,
            "idempotency_key": attempt.idempotency_key,
            "status": attempt.status,
            "mode": attempt.mode,
        }
