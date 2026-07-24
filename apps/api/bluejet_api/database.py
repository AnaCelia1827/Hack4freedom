
"""PostgreSQL persistence primitives for financial invariants."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable
import hashlib
import re
import uuid
from urllib.parse import urlparse

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, create_engine, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .auth import normalize_nostr_pubkey


ACTIVE_ATTEMPT_STATUSES = ("CREATED", "VALIDATED", "PROCESSING", "AMBIGUOUS")
OPPORTUNITY_TYPES = {
    "HACKATHON", "FREE_COURSE", "EVENT", "TALK", "MEETUP", "MENTORSHIP",
    "EDUCATIONAL_PROGRAM", "OTHER",
}
OPPORTUNITY_FORMATS = {"ONLINE", "ONSITE", "HYBRID"}
REPORT_CATEGORIES = {
    "SPAM", "FRAUD", "PERSONAL_DATA", "HARASSMENT", "MISLEADING_CONTENT",
    "MALICIOUS_LINK", "OUT_OF_SCOPE", "OTHER",
}


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
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    claimed_by: Mapped[str | None] = mapped_column(String(120))
    last_error: Mapped[str | None] = mapped_column(String(240))


class InboxEvent(Base):
    __tablename__ = "inbox_events"

    provider_event_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditEvent(Base):
    __tablename__ = "audit_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    actor_id: Mapped[str | None] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(80), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(36), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)


class OnboardingDraft(Base):
    __tablename__ = "onboarding_drafts"
    __table_args__ = (
        CheckConstraint("status IN ('IN_PROGRESS', 'COMPLETED')", name="ck_onboarding_drafts_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="IN_PROGRESS")
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "nostr_pubkey ~ '^[0-9a-f]{64}$'",
            name="ck_users_nostr_pubkey_hex",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    nostr_pubkey: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        CheckConstraint(
            "role IN ('PARTICIPANT', 'ORGANIZATION', 'DONOR', 'REVIEWER', 'ADMIN')",
            name="ck_user_roles_role",
        ),
        Index(
            "uq_user_roles_active_user_role",
            "user_id",
            "role",
            unique=True,
            postgresql_where=text("revoked_at IS NULL"),
        ),
        Index(
            "ix_user_roles_active_role",
            "role",
            postgresql_where=text("revoked_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    granted_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CompanyMembership(Base):
    __tablename__ = "company_memberships"
    __table_args__ = (
        CheckConstraint(
            "membership_role IN ('OWNER', 'MEMBER')",
            name="ck_company_memberships_role",
        ),
        Index(
            "uq_company_memberships_active_company_user",
            "company_id",
            "user_id",
            unique=True,
            postgresql_where=text("revoked_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    membership_role: Mapped[str] = mapped_column(String(20), nullable=False)
    granted_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuthChallenge(Base):
    __tablename__ = "auth_challenges"
    __table_args__ = (
        CheckConstraint("length(challenge_hash) = 64", name="ck_auth_challenges_hash_length"),
        CheckConstraint("attempt_count >= 0", name="ck_auth_challenges_attempt_count"),
    )

    challenge_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class ParticipantSession(Base):
    __tablename__ = "participant_sessions"
    __table_args__ = (
        CheckConstraint("length(token_hash) = 64", name="ck_participant_sessions_hash_length"),
        CheckConstraint(
            "session_scope IN ('PARTICIPANT', 'ADMIN')",
            name="ck_participant_sessions_scope",
        ),
    )

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    auth_mode: Mapped[str] = mapped_column(String(12), nullable=False, default="REAL")
    session_scope: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PARTICIPANT"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class LearningEnrollment(Base):
    __tablename__ = "learning_enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", "course_version", name="uq_learning_enrollments_user_course_version"),
        CheckConstraint("status IN ('IN_PROGRESS', 'COMPLETED')", name="ck_learning_enrollments_status"),
        CheckConstraint("progress BETWEEN 0 AND 100", name="ck_learning_enrollments_progress"),
        CheckConstraint("attempt_count >= 0", name="ck_learning_enrollments_attempt_count"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    course_id: Mapped[str] = mapped_column(String(120), nullable=False)
    course_version: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="IN_PROGRESS")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        UniqueConstraint("enrollment_id", "attempt_number", name="uq_quiz_attempts_enrollment_number"),
        CheckConstraint("score BETWEEN 0 AND 100", name="ck_quiz_attempts_score"),
        CheckConstraint("length(answers_hash) = 64", name="ck_quiz_attempts_answers_hash"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    enrollment_id: Mapped[str] = mapped_column(ForeignKey("learning_enrollments.id", ondelete="RESTRICT"), nullable=False, index=True)
    module_id: Mapped[str] = mapped_column(String(120), nullable=False)
    assessment_version: Mapped[str] = mapped_column(String(40), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    answers_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SkillEvidence(Base):
    __tablename__ = "skill_evidence"
    __table_args__ = (
        UniqueConstraint("user_id", "module_id", "assessment_version", name="uq_skill_evidence_user_module_version"),
        UniqueConstraint("quiz_attempt_id", name="uq_skill_evidence_quiz_attempt"),
        CheckConstraint("score BETWEEN 80 AND 100", name="ck_skill_evidence_passing_score"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    module_id: Mapped[str] = mapped_column(String(120), nullable=False)
    assessment_version: Mapped[str] = mapped_column(String(40), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    quiz_attempt_id: Mapped[str] = mapped_column(ForeignKey("quiz_attempts.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class PaidTask(Base):
    __tablename__ = "paid_tasks"
    __table_args__ = (
        CheckConstraint("reward_sats > 0", name="ck_paid_tasks_positive_reward"),
        CheckConstraint("slots = 1", name="ck_paid_tasks_one_slot"),
        CheckConstraint("status IN ('DRAFT', 'PUBLISHED', 'CLOSED')", name="ck_paid_tasks_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    module_id: Mapped[str] = mapped_column(String(120), nullable=False)
    reward_sats: Mapped[int] = mapped_column(BigInteger, nullable=False)
    slots: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TaskFundingReservation(Base):
    __tablename__ = "task_funding_reservations"
    __table_args__ = (
        UniqueConstraint("task_id", name="uq_task_funding_reservations_task"),
        CheckConstraint("amount_sats > 0", name="ck_task_funding_reservations_positive_amount"),
        CheckConstraint("status = 'RESERVED'", name="ck_task_funding_reservations_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(
        ForeignKey("paid_tasks.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    amount_sats: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="RESERVED")
    ledger_transaction_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_transactions.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TaskFundingLine(Base):
    __tablename__ = "task_funding_lines"
    __table_args__ = (CheckConstraint("amount_sats > 0", name="ck_task_funding_lines_positive_amount"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    reservation_id: Mapped[str] = mapped_column(
        ForeignKey("task_funding_reservations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    account: Mapped[str] = mapped_column(String(120), nullable=False)
    amount_sats: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(36))


class Assignment(Base):
    __tablename__ = "assignments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('RESERVED', 'IN_PROGRESS', 'SUBMITTED', 'UNDER_REVIEW', "
            "'CHANGES_REQUESTED', 'RESUBMITTED', 'APPROVED', 'REJECTED', "
            "'PAYMENT_PENDING', 'PAYMENT_PROCESSING', 'PAYMENT_FAILED', 'PAID', 'EXPIRED')",
            name="ck_assignments_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(
        ForeignKey("paid_tasks.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="RESERVED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AssignmentReservation(Base):
    __tablename__ = "assignment_reservations"
    __table_args__ = (
        UniqueConstraint("assignment_id", name="uq_assignment_reservations_assignment"),
        CheckConstraint(
            "status IN ('ACTIVE', 'EXPIRED', 'CONSUMED')",
            name="ck_assignment_reservations_status",
        ),
        Index(
            "uq_assignment_reservations_one_active_per_task",
            "task_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    assignment_id: Mapped[str] = mapped_column(
        ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False
    )
    task_id: Mapped[str] = mapped_column(
        ForeignKey("paid_tasks.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    reserved_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StoredObject(Base):
    __tablename__ = "stored_objects"
    __table_args__ = (
        CheckConstraint("size_bytes BETWEEN 0 AND 10485760", name="ck_stored_objects_size"),
        CheckConstraint("length(content_hash) = 64", name="ck_stored_objects_hash_length"),
        CheckConstraint("private = true", name="ck_stored_objects_private"),
        CheckConstraint(
            "scan_status IN ('QUARANTINED', 'CLEAN', 'REJECTED')",
            name="ck_stored_objects_scan_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(80), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    scan_status: Mapped[str] = mapped_column(String(20), nullable=False, default="QUARANTINED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SubmissionDraft(Base):
    __tablename__ = "submission_drafts"
    __table_args__ = (
        UniqueConstraint("assignment_id", name="uq_submission_drafts_assignment"),
        CheckConstraint("private = true", name="ck_submission_drafts_private"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    assignment_id: Mapped[str] = mapped_column(
        ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    filename: Mapped[str] = mapped_column(String(255), nullable=False, default="submission.txt")
    mime_type: Mapped[str] = mapped_column(String(80), nullable=False, default="text/plain")
    private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint("assignment_id", "version", name="uq_submissions_assignment_version"),
        CheckConstraint("version > 0", name="ck_submissions_positive_version"),
        CheckConstraint("length(content_hash) = 64", name="ck_submissions_hash_length"),
        CheckConstraint("private = true", name="ck_submissions_private"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    assignment_id: Mapped[str] = mapped_column(
        ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    stored_object_id: Mapped[str | None] = mapped_column(
        ForeignKey("stored_objects.id", ondelete="RESTRICT")
    )
    private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("submission_id", name="uq_reviews_submission"),
        CheckConstraint(
            "decision IN ('APPROVE', 'REQUEST_CHANGES', 'REJECT')",
            name="ck_reviews_decision",
        ),
        CheckConstraint(
            "decision = 'APPROVE' OR length(trim(reason)) > 0",
            name="ck_reviews_reason_required",
        ),
        Index(
            "uq_reviews_one_correction_per_assignment",
            "assignment_id",
            unique=True,
            postgresql_where=text("decision = 'REQUEST_CHANGES'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    submission_id: Mapped[str] = mapped_column(
        ForeignKey("submissions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assignment_id: Mapped[str] = mapped_column(
        ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    reviewer_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    decision: Mapped[str] = mapped_column(String(24), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    previous_status: Mapped[str] = mapped_column(String(24), nullable=False)
    new_status: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class OpportunityListing(Base):
    __tablename__ = "opportunity_listings"
    __table_args__ = (
        CheckConstraint("status = 'PUBLISHED'", name="ck_opportunity_listings_status"),
        CheckConstraint(
            "external_url LIKE 'http://%' OR external_url LIKE 'https://%'",
            name="ck_opportunity_listings_http_scheme",
        ),
        CheckConstraint(
            "category IN ('HACKATHON', 'FREE_COURSE', 'EVENT', 'TALK', 'MEETUP', "
            "'MENTORSHIP', 'EDUCATIONAL_PROGRAM', 'OTHER')",
            name="ck_opportunity_listings_category",
        ),
        CheckConstraint("format IN ('ONLINE', 'ONSITE', 'HYBRID')", name="ck_opportunity_listings_format"),
        CheckConstraint("format = 'ONLINE' OR length(trim(location)) > 0", name="ck_opportunity_listings_location"),
        CheckConstraint("starts_at IS NOT NULL", name="ck_opportunity_listings_starts_at_required"),
        CheckConstraint("non_remunerated_ack IS TRUE", name="ck_opportunity_listings_non_remunerated"),
        CheckConstraint(
            "moderation_status IN ('VISIBLE', 'HIDDEN')",
            name="ck_opportunity_listings_moderation_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    author_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    organization_name: Mapped[str] = mapped_column(String(160), nullable=False)
    external_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    format: Mapped[str] = mapped_column(String(16), nullable=False, default="ONLINE")
    location: Mapped[str | None] = mapped_column(String(240))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    application_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    requirements: Mapped[str] = mapped_column(Text, nullable=False, default="")
    non_remunerated_ack: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    moderation_status: Mapped[str] = mapped_column(String(20), nullable=False, default="VISIBLE")
    idempotency_key: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PUBLISHED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CommunityPostReference(Base):
    __tablename__ = "community_post_references"
    __table_args__ = (
        CheckConstraint(
            "category IN ('learning', 'question', 'achievement')",
            name="ck_community_posts_category",
        ),
        CheckConstraint(
            "moderation_status IN ('VISIBLE', 'HIDDEN')",
            name="ck_community_posts_moderation_status",
        ),
        CheckConstraint(
            "relay_status IN ('LOCAL_ONLY', 'PUBLISHED')",
            name="ck_community_posts_relay_status",
        ),
        CheckConstraint(
            "mode IN ('SANDBOX', 'REAL')", name="ck_community_posts_mode"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    nostr_event_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    author_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(24), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    moderation_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="VISIBLE"
    )
    relay_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="LOCAL_ONLY"
    )
    mode: Mapped[str] = mapped_column(String(12), nullable=False, default="SANDBOX")
    idempotency_key: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ContentReport(Base):
    __tablename__ = "content_reports"
    __table_args__ = (
        UniqueConstraint(
            "post_reference_id", "reporter_user_id", name="uq_content_reports_reporter_post"
        ),
        CheckConstraint("status = 'OPEN'", name="ck_content_reports_status"),
        CheckConstraint("length(trim(reason)) > 0", name="ck_content_reports_reason"),
        CheckConstraint(
            "category IN ('SPAM', 'FRAUD', 'PERSONAL_DATA', 'HARASSMENT', "
            "'MISLEADING_CONTENT', 'MALICIOUS_LINK', 'OUT_OF_SCOPE', 'OTHER')",
            name="ck_content_reports_category",
        ),
        CheckConstraint("category <> 'OTHER' OR length(trim(details)) > 0", name="ck_content_reports_other_details"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    post_reference_id: Mapped[str | None] = mapped_column(
        ForeignKey("community_post_references.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    opportunity_listing_id: Mapped[str | None] = mapped_column(
        ForeignKey("opportunity_listings.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    reporter_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="OTHER")
    details: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ModerationDecision(Base):
    __tablename__ = "moderation_decisions"
    __table_args__ = (
        CheckConstraint("action IN ('HIDE', 'RESTORE', 'KEEP')", name="ck_moderation_decisions_action"),
        CheckConstraint("length(trim(reason)) > 0", name="ck_moderation_decisions_reason"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    post_reference_id: Mapped[str | None] = mapped_column(
        ForeignKey("community_post_references.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    opportunity_listing_id: Mapped[str | None] = mapped_column(
        ForeignKey("opportunity_listings.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    moderator_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    previous_status: Mapped[str] = mapped_column(String(20), nullable=False)
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LearningNote(Base):
    __tablename__ = "learning_notes"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", "lesson_id", name="uq_learning_notes_user_lesson"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    course_id: Mapped[str] = mapped_column(String(120), nullable=False)
    lesson_id: Mapped[str] = mapped_column(String(120), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LearningActivitySubmission(Base):
    __tablename__ = "learning_activity_submissions"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", "activity_id", name="uq_learning_activity_user_activity"),
        CheckConstraint("status = 'SUBMITTED'", name="ck_learning_activity_submitted"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    course_id: Mapped[str] = mapped_column(String(120), nullable=False)
    activity_id: Mapped[str] = mapped_column(String(120), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="SUBMITTED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BadgeDefinition(Base):
    __tablename__ = "badge_definitions"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    identifier: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    mode: Mapped[str] = mapped_column(String(12), nullable=False, default="SANDBOX")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class BadgeConsent(Base):
    __tablename__ = "badge_consents"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "skill_evidence_id",
            "badge_definition_id",
            name="uq_badge_consents_user_evidence_definition",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    skill_evidence_id: Mapped[str] = mapped_column(
        ForeignKey("skill_evidence.id", ondelete="RESTRICT"), nullable=False
    )
    badge_definition_id: Mapped[str] = mapped_column(
        ForeignKey("badge_definitions.id", ondelete="RESTRICT"), nullable=False
    )
    consented_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BadgePublication(Base):
    __tablename__ = "badge_publications"
    __table_args__ = (
        UniqueConstraint("consent_id", name="uq_badge_publications_consent"),
        CheckConstraint(
            "status IN ('PUBLISH_PENDING', 'PUBLISHED', 'FAILED')",
            name="ck_badge_publications_status",
        ),
        CheckConstraint("mode IN ('SANDBOX', 'REAL')", name="ck_badge_publications_mode"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    consent_id: Mapped[str] = mapped_column(
        ForeignKey("badge_consents.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PUBLISH_PENDING")
    mode: Mapped[str] = mapped_column(String(12), nullable=False, default="SANDBOX")
    nostr_event_id: Mapped[str | None] = mapped_column(String(64))
    relays: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    acknowledged_relays: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


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
    invoice_hash: Mapped[str | None] = mapped_column(String(64))
    invoice_network: Mapped[str | None] = mapped_column(String(20))
    invoice_amount_sats: Mapped[int | None] = mapped_column(BigInteger)
    invoice_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class ProviderPayment(Base):
    __tablename__ = "provider_payments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PROCESSING', 'AMBIGUOUS', 'SETTLED', 'FAILED')",
            name="ck_provider_payments_status",
        ),
        CheckConstraint(
            "mode IN ('MOCK', 'SANDBOX', 'REAL')",
            name="ck_provider_payments_mode",
        ),
        CheckConstraint(
            "payment_hash ~ '^[0-9a-f]{64}$'",
            name="ck_provider_payments_payment_hash",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    payout_attempt_id: Mapped[str] = mapped_column(
        ForeignKey("payout_attempts.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    payment_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(160))
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProviderEvent(Base):
    __tablename__ = "provider_events"
    __table_args__ = (
        UniqueConstraint(
            "provider", "provider_event_id", name="uq_provider_events_provider_event"
        ),
        CheckConstraint(
            "event_type IN ('AMBIGUOUS', 'SETTLED', 'FAILED')",
            name="ck_provider_events_type",
        ),
        CheckConstraint(
            "payload_hash ~ '^[0-9a-f]{64}$'",
            name="ck_provider_events_payload_hash",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_event_id: Mapped[str] = mapped_column(String(160), nullable=False)
    payout_attempt_id: Mapped[str] = mapped_column(
        ForeignKey("payout_attempts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PaymentReceipt(Base):
    __tablename__ = "payment_receipts"
    __table_args__ = (
        CheckConstraint("amount_sats > 0", name="ck_payment_receipts_positive_amount"),
        CheckConstraint("status = 'SETTLED'", name="ck_payment_receipts_status"),
        CheckConstraint(
            "mode IN ('MOCK', 'SANDBOX', 'REAL')",
            name="ck_payment_receipts_mode",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    payment_obligation_id: Mapped[str] = mapped_column(
        ForeignKey("payment_obligations.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    payout_attempt_id: Mapped[str] = mapped_column(
        ForeignKey("payout_attempts.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    ledger_transaction_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_transactions.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    receipt_number: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    assignment_id: Mapped[str] = mapped_column(String(36), nullable=False)
    amount_sats: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DonorProfile(Base):
    __tablename__ = "donor_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, unique=True, index=True
    )
    display_name: Mapped[str | None] = mapped_column(String(160))
    terms_version: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Contribution(Base):
    __tablename__ = "contributions"
    __table_args__ = (
        CheckConstraint("input_amount_sats > 0", name="ck_contributions_positive_amount"),
        CheckConstraint("input_currency = 'SAT'", name="ck_contributions_currency"),
        CheckConstraint(
            "status IN ('DRAFT', 'QUOTED', 'PENDING_PAYMENT', 'CONFIRMED', 'ALLOCATED', 'FAILED', 'CANCELLED')",
            name="ck_contributions_status",
        ),
        CheckConstraint(
            "mode IN ('MOCK', 'SANDBOX', 'REAL')", name="ck_contributions_mode"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    donor_profile_id: Mapped[str] = mapped_column(
        ForeignKey("donor_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    input_amount_sats: Mapped[int] = mapped_column(BigInteger, nullable=False)
    input_currency: Mapped[str] = mapped_column(String(12), nullable=False)
    terms_version: Mapped[str] = mapped_column(String(40), nullable=False)
    terms_accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ContributionAllocation(Base):
    __tablename__ = "contribution_allocations"
    __table_args__ = (
        UniqueConstraint(
            "contribution_id", "allocation_type", name="uq_contribution_allocations_type"
        ),
        CheckConstraint(
            "allocation_type IN ('IMPACT_FUND', 'LIQUIDITY_CAPITAL')",
            name="ck_contribution_allocations_type",
        ),
        CheckConstraint("amount_sats > 0", name="ck_contribution_allocations_amount"),
        CheckConstraint(
            "percentage_bps > 0 AND percentage_bps <= 10000",
            name="ck_contribution_allocations_percentage",
        ),
        CheckConstraint("status = 'ALLOCATED'", name="ck_contribution_allocations_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    contribution_id: Mapped[str] = mapped_column(
        ForeignKey("contributions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    allocation_type: Mapped[str] = mapped_column(String(24), nullable=False)
    amount_sats: Mapped[int] = mapped_column(BigInteger, nullable=False)
    percentage_bps: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ContributionReceipt(Base):
    __tablename__ = "contribution_receipts"
    __table_args__ = (
        CheckConstraint("total_sats > 0", name="ck_contribution_receipts_total"),
        CheckConstraint(
            "impact_sats >= 0 AND liquidity_sats >= 0 AND impact_sats + liquidity_sats = total_sats",
            name="ck_contribution_receipts_composition",
        ),
        CheckConstraint(
            "mode IN ('MOCK', 'SANDBOX', 'REAL')",
            name="ck_contribution_receipts_mode",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    contribution_id: Mapped[str] = mapped_column(
        ForeignKey("contributions.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    ledger_transaction_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_transactions.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    receipt_number: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    total_sats: Mapped[int] = mapped_column(BigInteger, nullable=False)
    impact_sats: Mapped[int] = mapped_column(BigInteger, nullable=False)
    liquidity_sats: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


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


class OnboardingIncomplete(ValueError):
    pass


class AssignmentUnavailable(RuntimeError):
    pass


class ReviewConflict(RuntimeError):
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

    def save_challenge(self, challenge_hash: str, expires_at: datetime) -> None:
        with self.sessions.begin() as session:
            session.add(AuthChallenge(challenge_hash=challenge_hash, expires_at=expires_at))

    def register_auth_attempt(
        self, challenge_hash: str, now: datetime, max_attempts: int
    ) -> bool:
        with self.sessions.begin() as session:
            registered = session.execute(
                update(AuthChallenge)
                .where(
                    AuthChallenge.challenge_hash == challenge_hash,
                    AuthChallenge.used_at.is_(None),
                    AuthChallenge.expires_at > now,
                    AuthChallenge.attempt_count < max_attempts,
                )
                .values(attempt_count=AuthChallenge.attempt_count + 1)
                .returning(AuthChallenge.challenge_hash)
            ).scalar_one_or_none()
        return registered is not None

    def consume_challenge_and_create_session(
        self,
        challenge_hash: str,
        now: datetime,
        token_hash: str,
        pubkey: str,
        session_expires_at: datetime,
        auth_mode: str,
        session_scope: str,
    ) -> bool:
        with self.sessions.begin() as session:
            consumed = session.execute(
                update(AuthChallenge)
                .where(
                    AuthChallenge.challenge_hash == challenge_hash,
                    AuthChallenge.used_at.is_(None),
                    AuthChallenge.expires_at > now,
                )
                .values(used_at=now)
                .returning(AuthChallenge.challenge_hash)
            ).scalar_one_or_none()
            if consumed is None:
                return False
            stored_user_id = self._ensure_user(session, pubkey)
            session.add(
                ParticipantSession(
                    token_hash=token_hash,
                    user_id=stored_user_id,
                    expires_at=session_expires_at,
                    auth_mode=auth_mode,
                    session_scope=session_scope,
                )
            )
        return True

    def create_session(
        self,
        token_hash: str,
        pubkey: str,
        session_expires_at: datetime,
        auth_mode: str,
        session_scope: str,
    ) -> None:
        with self.sessions.begin() as session:
            user_id = self._ensure_user(session, pubkey)
            session.add(
                ParticipantSession(
                    token_hash=token_hash,
                    user_id=user_id,
                    expires_at=session_expires_at,
                    auth_mode=auth_mode,
                    session_scope=session_scope,
                )
            )

    def get_session(
        self, token_hash: str, now: datetime, session_scope: str
    ) -> tuple[str, datetime, str] | None:
        with self.sessions() as session:
            row = session.execute(
                select(User.nostr_pubkey, ParticipantSession.expires_at, ParticipantSession.auth_mode)
                .join(ParticipantSession, ParticipantSession.user_id == User.id)
                .where(
                    ParticipantSession.token_hash == token_hash,
                    ParticipantSession.revoked_at.is_(None),
                    ParticipantSession.expires_at > now,
                    ParticipantSession.session_scope == session_scope,
                )
            ).one_or_none()
            return (row[0], row[1], row[2]) if row else None

    def revoke_session(self, token_hash: str, now: datetime, session_scope: str) -> None:
        with self.sessions.begin() as session:
            session.execute(
                update(ParticipantSession)
                .where(
                    ParticipantSession.token_hash == token_hash,
                    ParticipantSession.session_scope == session_scope,
                    ParticipantSession.revoked_at.is_(None),
                )
                .values(revoked_at=now)
            )

    def grant_role(
        self,
        pubkey: str,
        role: str,
        granted_by_pubkey: str | None = None,
    ) -> dict[str, Any]:
        normalized_pubkey = normalize_nostr_pubkey(pubkey)
        normalized_role = str(role).strip().upper()
        if normalized_role not in {
            "PARTICIPANT",
            "ORGANIZATION",
            "DONOR",
            "REVIEWER",
            "ADMIN",
        }:
            raise ValueError("invalid role")
        normalized_granter = (
            normalize_nostr_pubkey(granted_by_pubkey) if granted_by_pubkey else None
        )
        now = datetime.now(timezone.utc)
        with self.sessions.begin() as session:
            user_id = self._ensure_user(session, normalized_pubkey)
            granted_by_user_id = (
                self._ensure_user(session, normalized_granter)
                if normalized_granter
                else None
            )
            existing = session.scalar(
                select(UserRole).where(
                    UserRole.user_id == user_id,
                    UserRole.role == normalized_role,
                    UserRole.revoked_at.is_(None),
                )
            )
            if existing:
                return self._user_role_dict(existing, normalized_pubkey)
            grant = UserRole(
                id=str(uuid.uuid4()),
                user_id=user_id,
                role=normalized_role,
                granted_by_user_id=granted_by_user_id,
                granted_at=now,
            )
            session.add(grant)
            session.add(
                AuditEvent(
                    event_id=str(uuid.uuid4()),
                    actor_id=granted_by_user_id,
                    action="IDENTITY_ROLE_GRANTED",
                    aggregate_type="User",
                    aggregate_id=user_id,
                    occurred_at=now,
                    details={"role": normalized_role},
                )
            )
        return self._user_role_dict(grant, normalized_pubkey)

    def revoke_role(
        self,
        pubkey: str,
        role: str,
        revoked_by_pubkey: str | None = None,
    ) -> bool:
        normalized_pubkey = normalize_nostr_pubkey(pubkey)
        normalized_role = str(role).strip().upper()
        normalized_revoker = (
            normalize_nostr_pubkey(revoked_by_pubkey) if revoked_by_pubkey else None
        )
        now = datetime.now(timezone.utc)
        with self.sessions.begin() as session:
            row = session.execute(
                select(UserRole, User.id)
                .join(User, UserRole.user_id == User.id)
                .where(
                    User.nostr_pubkey == normalized_pubkey,
                    UserRole.role == normalized_role,
                    UserRole.revoked_at.is_(None),
                )
                .with_for_update()
            ).one_or_none()
            if not row:
                return False
            grant, user_id = row
            revoker_id = (
                self._ensure_user(session, normalized_revoker)
                if normalized_revoker
                else None
            )
            grant.revoked_at = now
            session.add(
                AuditEvent(
                    event_id=str(uuid.uuid4()),
                    actor_id=revoker_id,
                    action="IDENTITY_ROLE_REVOKED",
                    aggregate_type="User",
                    aggregate_id=user_id,
                    occurred_at=now,
                    details={"role": normalized_role},
                )
            )
        return True

    def roles_for_pubkey(self, pubkey: str) -> set[str]:
        normalized_pubkey = normalize_nostr_pubkey(pubkey)
        with self.sessions() as session:
            return set(
                session.scalars(
                    select(UserRole.role)
                    .join(User, UserRole.user_id == User.id)
                    .where(
                        User.nostr_pubkey == normalized_pubkey,
                        UserRole.revoked_at.is_(None),
                    )
                )
            )

    def has_any_role(self, pubkey: str, roles: Iterable[str]) -> bool:
        required = {str(role).strip().upper() for role in roles}
        return bool(self.roles_for_pubkey(pubkey) & required)

    def add_company_membership(
        self,
        pubkey: str,
        company_id: str,
        membership_role: str = "OWNER",
        granted_by_pubkey: str | None = None,
    ) -> dict[str, Any]:
        normalized_pubkey = normalize_nostr_pubkey(pubkey)
        normalized_role = str(membership_role).strip().upper()
        if normalized_role not in {"OWNER", "MEMBER"}:
            raise ValueError("invalid company membership role")
        normalized_granter = (
            normalize_nostr_pubkey(granted_by_pubkey) if granted_by_pubkey else None
        )
        now = datetime.now(timezone.utc)
        with self.sessions.begin() as session:
            if not session.get(Company, company_id):
                raise KeyError(company_id)
            user_id = self._ensure_user(session, normalized_pubkey)
            if not session.scalar(
                select(UserRole.id).where(
                    UserRole.user_id == user_id,
                    UserRole.role == "ORGANIZATION",
                    UserRole.revoked_at.is_(None),
                )
            ):
                raise ValueError("organization role is required")
            existing = session.scalar(
                select(CompanyMembership).where(
                    CompanyMembership.company_id == company_id,
                    CompanyMembership.user_id == user_id,
                    CompanyMembership.revoked_at.is_(None),
                )
            )
            if existing:
                return self._company_membership_dict(existing, normalized_pubkey)
            granted_by_user_id = (
                self._ensure_user(session, normalized_granter)
                if normalized_granter
                else None
            )
            membership = CompanyMembership(
                id=str(uuid.uuid4()),
                company_id=company_id,
                user_id=user_id,
                membership_role=normalized_role,
                granted_by_user_id=granted_by_user_id,
                created_at=now,
            )
            session.add(membership)
            session.add(
                AuditEvent(
                    event_id=str(uuid.uuid4()),
                    actor_id=granted_by_user_id,
                    action="COMPANY_MEMBERSHIP_GRANTED",
                    aggregate_type="Company",
                    aggregate_id=company_id,
                    occurred_at=now,
                    details={"membership_role": normalized_role, "user_id": user_id},
                )
            )
        return self._company_membership_dict(membership, normalized_pubkey)

    def has_company_membership(self, pubkey: str, company_id: str) -> bool:
        normalized_pubkey = normalize_nostr_pubkey(pubkey)
        with self.sessions() as session:
            return (
                session.scalar(
                    select(CompanyMembership.id)
                    .join(User, CompanyMembership.user_id == User.id)
                    .where(
                        User.nostr_pubkey == normalized_pubkey,
                        CompanyMembership.company_id == company_id,
                        CompanyMembership.revoked_at.is_(None),
                    )
                )
                is not None
            )

    def create_onboarding_draft(self, pubkey: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with self.sessions.begin() as session:
            user_id = session.scalar(
                select(User.id).where(User.nostr_pubkey == pubkey).with_for_update()
            )
            if not user_id:
                raise KeyError(pubkey)
            existing = session.scalar(
                select(OnboardingDraft).where(
                    OnboardingDraft.user_id == user_id,
                    OnboardingDraft.status == "IN_PROGRESS",
                )
            )
            if existing:
                return self._onboarding_dict(existing)
            draft = OnboardingDraft(
                id=str(uuid.uuid4()),
                user_id=user_id,
                status="IN_PROGRESS",
                data={},
                created_at=now,
                updated_at=now,
            )
            session.add(draft)
        return self._onboarding_dict(draft)

    def get_onboarding_draft(self, draft_id: str, pubkey: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            draft = session.scalar(
                select(OnboardingDraft)
                .join(User, OnboardingDraft.user_id == User.id)
                .where(OnboardingDraft.id == draft_id, User.nostr_pubkey == pubkey)
            )
            return self._onboarding_dict(draft) if draft else None

    def has_completed_onboarding(self, pubkey: str) -> bool:
        normalized_pubkey = normalize_nostr_pubkey(pubkey)
        with self.sessions() as session:
            return (
                session.scalar(
                    select(OnboardingDraft.id)
                    .join(User, OnboardingDraft.user_id == User.id)
                    .where(
                        User.nostr_pubkey == normalized_pubkey,
                        OnboardingDraft.status == "COMPLETED",
                    )
                    .limit(1)
                )
                is not None
            )

    def update_onboarding_draft(self, draft_id: str, pubkey: str, fields: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with self.sessions.begin() as session:
            draft = session.scalar(
                select(OnboardingDraft)
                .join(User, OnboardingDraft.user_id == User.id)
                .where(OnboardingDraft.id == draft_id, User.nostr_pubkey == pubkey)
                .with_for_update()
            )
            if not draft:
                raise KeyError(draft_id)
            if draft.status != "IN_PROGRESS":
                raise ValueError("completed onboarding cannot be changed")
            draft.data = {**draft.data, **fields}
            draft.updated_at = now
        return self._onboarding_dict(draft)

    def complete_onboarding_draft(
        self, draft_id: str, pubkey: str, required: Iterable[str]
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with self.sessions.begin() as session:
            draft = session.scalar(
                select(OnboardingDraft)
                .join(User, OnboardingDraft.user_id == User.id)
                .where(OnboardingDraft.id == draft_id, User.nostr_pubkey == pubkey)
                .with_for_update()
            )
            if not draft:
                raise KeyError(draft_id)
            if draft.status == "COMPLETED":
                return self._onboarding_dict(draft)
            if any(not draft.data.get(key) for key in required):
                raise OnboardingIncomplete("required onboarding data is missing")
            draft.status = "COMPLETED"
            draft.completed_at = now
            draft.updated_at = now
            session.add(
                OutboxEvent(
                    event_id=str(uuid.uuid4()),
                    event_type="OnboardingCompleted",
                    version=1,
                    aggregate_id=draft.id,
                    occurred_at=now,
                    payload={"onboarding_draft_id": draft.id},
                    attempts=0,
                )
            )
            session.add(
                AuditEvent(
                    event_id=str(uuid.uuid4()),
                    actor_id=draft.user_id,
                    action="ONBOARDING_COMPLETED",
                    aggregate_type="OnboardingDraft",
                    aggregate_id=draft.id,
                    occurred_at=now,
                    details={"status": "COMPLETED"},
                )
            )
        return self._onboarding_dict(draft)

    def enroll_learning(self, pubkey: str, course_id: str, course_version: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with self.sessions.begin() as session:
            user_id = session.scalar(select(User.id).where(User.nostr_pubkey == pubkey))
            if not user_id:
                raise KeyError(pubkey)
            session.execute(
                pg_insert(LearningEnrollment)
                .values(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    course_id=course_id,
                    course_version=course_version,
                    status="IN_PROGRESS",
                    progress=0,
                    attempt_count=0,
                    started_at=now,
                )
                .on_conflict_do_nothing(
                    constraint="uq_learning_enrollments_user_course_version"
                )
            )
            enrollment = session.scalar(
                select(LearningEnrollment).where(
                    LearningEnrollment.user_id == user_id,
                    LearningEnrollment.course_id == course_id,
                    LearningEnrollment.course_version == course_version,
                )
            )
        return self._learning_enrollment_dict(enrollment)

    def list_learning_enrollments(self, pubkey: str) -> list[dict[str, Any]]:
        with self.sessions() as session:
            enrollments = list(
                session.scalars(
                    select(LearningEnrollment)
                    .join(User, LearningEnrollment.user_id == User.id)
                    .where(User.nostr_pubkey == pubkey)
                    .order_by(LearningEnrollment.started_at, LearningEnrollment.id)
                )
            )
        return [self._learning_enrollment_dict(enrollment) for enrollment in enrollments]

    def record_quiz_attempt(
        self,
        pubkey: str,
        course_id: str,
        course_version: str,
        module_id: str,
        assessment_version: str,
        score: int,
        answers_hash: str,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
            raise ValueError("score must be between 0 and 100")
        now = datetime.now(timezone.utc)
        with self.sessions.begin() as session:
            user_id = session.scalar(select(User.id).where(User.nostr_pubkey == pubkey))
            if not user_id:
                raise KeyError(pubkey)
            session.execute(
                pg_insert(LearningEnrollment)
                .values(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    course_id=course_id,
                    course_version=course_version,
                    status="IN_PROGRESS",
                    progress=0,
                    attempt_count=0,
                    started_at=now,
                )
                .on_conflict_do_nothing(
                    constraint="uq_learning_enrollments_user_course_version"
                )
            )
            enrollment = session.scalar(
                select(LearningEnrollment)
                .where(
                    LearningEnrollment.user_id == user_id,
                    LearningEnrollment.course_id == course_id,
                    LearningEnrollment.course_version == course_version,
                )
                .with_for_update()
            )
            enrollment.attempt_count += 1
            enrollment.progress = 100 if score >= 80 else max(enrollment.progress, 50)
            if score >= 80:
                enrollment.status = "COMPLETED"
                enrollment.completed_at = enrollment.completed_at or now
            attempt = QuizAttempt(
                id=str(uuid.uuid4()),
                enrollment_id=enrollment.id,
                module_id=module_id,
                assessment_version=assessment_version,
                score=score,
                attempt_number=enrollment.attempt_count,
                answers_hash=answers_hash,
                created_at=now,
            )
            session.add(attempt)
            session.flush()
            evidence_id = None
            if score >= 80:
                evidence_id = session.execute(
                    pg_insert(SkillEvidence)
                    .values(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        module_id=module_id,
                        assessment_version=assessment_version,
                        score=score,
                        quiz_attempt_id=attempt.id,
                        created_at=now,
                    )
                    .on_conflict_do_nothing(
                        constraint="uq_skill_evidence_user_module_version"
                    )
                    .returning(SkillEvidence.id)
                ).scalar_one_or_none()
                if evidence_id:
                    session.add_all(
                        [
                            OutboxEvent(
                                event_id=str(uuid.uuid4()),
                                event_type="QuizPassed",
                                version=1,
                                aggregate_id=attempt.id,
                                occurred_at=now,
                                payload={
                                    "module_id": module_id,
                                    "assessment_version": assessment_version,
                                    "score": score,
                                },
                                attempts=0,
                            ),
                            OutboxEvent(
                                event_id=str(uuid.uuid4()),
                                event_type="SkillEvidenceCreated",
                                version=1,
                                aggregate_id=evidence_id,
                                occurred_at=now,
                                payload={
                                    "module_id": module_id,
                                    "assessment_version": assessment_version,
                                },
                                attempts=0,
                            ),
                        ]
                    )
            evidence = session.scalar(
                select(SkillEvidence).where(
                    SkillEvidence.user_id == user_id,
                    SkillEvidence.module_id == module_id,
                    SkillEvidence.assessment_version == assessment_version,
                )
            )
        return self._quiz_attempt_dict(attempt), self._skill_evidence_dict(evidence) if evidence else None

    def list_skill_evidence(self, pubkey: str) -> list[dict[str, Any]]:
        with self.sessions() as session:
            evidence = list(
                session.scalars(
                    select(SkillEvidence)
                    .join(User, SkillEvidence.user_id == User.id)
                    .where(User.nostr_pubkey == pubkey)
                    .order_by(SkillEvidence.created_at, SkillEvidence.id)
                )
            )
        return [self._skill_evidence_dict(item) for item in evidence]

    def save_learning_note(
        self, pubkey: str, course_id: str, lesson_id: str, content: str
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with self.sessions.begin() as session:
            user_id = session.scalar(select(User.id).where(User.nostr_pubkey == pubkey))
            if not user_id:
                raise KeyError(pubkey)
            session.execute(
                pg_insert(LearningNote)
                .values(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    course_id=course_id,
                    lesson_id=lesson_id,
                    content=content,
                    updated_at=now,
                )
                .on_conflict_do_update(
                    constraint="uq_learning_notes_user_lesson",
                    set_={"content": content, "updated_at": now},
                )
            )
            note = session.scalar(
                select(LearningNote).where(
                    LearningNote.user_id == user_id,
                    LearningNote.course_id == course_id,
                    LearningNote.lesson_id == lesson_id,
                )
            )
        return self._learning_note_dict(note)

    def get_learning_note(self, pubkey: str, course_id: str, lesson_id: str) -> dict[str, Any]:
        with self.sessions() as session:
            note = session.scalar(
                select(LearningNote)
                .join(User, LearningNote.user_id == User.id)
                .where(
                    User.nostr_pubkey == pubkey,
                    LearningNote.course_id == course_id,
                    LearningNote.lesson_id == lesson_id,
                )
            )
        return self._learning_note_dict(note) if note else {"content": ""}

    def submit_learning_activity(
        self, pubkey: str, course_id: str, activity_id: str, content: str
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with self.sessions.begin() as session:
            user_id = session.scalar(select(User.id).where(User.nostr_pubkey == pubkey))
            if not user_id:
                raise KeyError(pubkey)
            submission_id = session.execute(
                pg_insert(LearningActivitySubmission)
                .values(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    course_id=course_id,
                    activity_id=activity_id,
                    content=content,
                    status="SUBMITTED",
                    created_at=now,
                )
                .on_conflict_do_nothing(
                    constraint="uq_learning_activity_user_activity"
                )
                .returning(LearningActivitySubmission.id)
            ).scalar_one_or_none()
            if not submission_id:
                raise ValueError("activity already submitted")
            submission = session.get(LearningActivitySubmission, submission_id)
        return self._learning_activity_dict(submission)

    def consent_badge_publication(
        self, pubkey: str, evidence_id: str, badge_definition: dict
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with self.sessions.begin() as session:
            user_id = session.scalar(select(User.id).where(User.nostr_pubkey == pubkey))
            evidence = session.scalar(
                select(SkillEvidence).where(
                    SkillEvidence.id == evidence_id,
                    SkillEvidence.user_id == user_id,
                )
            )
            if not user_id or not evidence:
                raise ValueError("skill evidence not found")
            session.execute(
                pg_insert(BadgeDefinition)
                .values(
                    id=badge_definition["id"],
                    identifier=badge_definition["identifier"],
                    name=badge_definition["name"],
                    description=badge_definition["description"],
                    mode="SANDBOX",
                    created_at=now,
                )
                .on_conflict_do_nothing(index_elements=[BadgeDefinition.id])
            )
            consent_id = session.execute(
                pg_insert(BadgeConsent)
                .values(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    skill_evidence_id=evidence_id,
                    badge_definition_id=badge_definition["id"],
                    consented_at=now,
                )
                .on_conflict_do_nothing(
                    constraint="uq_badge_consents_user_evidence_definition"
                )
                .returning(BadgeConsent.id)
            ).scalar_one_or_none()
            if consent_id is None:
                consent_id = session.scalar(
                    select(BadgeConsent.id).where(
                        BadgeConsent.user_id == user_id,
                        BadgeConsent.skill_evidence_id == evidence_id,
                        BadgeConsent.badge_definition_id == badge_definition["id"],
                    )
                )
            publication_id = session.execute(
                pg_insert(BadgePublication)
                .values(
                    id=str(uuid.uuid4()),
                    consent_id=consent_id,
                    status="PUBLISH_PENDING",
                    mode="SANDBOX",
                    nostr_event_id=None,
                    relays=[],
                    acknowledged_relays=[],
                    requested_at=now,
                )
                .on_conflict_do_nothing(constraint="uq_badge_publications_consent")
                .returning(BadgePublication.id)
            ).scalar_one_or_none()
            if publication_id:
                session.add(
                    OutboxEvent(
                        event_id=str(uuid.uuid4()),
                        event_type="BadgePublicationRequested",
                        version=1,
                        aggregate_id=publication_id,
                        occurred_at=now,
                        payload={
                            "badge_definition_id": badge_definition["id"],
                            "skill_evidence_id": evidence_id,
                            "mode": "SANDBOX",
                        },
                        attempts=0,
                    )
                )
            publication = session.scalar(
                select(BadgePublication).where(BadgePublication.consent_id == consent_id)
            )
        return self._badge_publication_dict(
            publication, evidence_id, badge_definition["id"]
        )

    def get_badge_publication(
        self, pubkey: str, evidence_id: str
    ) -> dict[str, Any] | None:
        with self.sessions() as session:
            row = session.execute(
                select(BadgePublication, BadgeConsent.badge_definition_id)
                .join(BadgeConsent, BadgePublication.consent_id == BadgeConsent.id)
                .join(User, BadgeConsent.user_id == User.id)
                .where(
                    User.nostr_pubkey == pubkey,
                    BadgeConsent.skill_evidence_id == evidence_id,
                )
            ).one_or_none()
        return (
            self._badge_publication_dict(row[0], evidence_id, row[1]) if row else None
        )

    def claim_outbox(
        self,
        worker_id: str,
        limit: int = 20,
        lease_seconds: int = 60,
    ) -> list[dict[str, Any]]:
        if not worker_id or len(worker_id) > 120:
            raise ValueError("worker_id must contain at most 120 characters")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        if isinstance(lease_seconds, bool) or not isinstance(lease_seconds, int) or lease_seconds <= 0:
            raise ValueError("lease_seconds must be a positive integer")
        now = datetime.now(timezone.utc)
        stale_before = now - timedelta(seconds=lease_seconds)
        with self.sessions.begin() as session:
            events = list(
                session.scalars(
                    select(OutboxEvent)
                    .where(
                        OutboxEvent.published_at.is_(None),
                        or_(OutboxEvent.claimed_at.is_(None), OutboxEvent.claimed_at < stale_before),
                    )
                    .order_by(OutboxEvent.occurred_at, OutboxEvent.event_id)
                    .with_for_update(skip_locked=True)
                    .limit(limit)
                )
            )
            for event in events:
                event.claimed_at = now
                event.claimed_by = worker_id
                event.attempts += 1
        return [self._outbox_dict(event) for event in events]

    def mark_outbox_published(self, event_id: str, worker_id: str) -> bool:
        now = datetime.now(timezone.utc)
        with self.sessions.begin() as session:
            result = session.execute(
                update(OutboxEvent)
                .where(
                    OutboxEvent.event_id == event_id,
                    OutboxEvent.claimed_by == worker_id,
                    OutboxEvent.published_at.is_(None),
                )
                .values(published_at=now, claimed_at=None, claimed_by=None, last_error=None)
            )
            return result.rowcount == 1

    def release_outbox(self, event_id: str, worker_id: str, error_code: str) -> bool:
        safe_error = error_code[:240]
        with self.sessions.begin() as session:
            result = session.execute(
                update(OutboxEvent)
                .where(
                    OutboxEvent.event_id == event_id,
                    OutboxEvent.claimed_by == worker_id,
                    OutboxEvent.published_at.is_(None),
                )
                .values(claimed_at=None, claimed_by=None, last_error=safe_error)
            )
            return result.rowcount == 1

    def receive_inbox(self, provider: str, provider_event_id: str, payload: dict[str, Any]) -> bool:
        now = datetime.now(timezone.utc)
        with self.sessions.begin() as session:
            inserted = session.execute(
                pg_insert(InboxEvent)
                .values(
                    provider=provider,
                    provider_event_id=provider_event_id,
                    received_at=now,
                    payload=payload,
                )
                .on_conflict_do_nothing(index_elements=[InboxEvent.provider_event_id])
                .returning(InboxEvent.provider_event_id)
            ).scalar_one_or_none()
            return inserted is not None

    def mark_inbox_processed(self, provider_event_id: str) -> bool:
        with self.sessions.begin() as session:
            result = session.execute(
                update(InboxEvent)
                .where(InboxEvent.provider_event_id == provider_event_id, InboxEvent.processed_at.is_(None))
                .values(processed_at=datetime.now(timezone.utc))
            )
            return result.rowcount == 1

    def append_audit(
        self,
        action: str,
        aggregate_type: str,
        aggregate_id: str,
        details: dict[str, Any],
        actor_id: str | None = None,
    ) -> str:
        event_id = str(uuid.uuid4())
        with self.sessions.begin() as session:
            session.add(
                AuditEvent(
                    event_id=event_id,
                    actor_id=actor_id,
                    action=action,
                    aggregate_type=aggregate_type,
                    aggregate_id=aggregate_id,
                    occurred_at=datetime.now(timezone.utc),
                    details=details,
                )
            )
        return event_id

    def create_company(self, name: str, description: str = "") -> dict[str, Any]:
        normalized_name = str(name).strip()
        if not normalized_name:
            raise ValueError("company name is required")
        company = Company(
            id=str(uuid.uuid4()),
            name=normalized_name,
            description=str(description).strip(),
            created_at=datetime.now(timezone.utc),
        )
        with self.sessions.begin() as session:
            session.add(company)
        return self._company_dict(company)

    def get_company(self, company_id: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            company = session.get(Company, company_id)
            return self._company_dict(company) if company else None

    def create_paid_task(
        self,
        company_id: str,
        title: str,
        instructions: str,
        reward_sats: int,
        module_id: str,
    ) -> dict[str, Any]:
        if isinstance(reward_sats, bool) or not isinstance(reward_sats, int) or reward_sats <= 0:
            raise ValueError("reward_sats must be a positive integer")
        normalized_title = str(title).strip()
        if not normalized_title:
            raise ValueError("task title is required")
        now = datetime.now(timezone.utc)
        task = PaidTask(
            id=str(uuid.uuid4()),
            company_id=company_id,
            title=normalized_title,
            instructions=str(instructions),
            module_id=str(module_id),
            reward_sats=reward_sats,
            slots=1,
            status="DRAFT",
            created_at=now,
        )
        with self.sessions.begin() as session:
            if not session.get(Company, company_id):
                raise KeyError(company_id)
            session.add(task)
        return self._paid_task_dict(task, 0)

    def reserve_task_funding(
        self,
        task_id: str,
        amount_sats: int,
        sources: Iterable[dict[str, Any]] | None = None,
        mode: str = "SANDBOX",
    ) -> dict[str, Any]:
        allowed_accounts = {"COMPANY_FUNDS", "MATCHING_POOL", "BONUS_REALIZED"}
        normalized_sources = list(sources or [{"account": "COMPANY_FUNDS", "amount_sats": amount_sats}])
        if not normalized_sources:
            raise ValueError("at least one funding source is required")
        for source in normalized_sources:
            if source.get("account") not in allowed_accounts:
                raise ValueError("invalid funding source account")
            value = source.get("amount_sats")
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError("funding source amounts must be positive integers")
        if sum(source["amount_sats"] for source in normalized_sources) != amount_sats:
            raise ValueError("funding source composition must equal amount_sats")
        now = datetime.now(timezone.utc)
        reservation_id = str(uuid.uuid4())
        transaction_id = str(uuid.uuid4())
        try:
            with self.sessions.begin() as session:
                task = session.scalar(
                    select(PaidTask).where(PaidTask.id == task_id).with_for_update()
                )
                if not task:
                    raise KeyError(task_id)
                if task.status != "DRAFT" or amount_sats != task.reward_sats:
                    raise ValueError("funding must fully cover a draft task")
                if session.scalar(
                    select(TaskFundingReservation.id).where(TaskFundingReservation.task_id == task_id)
                ):
                    raise AssignmentUnavailable("task funding is already reserved")
                session.add(
                    LedgerTransaction(
                        id=transaction_id,
                        event_type="TASK_FUNDED",
                        reference_id=f"task-funding:{task_id}",
                        mode=mode,
                        occurred_at=now,
                    )
                )
                session.flush()
                for source in normalized_sources:
                    session.add(
                        LedgerEntry(
                            id=str(uuid.uuid4()),
                            transaction_id=transaction_id,
                            account=source["account"],
                            direction="DEBIT",
                            amount_sats=source["amount_sats"],
                            source_id=source.get("source_id"),
                        )
                    )
                session.add(
                    LedgerEntry(
                        id=str(uuid.uuid4()),
                        transaction_id=transaction_id,
                        account="TASK_RESERVED",
                        direction="CREDIT",
                        amount_sats=amount_sats,
                        source_id=task_id,
                    )
                )
                reservation = TaskFundingReservation(
                    id=reservation_id,
                    task_id=task_id,
                    amount_sats=amount_sats,
                    status="RESERVED",
                    ledger_transaction_id=transaction_id,
                    created_at=now,
                )
                session.add(reservation)
                session.flush()
                session.add_all(
                    TaskFundingLine(
                        id=str(uuid.uuid4()),
                        reservation_id=reservation_id,
                        account=source["account"],
                        amount_sats=source["amount_sats"],
                        source_id=source.get("source_id"),
                    )
                    for source in normalized_sources
                )
                session.add(
                    OutboxEvent(
                        event_id=str(uuid.uuid4()),
                        event_type="TaskFunded",
                        version=1,
                        aggregate_id=task_id,
                        occurred_at=now,
                        payload={"task_id": task_id, "amount_sats": amount_sats, "mode": mode},
                        attempts=0,
                    )
                )
        except IntegrityError as error:
            raise AssignmentUnavailable("task funding is already reserved") from error
        return {
            "id": reservation_id,
            "task_id": task_id,
            "amount_sats": amount_sats,
            "status": "RESERVED",
            "ledger_transaction_id": transaction_id,
            "sources": normalized_sources,
            "mode": mode,
        }

    def publish_paid_task(self, task_id: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with self.sessions.begin() as session:
            task = session.scalar(select(PaidTask).where(PaidTask.id == task_id).with_for_update())
            if not task:
                raise KeyError(task_id)
            funding = session.scalar(
                select(TaskFundingReservation).where(
                    TaskFundingReservation.task_id == task_id,
                    TaskFundingReservation.status == "RESERVED",
                )
            )
            if not funding or funding.amount_sats != task.reward_sats:
                raise ValueError("task must be fully funded")
            if task.status == "PUBLISHED":
                return self._paid_task_dict(task, funding.amount_sats)
            if task.status != "DRAFT":
                raise ValueError("task cannot be published")
            task.status = "PUBLISHED"
            task.published_at = now
            session.add(
                OutboxEvent(
                    event_id=str(uuid.uuid4()),
                    event_type="PaidTaskPublished",
                    version=1,
                    aggregate_id=task_id,
                    occurred_at=now,
                    payload={"task_id": task_id},
                    attempts=0,
                )
            )
        return self._paid_task_dict(task, funding.amount_sats)

    def get_paid_task(self, task_id: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            row = session.execute(
                select(PaidTask, TaskFundingReservation.amount_sats)
                .outerjoin(TaskFundingReservation, TaskFundingReservation.task_id == PaidTask.id)
                .where(PaidTask.id == task_id)
            ).one_or_none()
            return self._paid_task_dict(row[0], row[1] or 0) if row else None

    def list_paid_tasks(self, pubkey: str | None = None, eligible_only: bool = False) -> list[dict[str, Any]]:
        with self.sessions() as session:
            rows = list(
                session.execute(
                    select(PaidTask, TaskFundingReservation.amount_sats)
                    .join(TaskFundingReservation, TaskFundingReservation.task_id == PaidTask.id)
                    .where(PaidTask.status == "PUBLISHED")
                    .order_by(PaidTask.published_at, PaidTask.id)
                )
            )
            evidence_modules: set[str] = set()
            if pubkey:
                evidence_modules = set(
                    session.scalars(
                        select(SkillEvidence.module_id)
                        .join(User, SkillEvidence.user_id == User.id)
                        .where(User.nostr_pubkey == pubkey)
                    )
                )
        items = []
        for task, funded_sats in rows:
            eligible = task.module_id in evidence_modules
            if eligible_only and not eligible:
                continue
            items.append({**self._paid_task_dict(task, funded_sats), "eligible": eligible})
        return items

    def reserve_assignment(self, task_id: str, pubkey: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        reserved_until = now + timedelta(minutes=60)
        assignment_id = str(uuid.uuid4())
        reservation_id = str(uuid.uuid4())
        try:
            with self.sessions.begin() as session:
                task = session.scalar(select(PaidTask).where(PaidTask.id == task_id).with_for_update())
                if not task or task.status != "PUBLISHED":
                    raise ValueError("task unavailable")
                user_id = session.scalar(select(User.id).where(User.nostr_pubkey == pubkey))
                if not user_id or not session.scalar(
                    select(SkillEvidence.id).where(
                        SkillEvidence.user_id == user_id,
                        SkillEvidence.module_id == task.module_id,
                    ).limit(1)
                ):
                    raise ValueError("participant ineligible")
                active = session.scalar(
                    select(AssignmentReservation)
                    .where(
                        AssignmentReservation.task_id == task_id,
                        AssignmentReservation.status == "ACTIVE",
                    )
                    .with_for_update()
                )
                if active and active.reserved_until <= now:
                    active.status = "EXPIRED"
                    active.expired_at = now
                    expired_assignment = session.get(Assignment, active.assignment_id)
                    expired_assignment.status = "EXPIRED"
                    session.add(
                        OutboxEvent(
                            event_id=str(uuid.uuid4()),
                            event_type="AssignmentExpired",
                            version=1,
                            aggregate_id=active.assignment_id,
                            occurred_at=now,
                            payload={"assignment_id": active.assignment_id, "task_id": task_id},
                            attempts=0,
                        )
                    )
                    active = None
                if active:
                    raise AssignmentUnavailable("task already reserved")
                assignment = Assignment(
                    id=assignment_id,
                    task_id=task_id,
                    user_id=user_id,
                    status="RESERVED",
                    created_at=now,
                )
                reservation = AssignmentReservation(
                    id=reservation_id,
                    assignment_id=assignment_id,
                    task_id=task_id,
                    status="ACTIVE",
                    reserved_until=reserved_until,
                    created_at=now,
                )
                session.add_all([assignment, reservation])
                session.add(
                    OutboxEvent(
                        event_id=str(uuid.uuid4()),
                        event_type="AssignmentReserved",
                        version=1,
                        aggregate_id=assignment_id,
                        occurred_at=now,
                        payload={
                            "assignment_id": assignment_id,
                            "task_id": task_id,
                            "reserved_until": reserved_until.isoformat(),
                        },
                        attempts=0,
                    )
                )
        except IntegrityError as error:
            raise AssignmentUnavailable("task already reserved") from error
        return {
            "id": assignment_id,
            "task_id": task_id,
            "pubkey": pubkey,
            "status": "RESERVED",
            "reservation_id": reservation_id,
            "reserved_until": reserved_until.isoformat(),
        }

    def expire_assignment_reservations(self, now: datetime | None = None, limit: int = 100) -> int:
        current = now or datetime.now(timezone.utc)
        with self.sessions.begin() as session:
            reservations = list(
                session.scalars(
                    select(AssignmentReservation)
                    .where(
                        AssignmentReservation.status == "ACTIVE",
                        AssignmentReservation.reserved_until <= current,
                    )
                    .with_for_update(skip_locked=True)
                    .limit(limit)
                )
            )
            for reservation in reservations:
                reservation.status = "EXPIRED"
                reservation.expired_at = current
                assignment = session.get(Assignment, reservation.assignment_id)
                assignment.status = "EXPIRED"
                session.add(
                    OutboxEvent(
                        event_id=str(uuid.uuid4()),
                        event_type="AssignmentExpired",
                        version=1,
                        aggregate_id=assignment.id,
                        occurred_at=current,
                        payload={"assignment_id": assignment.id, "task_id": reservation.task_id},
                        attempts=0,
                    )
                )
        return len(reservations)

    def get_assignment(self, assignment_id: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            row = session.execute(
                select(Assignment, AssignmentReservation, User.nostr_pubkey)
                .join(AssignmentReservation, AssignmentReservation.assignment_id == Assignment.id)
                .join(User, Assignment.user_id == User.id)
                .where(Assignment.id == assignment_id)
            ).one_or_none()
        return self._assignment_dict(*row) if row else None

    def create_stored_object(
        self,
        pubkey: str,
        filename: str,
        mime_type: str,
        size_bytes: int,
        content_hash: str,
    ) -> dict[str, Any]:
        allowed_mime = {"image/png", "image/jpeg", "application/pdf", "video/mp4"}
        if mime_type not in allowed_mime:
            raise ValueError("unsupported upload type")
        if isinstance(size_bytes, bool) or not isinstance(size_bytes, int) or not 0 <= size_bytes <= 10 * 1024 * 1024:
            raise ValueError("upload exceeds 10 MB")
        normalized_hash = str(content_hash).lower()
        if len(normalized_hash) != 64 or any(character not in "0123456789abcdef" for character in normalized_hash):
            raise ValueError("a SHA-256 content_hash is required")
        now = datetime.now(timezone.utc)
        stored = StoredObject(
            id=str(uuid.uuid4()),
            owner_user_id="",
            storage_key=f"quarantine/{uuid.uuid4()}",
            filename=str(filename),
            mime_type=mime_type,
            size_bytes=size_bytes,
            content_hash=normalized_hash,
            private=True,
            scan_status="QUARANTINED",
            created_at=now,
        )
        with self.sessions.begin() as session:
            user_id = session.scalar(select(User.id).where(User.nostr_pubkey == pubkey))
            if not user_id:
                raise KeyError(pubkey)
            stored.owner_user_id = user_id
            session.add(stored)
        return self._stored_object_dict(stored)

    def mark_stored_object_scanned(self, object_id: str, clean: bool) -> dict[str, Any]:
        with self.sessions.begin() as session:
            stored = session.scalar(
                select(StoredObject).where(StoredObject.id == object_id).with_for_update()
            )
            if not stored:
                raise KeyError(object_id)
            if stored.scan_status != "QUARANTINED":
                raise ValueError("object was already scanned")
            stored.scan_status = "CLEAN" if clean else "REJECTED"
        return self._stored_object_dict(stored)

    def save_submission_draft(
        self,
        assignment_id: str,
        pubkey: str,
        content: str,
        filename: str,
        mime_type: str,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        expired = False
        draft = None
        with self.sessions.begin() as session:
            assignment = session.scalar(
                select(Assignment)
                .join(User, Assignment.user_id == User.id)
                .where(Assignment.id == assignment_id, User.nostr_pubkey == pubkey)
                .with_for_update()
            )
            if not assignment:
                raise ValueError("assignment not owned by participant")
            reservation = session.scalar(
                select(AssignmentReservation).where(
                    AssignmentReservation.assignment_id == assignment_id
                ).with_for_update()
            )
            if assignment.status != "RESERVED" or reservation.status != "ACTIVE":
                raise ValueError("assignment does not accept drafts")
            if reservation.reserved_until <= now:
                reservation.status = "EXPIRED"
                reservation.expired_at = now
                assignment.status = "EXPIRED"
                session.add(
                    OutboxEvent(
                        event_id=str(uuid.uuid4()),
                        event_type="AssignmentExpired",
                        version=1,
                        aggregate_id=assignment_id,
                        occurred_at=now,
                        payload={"assignment_id": assignment_id, "task_id": assignment.task_id},
                        attempts=0,
                    )
                )
                expired = True
            else:
                session.execute(
                    pg_insert(SubmissionDraft)
                    .values(
                        id=str(uuid.uuid4()),
                        assignment_id=assignment_id,
                        content=str(content),
                        filename=str(filename),
                        mime_type=str(mime_type),
                        private=True,
                        updated_at=now,
                    )
                    .on_conflict_do_update(
                        constraint="uq_submission_drafts_assignment",
                        set_={
                            "content": str(content),
                            "filename": str(filename),
                            "mime_type": str(mime_type),
                            "updated_at": now,
                        },
                    )
                )
                draft = session.scalar(
                    select(SubmissionDraft).where(
                        SubmissionDraft.assignment_id == assignment_id
                    )
                )
        if expired:
            raise ValueError("reservation expired")
        return self._submission_draft_dict(draft)

    def get_submission_draft(self, assignment_id: str, pubkey: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            draft = session.scalar(
                select(SubmissionDraft)
                .join(Assignment, SubmissionDraft.assignment_id == Assignment.id)
                .join(User, Assignment.user_id == User.id)
                .where(
                    SubmissionDraft.assignment_id == assignment_id,
                    User.nostr_pubkey == pubkey,
                )
            )
            if draft:
                return self._submission_draft_dict(draft)
            owned = session.scalar(
                select(Assignment.id)
                .join(User, Assignment.user_id == User.id)
                .where(Assignment.id == assignment_id, User.nostr_pubkey == pubkey)
            )
            if not owned:
                raise ValueError("assignment not owned by participant")
            return None

    def create_submission(
        self,
        assignment_id: str,
        pubkey: str,
        content: str,
        stored_object_id: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        expired = False
        submission = None
        with self.sessions.begin() as session:
            assignment = session.scalar(
                select(Assignment).where(Assignment.id == assignment_id).with_for_update()
            )
            user_id = session.scalar(select(User.id).where(User.nostr_pubkey == pubkey))
            if not assignment or assignment.user_id != user_id:
                raise ValueError("assignment not owned by participant")
            is_correction = assignment.status == "CHANGES_REQUESTED"
            if assignment.status not in {"RESERVED", "CHANGES_REQUESTED"}:
                raise ValueError("assignment does not accept a submission")
            reservation = None
            if not is_correction:
                reservation = session.scalar(
                    select(AssignmentReservation).where(
                        AssignmentReservation.assignment_id == assignment_id
                    ).with_for_update()
                )
                if not reservation or reservation.status != "ACTIVE":
                    raise ValueError("assignment does not accept a submission")
                if reservation.reserved_until <= now:
                    reservation.status = "EXPIRED"
                    reservation.expired_at = now
                    assignment.status = "EXPIRED"
                    session.add(
                        OutboxEvent(
                            event_id=str(uuid.uuid4()),
                            event_type="AssignmentExpired",
                            version=1,
                            aggregate_id=assignment_id,
                            occurred_at=now,
                            payload={"assignment_id": assignment_id, "task_id": assignment.task_id},
                            attempts=0,
                        )
                    )
                    expired = True
            if not expired:
                stored = None
                if stored_object_id:
                    stored = session.get(StoredObject, stored_object_id)
                    if not stored or stored.owner_user_id != user_id or stored.scan_status != "CLEAN":
                        raise ValueError("stored object is unavailable or not clean")
                normalized_content = str(content)
                if not normalized_content.strip() and not stored:
                    raise ValueError("submission content or a clean stored object is required")
                digest_input = normalized_content.encode()
                if stored:
                    digest_input += bytes.fromhex(stored.content_hash)
                submission = Submission(
                    id=str(uuid.uuid4()),
                    assignment_id=assignment_id,
                    version=2 if is_correction else 1,
                    content=normalized_content,
                    content_hash=hashlib.sha256(digest_input).hexdigest(),
                    stored_object_id=stored_object_id,
                    private=True,
                    submitted_at=now,
                )
                assignment.status = "RESUBMITTED" if is_correction else "SUBMITTED"
                assignment.submitted_at = now
                if reservation:
                    reservation.status = "CONSUMED"
                session.add(submission)
                session.add(
                    OutboxEvent(
                        event_id=str(uuid.uuid4()),
                        event_type="SubmissionCreated",
                        version=1,
                        aggregate_id=submission.id,
                        occurred_at=now,
                        payload={
                            "submission_id": submission.id,
                            "assignment_id": assignment_id,
                            "version": submission.version,
                        },
                        attempts=0,
                    )
                )
        if expired:
            raise ValueError("reservation expired")
        return self._submission_dict(submission)

    def get_submission(self, submission_id: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            submission = session.get(Submission, submission_id)
            return self._submission_dict(submission) if submission else None

    def list_pending_submissions(self) -> list[dict[str, Any]]:
        with self.sessions() as session:
            rows = list(
                session.execute(
                    select(Submission, Assignment.status)
                    .join(Assignment, Submission.assignment_id == Assignment.id)
                    .where(Assignment.status.in_(("SUBMITTED", "RESUBMITTED")))
                    .order_by(Submission.assignment_id, Submission.version.desc())
                )
            )
        latest: dict[str, dict[str, Any]] = {}
        for submission, assignment_status in rows:
            latest.setdefault(
                submission.assignment_id,
                {**self._submission_dict(submission), "assignment_status": assignment_status},
            )
        return list(latest.values())

    def get_submission_for_review(self, submission_id: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            row = session.execute(
                select(Submission, Assignment.status, PaidTask.title, PaidTask.reward_sats)
                .join(Assignment, Submission.assignment_id == Assignment.id)
                .join(PaidTask, Assignment.task_id == PaidTask.id)
                .where(Submission.id == submission_id)
            ).one_or_none()
            if not row:
                return None
            submission, assignment_status, task_title, reward_sats = row
            return {
                **self._submission_dict(submission),
                "content": submission.content,
                "assignment_status": assignment_status,
                "task_title": task_title,
                "reward_sats": reward_sats,
            }

    def review_submission(
        self,
        submission_id: str,
        reviewer_pubkey: str,
        decision: str,
        reason: str = "",
        mode: str = "SANDBOX",
    ) -> dict[str, Any]:
        if decision not in {"APPROVE", "REQUEST_CHANGES", "REJECT"}:
            raise ValueError("invalid review decision")
        normalized_reason = str(reason).strip()
        if decision in {"REQUEST_CHANGES", "REJECT"} and not normalized_reason:
            raise ValueError("justification required")
        if mode not in {"MOCK", "SANDBOX", "REAL"}:
            raise ValueError("invalid financial mode")
        now = datetime.now(timezone.utc)
        result: dict[str, Any] | None = None
        try:
            with self.sessions.begin() as session:
                submission = session.scalar(
                    select(Submission)
                    .where(Submission.id == submission_id)
                )
                if not submission:
                    raise KeyError(submission_id)
                assignment = session.scalar(
                    select(Assignment)
                    .where(Assignment.id == submission.assignment_id)
                    .with_for_update()
                )
                reviewer_user_id = session.scalar(
                    select(User.id).where(User.nostr_pubkey == reviewer_pubkey)
                )
                if not reviewer_user_id:
                    raise KeyError(reviewer_pubkey)
                existing = session.scalar(
                    select(Review).where(Review.submission_id == submission_id)
                )
                if existing:
                    if existing.decision != decision:
                        raise ReviewConflict("submission already has another decision")
                    obligation = session.scalar(
                        select(PaymentObligation).where(
                            PaymentObligation.assignment_id == assignment.id
                        )
                    )
                    result = {
                        "review": self._review_dict(existing),
                        "payment_obligation": (
                            self._obligation_dict(obligation) if obligation else None
                        ),
                    }
                else:
                    if assignment.status not in {"SUBMITTED", "RESUBMITTED"}:
                        raise ReviewConflict("assignment is not awaiting review")
                    previous_status = assignment.status
                    if decision == "REQUEST_CHANGES":
                        if session.scalar(
                            select(Review.id).where(
                                Review.assignment_id == assignment.id,
                                Review.decision == "REQUEST_CHANGES",
                            )
                        ):
                            raise ReviewConflict("the single correction was already used")
                        new_status = "CHANGES_REQUESTED"
                    elif decision == "REJECT":
                        new_status = "REJECTED"
                    else:
                        new_status = "PAYMENT_PENDING"

                    review = Review(
                        id=str(uuid.uuid4()),
                        submission_id=submission_id,
                        assignment_id=assignment.id,
                        reviewer_user_id=reviewer_user_id,
                        decision=decision,
                        reason=normalized_reason,
                        previous_status=previous_status,
                        new_status=new_status,
                        created_at=now,
                    )
                    assignment.status = new_status
                    session.add(review)
                    obligation = None
                    if decision == "APPROVE":
                        task = session.scalar(
                            select(PaidTask)
                            .where(PaidTask.id == assignment.task_id)
                            .with_for_update()
                        )
                        funding = session.scalar(
                            select(TaskFundingReservation).where(
                                TaskFundingReservation.task_id == task.id,
                                TaskFundingReservation.status == "RESERVED",
                            )
                        )
                        if not funding or funding.amount_sats != task.reward_sats:
                            raise ReviewConflict("task funding is unavailable")
                        transaction_id = str(uuid.uuid4())
                        obligation = PaymentObligation(
                            id=str(uuid.uuid4()),
                            assignment_id=assignment.id,
                            amount_sats=task.reward_sats,
                            status="OPEN",
                            mode=mode,
                            created_at=now,
                        )
                        session.add_all(
                            [
                                LedgerTransaction(
                                    id=transaction_id,
                                    event_type="ASSIGNMENT_APPROVED",
                                    reference_id=f"assignment-approval:{assignment.id}",
                                    mode=mode,
                                    occurred_at=now,
                                ),
                                obligation,
                            ]
                        )
                        session.flush()
                        session.add_all(
                            [
                                LedgerEntry(
                                    id=str(uuid.uuid4()),
                                    transaction_id=transaction_id,
                                    account="TASK_RESERVED",
                                    direction="DEBIT",
                                    amount_sats=task.reward_sats,
                                    source_id=task.id,
                                ),
                                LedgerEntry(
                                    id=str(uuid.uuid4()),
                                    transaction_id=transaction_id,
                                    account="PARTICIPANT_PAYABLE",
                                    direction="CREDIT",
                                    amount_sats=task.reward_sats,
                                    source_id=assignment.id,
                                ),
                            ]
                        )
                    session.add(
                        AuditEvent(
                            event_id=str(uuid.uuid4()),
                            actor_id=reviewer_user_id,
                            action=f"SUBMISSION_{decision}",
                            aggregate_type="Assignment",
                            aggregate_id=assignment.id,
                            occurred_at=now,
                            details={
                                "submission_id": submission_id,
                                "decision": decision,
                                "previous_status": previous_status,
                                "new_status": new_status,
                                "reason": normalized_reason,
                            },
                        )
                    )
                    event_type = {
                        "APPROVE": "SubmissionApproved",
                        "REQUEST_CHANGES": "ChangesRequested",
                        "REJECT": "SubmissionRejected",
                    }[decision]
                    session.add(
                        OutboxEvent(
                            event_id=str(uuid.uuid4()),
                            event_type=event_type,
                            version=1,
                            aggregate_id=assignment.id,
                            occurred_at=now,
                            payload={
                                "assignment_id": assignment.id,
                                "submission_id": submission_id,
                                "decision": decision,
                            },
                            attempts=0,
                        )
                    )
                    if obligation:
                        session.add(
                            OutboxEvent(
                                event_id=str(uuid.uuid4()),
                                event_type="PaymentObligationCreated",
                                version=1,
                                aggregate_id=obligation.id,
                                occurred_at=now,
                                payload={
                                    "payment_obligation_id": obligation.id,
                                    "assignment_id": assignment.id,
                                    "amount_sats": obligation.amount_sats,
                                    "mode": obligation.mode,
                                },
                                attempts=0,
                            )
                        )
                    result = {
                        "review": self._review_dict(review),
                        "payment_obligation": (
                            self._obligation_dict(obligation) if obligation else None
                        ),
                    }
        except IntegrityError as error:
            raise ReviewConflict("review conflicts with an existing decision") from error
        return result

    def create_opportunity_listing(
        self,
        pubkey: str,
        title: str,
        category: str,
        description: str,
        organization_name: str,
        external_url: str,
        *,
        format: str,
        location: str | None,
        starts_at: str,
        application_deadline: str | None,
        tags: list[str] | None,
        requirements: str,
        non_remunerated_ack: bool,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        normalized_url = str(external_url).strip()
        parsed = urlparse(normalized_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("a secure external origin is required")
        normalized_title = str(title).strip()
        normalized_category = str(category).strip().upper()
        normalized_description = str(description).strip()
        normalized_organization = str(organization_name).strip()
        normalized_format = str(format).strip().upper()
        normalized_location = str(location or "").strip() or None
        normalized_requirements = str(requirements or "").strip()
        normalized_tags = list(dict.fromkeys(str(tag).strip().lstrip("#") for tag in (tags or []) if str(tag).strip()))
        normalized_idempotency_key = str(idempotency_key or "").strip() or None
        if not all(
            (
                normalized_title,
                normalized_category,
                normalized_description,
                normalized_organization,
            )
        ):
            raise ValueError("opportunity fields are required")
        if len(normalized_title) > 200 or len(normalized_organization) > 160:
            raise ValueError("opportunity field is too long")
        if normalized_category not in OPPORTUNITY_TYPES or normalized_format not in OPPORTUNITY_FORMATS:
            raise ValueError("invalid opportunity type or format")
        if normalized_format != "ONLINE" and not normalized_location:
            raise ValueError("location is required for onsite or hybrid opportunities")
        if non_remunerated_ack is not True:
            raise ValueError("non-remunerated opportunity acknowledgement is required")
        if len(normalized_tags) > 8 or any(len(tag) > 40 for tag in normalized_tags):
            raise ValueError("invalid opportunity tags")
        if len(normalized_requirements) > 2000:
            raise ValueError("opportunity requirements are too long")
        try:
            normalized_starts_at = datetime.fromisoformat(str(starts_at).replace("Z", "+00:00"))
            normalized_deadline = (
                datetime.fromisoformat(str(application_deadline).replace("Z", "+00:00"))
                if application_deadline
                else None
            )
        except ValueError as error:
            raise ValueError("invalid opportunity date") from error
        if normalized_starts_at.tzinfo is None:
            normalized_starts_at = normalized_starts_at.replace(tzinfo=timezone.utc)
        if normalized_deadline and normalized_deadline.tzinfo is None:
            normalized_deadline = normalized_deadline.replace(tzinfo=timezone.utc)
        if normalized_deadline and normalized_deadline > normalized_starts_at:
            raise ValueError("application deadline must not be after the start date")
        now = datetime.now(timezone.utc)
        author_user_id = None
        try:
            with self.sessions.begin() as session:
                author_user_id = session.scalar(select(User.id).where(User.nostr_pubkey == pubkey))
                if not author_user_id:
                    raise KeyError(pubkey)
                if normalized_idempotency_key:
                    existing = session.scalar(
                        select(OpportunityListing).where(
                            OpportunityListing.author_user_id == author_user_id,
                            OpportunityListing.idempotency_key == normalized_idempotency_key,
                        )
                    )
                    if existing:
                        return self._opportunity_listing_dict(existing, pubkey)
                listing = OpportunityListing(
                    id=str(uuid.uuid4()),
                    author_user_id=author_user_id,
                    title=normalized_title,
                    category=normalized_category,
                    description=normalized_description,
                    organization_name=normalized_organization,
                    external_url=normalized_url,
                    format=normalized_format,
                    location=normalized_location,
                    starts_at=normalized_starts_at,
                    application_deadline=normalized_deadline,
                    tags=normalized_tags,
                    requirements=normalized_requirements,
                    non_remunerated_ack=True,
                    moderation_status="VISIBLE",
                    idempotency_key=normalized_idempotency_key,
                    status="PUBLISHED",
                    created_at=now,
                )
                session.add(listing)
                session.add(OutboxEvent(
                    event_id=str(uuid.uuid4()), event_type="OpportunityPublished", version=1,
                    aggregate_id=listing.id, occurred_at=now,
                    payload={"opportunity_listing_id": listing.id, "type": "EXTERNAL_OPPORTUNITY", "delivery": "LOCAL_ONLY"},
                    attempts=0,
                ))
        except IntegrityError:
            if not normalized_idempotency_key or not author_user_id:
                raise
            with self.sessions() as session:
                existing = session.scalar(select(OpportunityListing).where(
                    OpportunityListing.author_user_id == author_user_id,
                    OpportunityListing.idempotency_key == normalized_idempotency_key,
                ))
                if not existing:
                    raise
                return self._opportunity_listing_dict(existing, pubkey)
        return self.get_opportunity_listing(listing.id)

    def get_opportunity_listing(self, listing_id: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            row = session.execute(
                select(OpportunityListing, User.nostr_pubkey)
                .join(User, OpportunityListing.author_user_id == User.id)
                .where(OpportunityListing.id == listing_id)
            ).one_or_none()
            return self._opportunity_listing_dict(*row) if row else None

    def list_opportunity_listings(self) -> list[dict[str, Any]]:
        with self.sessions() as session:
            rows = list(
                session.execute(
                    select(OpportunityListing, User.nostr_pubkey)
                    .join(User, OpportunityListing.author_user_id == User.id)
                    .where(
                        OpportunityListing.status == "PUBLISHED",
                        OpportunityListing.moderation_status == "VISIBLE",
                    )
                    .order_by(OpportunityListing.created_at.desc(), OpportunityListing.id)
                )
            )
        return [self._opportunity_listing_dict(*row) for row in rows]

    @staticmethod
    def _validate_public_content(content: str) -> str:
        normalized = str(content).strip()
        if not normalized or len(normalized) > 2000:
            raise ValueError("invalid public post")
        lowered = normalized.lower()
        forbidden_markers = ("nsec1", "lnbc", "lntb", "invoice", "payment_hash", "preimage")
        if any(marker in lowered for marker in forbidden_markers):
            raise ValueError("public post contains prohibited sensitive or financial data")
        if re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", normalized):
            raise ValueError("public post contains personal data")
        return normalized

    def create_local_community_post(
        self,
        pubkey: str,
        category: str,
        content: str,
        public_acknowledged: bool,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if public_acknowledged is not True:
            raise ValueError("public Nostr warning must be acknowledged")
        if category not in {"learning", "question", "achievement"}:
            raise ValueError("invalid public post category")
        normalized_content = self._validate_public_content(content)
        normalized_idempotency_key = str(idempotency_key or "").strip() or None
        now = datetime.now(timezone.utc)
        author_user_id = None
        try:
            with self.sessions.begin() as session:
                author_user_id = session.scalar(
                    select(User.id).where(User.nostr_pubkey == pubkey)
                )
                if not author_user_id:
                    raise KeyError(pubkey)
                if normalized_idempotency_key:
                    existing = session.scalar(
                        select(CommunityPostReference).where(
                            CommunityPostReference.author_user_id == author_user_id,
                            CommunityPostReference.idempotency_key == normalized_idempotency_key,
                        )
                    )
                    if existing:
                        return self._community_post_dict(existing, pubkey)
                post = CommunityPostReference(
                    id=str(uuid.uuid4()), author_user_id=author_user_id, category=category,
                    content=normalized_content, moderation_status="VISIBLE",
                    relay_status="LOCAL_ONLY", mode="SANDBOX",
                    idempotency_key=normalized_idempotency_key, created_at=now,
                )
                session.add(post)
        except IntegrityError:
            if not normalized_idempotency_key or not author_user_id:
                raise
            with self.sessions() as session:
                existing = session.scalar(select(CommunityPostReference).where(
                    CommunityPostReference.author_user_id == author_user_id,
                    CommunityPostReference.idempotency_key == normalized_idempotency_key,
                ))
                if not existing:
                    raise
                return self._community_post_dict(existing, pubkey)
        return self._community_post_dict(post, pubkey)

    def list_visible_community_posts(
        self, limit: int = 20, offset: int = 0, category: str | None = None
    ) -> list[dict[str, Any]]:
        with self.sessions() as session:
            statement = (
                select(CommunityPostReference, User.nostr_pubkey)
                .join(User, CommunityPostReference.author_user_id == User.id)
                .where(CommunityPostReference.moderation_status == "VISIBLE")
            )
            if category:
                if category not in {"learning", "question", "achievement"}:
                    raise ValueError("invalid post category")
                statement = statement.where(CommunityPostReference.category == category)
            rows = list(session.execute(
                statement.order_by(CommunityPostReference.created_at.desc(), CommunityPostReference.id)
                .offset(offset).limit(limit)
            ))
        return [self._community_post_dict(*row) for row in rows]

    def report_community_content(
        self,
        pubkey: str,
        subject_type: str,
        subject_id: str,
        category: str,
        details: str = "",
    ) -> dict[str, Any]:
        normalized_subject_type = str(subject_type).strip().upper()
        normalized_category = str(category).strip().upper()
        normalized_details = str(details or "").strip()
        if normalized_subject_type not in {"POST", "OPPORTUNITY"}:
            raise ValueError("invalid report subject")
        if normalized_category not in REPORT_CATEGORIES:
            raise ValueError("invalid report category")
        if normalized_category == "OTHER" and not normalized_details:
            raise ValueError("details are required for OTHER reports")
        if len(normalized_details) > 1000:
            raise ValueError("report details are too long")
        now = datetime.now(timezone.utc)
        report = ContentReport(
            id=str(uuid.uuid4()),
            post_reference_id=subject_id if normalized_subject_type == "POST" else None,
            opportunity_listing_id=subject_id if normalized_subject_type == "OPPORTUNITY" else None,
            reporter_user_id="",
            reason=normalized_category,
            category=normalized_category,
            details=normalized_details,
            status="OPEN",
            created_at=now,
        )
        try:
            with self.sessions.begin() as session:
                reporter_user_id = session.scalar(
                    select(User.id).where(User.nostr_pubkey == pubkey)
                )
                target = (
                    session.get(CommunityPostReference, subject_id)
                    if normalized_subject_type == "POST"
                    else session.get(OpportunityListing, subject_id)
                )
                if not reporter_user_id or not target:
                    raise KeyError(subject_id)
                report.reporter_user_id = reporter_user_id
                session.add(report)
                session.add(
                    AuditEvent(
                        event_id=str(uuid.uuid4()),
                        actor_id=reporter_user_id,
                        action="COMMUNITY_CONTENT_REPORTED",
                        aggregate_type="CommunityPostReference" if normalized_subject_type == "POST" else "OpportunityListing",
                        aggregate_id=subject_id,
                        occurred_at=now,
                        details={"report_id": report.id, "status": "OPEN", "category": normalized_category},
                    )
                )
        except IntegrityError as error:
            raise ValueError("content was already reported by this participant") from error
        return {
            "id": report.id,
            "subject_type": normalized_subject_type,
            "subject_id": subject_id,
            "category": report.category,
            "details": report.details,
            "status": report.status,
            "created_at": report.created_at.isoformat(),
        }

    def report_community_post(self, pubkey: str, post_id: str, reason: str) -> dict[str, Any]:
        return self.report_community_content(pubkey, "POST", post_id, "OTHER", reason)

    def moderate_community_content(
        self,
        moderator_pubkey: str,
        subject_type: str,
        subject_id: str,
        action: str,
        reason: str,
    ) -> dict[str, Any]:
        normalized_subject_type = str(subject_type).strip().upper()
        if normalized_subject_type not in {"POST", "OPPORTUNITY"}:
            raise ValueError("invalid moderation subject")
        if action not in {"HIDE", "RESTORE", "KEEP"}:
            raise ValueError("invalid moderation action")
        normalized_reason = str(reason).strip()
        if not normalized_reason:
            raise ValueError("moderation reason is required")
        now = datetime.now(timezone.utc)
        with self.sessions.begin() as session:
            moderator_user_id = session.scalar(
                select(User.id).where(User.nostr_pubkey == moderator_pubkey)
            )
            model = CommunityPostReference if normalized_subject_type == "POST" else OpportunityListing
            target = session.scalar(select(model).where(model.id == subject_id).with_for_update())
            if not moderator_user_id or not target:
                raise KeyError(subject_id)
            if target.author_user_id == moderator_user_id:
                raise ValueError("authors cannot moderate their own content")
            expected_previous = "HIDDEN" if action == "RESTORE" else "VISIBLE"
            new_status = "HIDDEN" if action == "HIDE" else "VISIBLE"
            if target.moderation_status != expected_previous:
                raise ValueError("moderation transition is not applicable")
            decision = ModerationDecision(
                id=str(uuid.uuid4()),
                post_reference_id=subject_id if normalized_subject_type == "POST" else None,
                opportunity_listing_id=subject_id if normalized_subject_type == "OPPORTUNITY" else None,
                moderator_user_id=moderator_user_id,
                action=action,
                reason=normalized_reason,
                previous_status=target.moderation_status,
                new_status=new_status,
                created_at=now,
            )
            target.moderation_status = new_status
            session.add(decision)
            session.add(
                AuditEvent(
                    event_id=str(uuid.uuid4()),
                    actor_id=moderator_user_id,
                    action=f"COMMUNITY_CONTENT_{action}",
                    aggregate_type="CommunityPostReference" if normalized_subject_type == "POST" else "OpportunityListing",
                    aggregate_id=subject_id,
                    occurred_at=now,
                    details={
                        "moderation_decision_id": decision.id,
                        "previous_status": decision.previous_status,
                        "new_status": decision.new_status,
                        "reason": normalized_reason,
                    },
                )
            )
        return {
            "id": decision.id,
            "subject_type": normalized_subject_type,
            "subject_id": subject_id,
            "action": action,
            "reason": normalized_reason,
            "previous_status": decision.previous_status,
            "new_status": decision.new_status,
            "created_at": now.isoformat(),
        }

    def moderate_community_post(
        self, moderator_pubkey: str, post_id: str, action: str, reason: str
    ) -> dict[str, Any]:
        return self.moderate_community_content(moderator_pubkey, "POST", post_id, action, reason)

    def list_community_moderation_queue(self) -> list[dict[str, Any]]:
        with self.sessions() as session:
            reports = list(session.scalars(select(ContentReport).order_by(ContentReport.created_at.asc())))
            items: list[dict[str, Any]] = []
            represented: set[tuple[str, str]] = set()
            unresolved: dict[tuple[str, str], list[ContentReport]] = {}
            for report in reports:
                subject_type = "POST" if report.post_reference_id else "OPPORTUNITY"
                subject_id = report.post_reference_id or report.opportunity_listing_id
                decision_filter = (
                    ModerationDecision.post_reference_id == subject_id
                    if subject_type == "POST"
                    else ModerationDecision.opportunity_listing_id == subject_id
                )
                latest_decision = session.scalar(
                    select(ModerationDecision).where(decision_filter)
                    .order_by(ModerationDecision.created_at.desc()).limit(1)
                )
                if latest_decision and latest_decision.created_at >= report.created_at:
                    continue
                unresolved.setdefault((subject_type, subject_id), []).append(report)
            for (subject_type, subject_id), subject_reports in unresolved.items():
                target = session.get(
                    CommunityPostReference if subject_type == "POST" else OpportunityListing,
                    subject_id,
                )
                if target:
                    represented.add((subject_type, subject_id))
                    latest_report = subject_reports[-1]
                    items.append({
                        "report_id": latest_report.id, "report_count": len(subject_reports),
                        "subject_type": subject_type, "subject_id": subject_id,
                        "category": latest_report.category, "details": latest_report.details,
                        "moderation_status": target.moderation_status,
                        "excerpt": target.content[:240] if subject_type == "POST" else target.title,
                    })
            for model, subject_type in (
                (CommunityPostReference, "POST"), (OpportunityListing, "OPPORTUNITY")
            ):
                hidden = session.scalars(select(model).where(model.moderation_status == "HIDDEN"))
                for target in hidden:
                    if (subject_type, target.id) not in represented:
                        items.append({
                            "report_id": None, "report_count": 0, "subject_type": subject_type,
                            "subject_id": target.id, "category": None, "details": "",
                            "moderation_status": "HIDDEN",
                            "excerpt": target.content[:240] if subject_type == "POST" else target.title,
                        })
        return items

    def mark_assignment_approved(self, assignment_id: str) -> dict[str, Any]:
        raise RuntimeError("approval must use review_submission")

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

    def create_payout_attempt(
        self,
        obligation_id: str,
        idempotency_key: str,
        mode: str,
        *,
        invoice_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not idempotency_key:
            raise ValueError("idempotency key is required")
        metadata = self._normalize_invoice_metadata(invoice_metadata)
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
                if metadata.get("amount_sats") not in {None, obligation.amount_sats}:
                    raise ValueError("invoice amount does not match obligation")
                attempt = PayoutAttempt(
                    id=str(uuid.uuid4()),
                    payment_obligation_id=obligation_id,
                    idempotency_key=idempotency_key,
                    payment_hash=metadata.get("payment_hash"),
                    invoice_hash=metadata.get("invoice_hash"),
                    invoice_network=metadata.get("network"),
                    invoice_amount_sats=metadata.get("amount_sats"),
                    invoice_expires_at=metadata.get("expires_at"),
                    status="VALIDATED",
                    mode=mode,
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(attempt)
                session.flush()
                obligation.status = "CLEARING"
                self._add_ledger_transaction(
                    session,
                    event_type="PayoutDispatchRequested",
                    reference_id=f"payout-dispatch:{attempt.id}",
                    mode=mode,
                    entries=[
                        {
                            "account": "PARTICIPANT_PAYABLE",
                            "direction": "DEBIT",
                            "amount_sats": obligation.amount_sats,
                            "source_id": obligation.id,
                        },
                        {
                            "account": "LIGHTNING_CLEARING",
                            "direction": "CREDIT",
                            "amount_sats": obligation.amount_sats,
                            "source_id": obligation.id,
                        },
                    ],
                )
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

    def mark_payout_processing(self, attempt_id: str, *, provider: str) -> dict[str, Any]:
        normalized_provider = str(provider).strip().upper()
        if not normalized_provider or len(normalized_provider) > 40:
            raise ValueError("provider is invalid")
        with self.sessions.begin() as session:
            attempt = session.scalar(
                select(PayoutAttempt).where(PayoutAttempt.id == attempt_id).with_for_update()
            )
            if not attempt:
                raise KeyError(attempt_id)
            existing = session.scalar(
                select(ProviderPayment).where(ProviderPayment.payout_attempt_id == attempt_id)
            )
            if attempt.status == "PROCESSING" and existing:
                return self._attempt_dict(attempt)
            if attempt.status != "VALIDATED":
                raise ValueError(f"attempt is {attempt.status}")
            if not attempt.payment_hash:
                raise ValueError("validated payment_hash is required before processing")
            now = datetime.now(timezone.utc)
            attempt.status = "PROCESSING"
            attempt.updated_at = now
            session.flush()
            session.add(
                ProviderPayment(
                    id=str(uuid.uuid4()),
                    payout_attempt_id=attempt.id,
                    provider=normalized_provider,
                    payment_hash=attempt.payment_hash,
                    status="PROCESSING",
                    mode=attempt.mode,
                    created_at=now,
                )
            )
            session.add(
                AuditEvent(
                    event_id=str(uuid.uuid4()),
                    actor_id=None,
                    action="PAYOUT_PROCESSING",
                    aggregate_type="PayoutAttempt",
                    aggregate_id=attempt.id,
                    occurred_at=now,
                    details={"provider": normalized_provider, "mode": attempt.mode},
                )
            )
        return self._attempt_dict(attempt)

    def mark_payout_ambiguous(
        self, attempt_id: str, *, provider_event_id: str
    ) -> dict[str, Any]:
        event_id = str(provider_event_id).strip()
        if not event_id or len(event_id) > 160:
            raise ValueError("provider_event_id is invalid")
        with self.sessions.begin() as session:
            attempt = session.scalar(
                select(PayoutAttempt).where(PayoutAttempt.id == attempt_id).with_for_update()
            )
            if not attempt:
                raise KeyError(attempt_id)
            payment = session.scalar(
                select(ProviderPayment)
                .where(ProviderPayment.payout_attempt_id == attempt_id)
                .with_for_update()
            )
            if not payment:
                raise ValueError("provider payment was not started")
            repeated = session.scalar(
                select(ProviderEvent).where(
                    ProviderEvent.provider == payment.provider,
                    ProviderEvent.provider_event_id == event_id,
                )
            )
            if repeated:
                if repeated.payout_attempt_id != attempt_id or repeated.event_type != "AMBIGUOUS":
                    raise IdempotencyConflict("provider event belongs to another outcome")
                return self._attempt_dict(attempt)
            if attempt.status != "PROCESSING":
                raise ValueError(f"attempt is {attempt.status}")
            now = datetime.now(timezone.utc)
            attempt.status = "AMBIGUOUS"
            attempt.updated_at = now
            session.flush()
            payment.status = "AMBIGUOUS"
            session.add(
                ProviderEvent(
                    id=str(uuid.uuid4()),
                    provider=payment.provider,
                    provider_event_id=event_id,
                    payout_attempt_id=attempt.id,
                    event_type="AMBIGUOUS",
                    payload_hash=self._provider_event_hash(
                        payment.provider, event_id, attempt.id, "AMBIGUOUS"
                    ),
                    created_at=now,
                )
            )
            session.add(
                OutboxEvent(
                    event_id=str(uuid.uuid4()),
                    event_type="PaymentAmbiguous",
                    version=1,
                    aggregate_id=attempt.id,
                    occurred_at=now,
                    payload={"payout_attempt_id": attempt.id, "mode": attempt.mode},
                    attempts=0,
                )
            )
            session.add(
                AuditEvent(
                    event_id=str(uuid.uuid4()),
                    actor_id=None,
                    action="PAYMENT_AMBIGUOUS",
                    aggregate_type="PayoutAttempt",
                    aggregate_id=attempt.id,
                    occurred_at=now,
                    details={"provider_event_id_hash": hashlib.sha256(event_id.encode()).hexdigest()},
                )
            )
        return self._attempt_dict(attempt)

    def reconcile_payout_attempt(
        self,
        attempt_id: str,
        *,
        outcome: str,
        provider_event_id: str,
        provider_reference: str | None = None,
    ) -> dict[str, Any]:
        normalized_outcome = str(outcome).strip().upper()
        if normalized_outcome not in {"SETTLED", "FAILED"}:
            raise ValueError("outcome must be SETTLED or FAILED")
        event_id = str(provider_event_id).strip()
        if not event_id or len(event_id) > 160:
            raise ValueError("provider_event_id is invalid")
        normalized_reference = str(provider_reference).strip() if provider_reference else None
        if normalized_reference and len(normalized_reference) > 160:
            raise ValueError("provider_reference is invalid")
        with self.sessions.begin() as session:
            attempt = session.scalar(
                select(PayoutAttempt).where(PayoutAttempt.id == attempt_id).with_for_update()
            )
            if not attempt:
                raise KeyError(attempt_id)
            obligation = session.scalar(
                select(PaymentObligation)
                .where(PaymentObligation.id == attempt.payment_obligation_id)
                .with_for_update()
            )
            payment = session.scalar(
                select(ProviderPayment)
                .where(ProviderPayment.payout_attempt_id == attempt_id)
                .with_for_update()
            )
            if not payment:
                raise ValueError("provider payment was not started")
            repeated = session.scalar(
                select(ProviderEvent).where(
                    ProviderEvent.provider == payment.provider,
                    ProviderEvent.provider_event_id == event_id,
                )
            )
            if repeated:
                if repeated.payout_attempt_id != attempt_id or repeated.event_type != normalized_outcome:
                    raise IdempotencyConflict("provider event belongs to another outcome")
                if normalized_outcome == "SETTLED":
                    receipt = session.scalar(
                        select(PaymentReceipt).where(PaymentReceipt.payout_attempt_id == attempt_id)
                    )
                    return self._payment_receipt_dict(receipt)
                return self._attempt_dict(attempt)
            if attempt.status not in {"PROCESSING", "AMBIGUOUS"}:
                raise ValueError(f"attempt is {attempt.status}")
            now = datetime.now(timezone.utc)
            attempt.status = normalized_outcome
            attempt.updated_at = now
            attempt.failure_code = "PROVIDER_FAILED" if normalized_outcome == "FAILED" else None
            session.flush()
            payment.status = normalized_outcome
            payment.provider_reference = normalized_reference
            payment.reconciled_at = now
            session.add(
                ProviderEvent(
                    id=str(uuid.uuid4()),
                    provider=payment.provider,
                    provider_event_id=event_id,
                    payout_attempt_id=attempt.id,
                    event_type=normalized_outcome,
                    payload_hash=self._provider_event_hash(
                        payment.provider, event_id, attempt.id, normalized_outcome
                    ),
                    created_at=now,
                )
            )
            if normalized_outcome == "SETTLED":
                ledger_id = self._add_ledger_transaction(
                    session,
                    event_type="PaymentSettled",
                    reference_id=f"payout-settled:{attempt.id}",
                    mode=attempt.mode,
                    entries=[
                        {"account": "LIGHTNING_CLEARING", "direction": "DEBIT", "amount_sats": obligation.amount_sats, "source_id": obligation.id},
                        {"account": "SETTLED", "direction": "CREDIT", "amount_sats": obligation.amount_sats, "source_id": obligation.id},
                    ],
                )
                obligation.status = "SETTLED"
                assignment = session.get(Assignment, obligation.assignment_id)
                if assignment:
                    assignment.status = "PAID"
                receipt = PaymentReceipt(
                    id=str(uuid.uuid4()),
                    payment_obligation_id=obligation.id,
                    payout_attempt_id=attempt.id,
                    ledger_transaction_id=ledger_id,
                    receipt_number=f"BJ-SBX-{attempt.id}",
                    assignment_id=obligation.assignment_id,
                    amount_sats=obligation.amount_sats,
                    status="SETTLED",
                    mode=attempt.mode,
                    issued_at=now,
                )
                session.add(receipt)
            else:
                self._add_ledger_transaction(
                    session,
                    event_type="PaymentFailedCompensated",
                    reference_id=f"payout-failed:{attempt.id}",
                    mode=attempt.mode,
                    entries=[
                        {"account": "LIGHTNING_CLEARING", "direction": "DEBIT", "amount_sats": obligation.amount_sats, "source_id": obligation.id},
                        {"account": "PARTICIPANT_PAYABLE", "direction": "CREDIT", "amount_sats": obligation.amount_sats, "source_id": obligation.id},
                    ],
                )
                obligation.status = "OPEN"
                assignment = session.get(Assignment, obligation.assignment_id)
                if assignment:
                    assignment.status = "PAYMENT_FAILED"
            session.add(
                OutboxEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=f"Payment{normalized_outcome.title()}",
                    version=1,
                    aggregate_id=attempt.id,
                    occurred_at=now,
                    payload={"payout_attempt_id": attempt.id, "mode": attempt.mode},
                    attempts=0,
                )
            )
            session.add(
                AuditEvent(
                    event_id=str(uuid.uuid4()),
                    actor_id=None,
                    action=f"PAYMENT_{normalized_outcome}",
                    aggregate_type="PayoutAttempt",
                    aggregate_id=attempt.id,
                    occurred_at=now,
                    details={"provider_event_id_hash": hashlib.sha256(event_id.encode()).hexdigest()},
                )
            )
            session.flush()
            result = self._payment_receipt_dict(receipt) if normalized_outcome == "SETTLED" else self._attempt_dict(attempt)
        return result

    def get_payment_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            receipt = session.get(PaymentReceipt, receipt_id)
            return self._payment_receipt_dict(receipt) if receipt else None

    def get_wallet_summary(self, pubkey: str, default_mode: str = "SANDBOX") -> dict[str, Any]:
        normalized_pubkey = normalize_nostr_pubkey(pubkey)
        with self.sessions() as session:
            user_id = session.scalar(
                select(User.id).where(User.nostr_pubkey == normalized_pubkey)
            )
            if not user_id:
                raise KeyError(normalized_pubkey)
            receipts = list(
                session.scalars(
                    select(PaymentReceipt)
                    .join(Assignment, Assignment.id == PaymentReceipt.assignment_id)
                    .where(Assignment.user_id == user_id)
                    .order_by(PaymentReceipt.issued_at.desc())
                )
            )
            assignments = list(
                session.scalars(
                    select(Assignment)
                    .where(
                        Assignment.user_id == user_id,
                        Assignment.status.not_in(("PAID", "EXPIRED", "REJECTED")),
                    )
                    .order_by(Assignment.created_at.desc())
                )
            )
        transactions = [self._payment_receipt_dict(receipt) for receipt in receipts]
        receipt_modes = {receipt.mode for receipt in receipts}
        mode = "REAL" if receipt_modes == {"REAL"} else default_mode
        return {
            "mode": mode,
            "score": 0,
            "total_sats": sum(receipt.amount_sats for receipt in receipts),
            "transactions": transactions,
            "in_progress": [
                {
                    "id": assignment.id,
                    "assignment_id": assignment.id,
                    "status": assignment.status,
                }
                for assignment in assignments
            ],
        }

    def receipt_owned_by_pubkey(self, receipt_id: str, pubkey: str) -> bool:
        normalized_pubkey = normalize_nostr_pubkey(pubkey)
        with self.sessions() as session:
            receipt = session.get(PaymentReceipt, receipt_id)
            if not receipt:
                return False
            owner_pubkey = session.scalar(
                select(User.nostr_pubkey)
                .join(Assignment, Assignment.user_id == User.id)
                .where(Assignment.id == receipt.assignment_id)
            )
            return owner_pubkey == normalized_pubkey

    def create_donor_contribution(
        self,
        pubkey: str,
        *,
        idempotency_key: str,
        amount_sats: int,
        impact_percentage_bps: int,
        liquidity_percentage_bps: int,
        terms_version: str,
        terms_accepted: bool,
        mode: str,
    ) -> dict[str, Any]:
        normalized_pubkey = normalize_nostr_pubkey(pubkey)
        if not self.has_any_role(normalized_pubkey, {"DONOR"}):
            raise PermissionError("DONOR role is required")
        if not idempotency_key or len(idempotency_key) > 255:
            raise ValueError("idempotency key is required")
        if isinstance(amount_sats, bool) or not isinstance(amount_sats, int) or amount_sats <= 0:
            raise ValueError("amount_sats must be a positive integer")
        for value in (impact_percentage_bps, liquidity_percentage_bps):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 10000:
                raise ValueError("allocation percentages must be integer basis points")
        if impact_percentage_bps + liquidity_percentage_bps != 10000:
            raise ValueError("allocation must total 10000 basis points")
        normalized_terms = str(terms_version).strip()
        if not terms_accepted or not normalized_terms or len(normalized_terms) > 40:
            raise ValueError("specific terms acceptance is required")
        if mode != "SANDBOX":
            raise ValueError("local donor contribution only supports SANDBOX")
        impact_sats = amount_sats * impact_percentage_bps // 10000
        liquidity_sats = amount_sats - impact_sats
        if impact_percentage_bps and impact_sats <= 0:
            raise ValueError("impact allocation rounds to zero sats")
        if liquidity_percentage_bps and liquidity_sats <= 0:
            raise ValueError("liquidity allocation rounds to zero sats")

        try:
            with self.sessions.begin() as session:
                session.execute(
                    text("SELECT pg_advisory_xact_lock(hashtextextended(:idempotency_key, 0))"),
                    {"idempotency_key": f"donor:{idempotency_key}"},
                )
                user = session.scalar(
                    select(User).where(User.nostr_pubkey == normalized_pubkey).with_for_update()
                )
                if not user:
                    raise PermissionError("DONOR identity is not registered")
                profile = session.scalar(
                    select(DonorProfile).where(DonorProfile.user_id == user.id)
                )
                if not profile:
                    profile = DonorProfile(
                        id=str(uuid.uuid4()),
                        user_id=user.id,
                        display_name=None,
                        terms_version=normalized_terms,
                        created_at=datetime.now(timezone.utc),
                    )
                    session.add(profile)
                    session.flush()
                repeated = session.scalar(
                    select(Contribution).where(
                        Contribution.idempotency_key == idempotency_key
                    )
                )
                if repeated:
                    if repeated.donor_profile_id != profile.id:
                        raise IdempotencyConflict(
                            "idempotency key belongs to another donor"
                        )
                    return self._donor_contribution_bundle(session, repeated)

                now = datetime.now(timezone.utc)
                contribution = Contribution(
                    id=str(uuid.uuid4()),
                    donor_profile_id=profile.id,
                    idempotency_key=idempotency_key,
                    input_amount_sats=amount_sats,
                    input_currency="SAT",
                    terms_version=normalized_terms,
                    terms_accepted_at=now,
                    status="ALLOCATED",
                    mode=mode,
                    created_at=now,
                )
                session.add(contribution)
                session.flush()
                allocations: list[ContributionAllocation] = []
                for allocation_type, allocated_sats, percentage_bps in (
                    ("IMPACT_FUND", impact_sats, impact_percentage_bps),
                    ("LIQUIDITY_CAPITAL", liquidity_sats, liquidity_percentage_bps),
                ):
                    if percentage_bps == 0:
                        continue
                    allocation = ContributionAllocation(
                        id=str(uuid.uuid4()),
                        contribution_id=contribution.id,
                        allocation_type=allocation_type,
                        amount_sats=allocated_sats,
                        percentage_bps=percentage_bps,
                        status="ALLOCATED",
                        created_at=now,
                    )
                    allocations.append(allocation)
                session.add_all(allocations)
                ledger_entries = [
                    {
                        "account": "SANDBOX_CONTRIBUTION_RECEIVED",
                        "direction": "DEBIT",
                        "amount_sats": amount_sats,
                        "source_id": contribution.id,
                    }
                ]
                if impact_sats:
                    ledger_entries.append(
                        {
                            "account": "IMPACT_FUND_AVAILABLE",
                            "direction": "CREDIT",
                            "amount_sats": impact_sats,
                            "source_id": contribution.id,
                        }
                    )
                if liquidity_sats:
                    ledger_entries.append(
                        {
                            "account": "LIQUIDITY_CAPITAL_PRINCIPAL",
                            "direction": "CREDIT",
                            "amount_sats": liquidity_sats,
                            "source_id": contribution.id,
                        }
                    )
                ledger_id = self._add_ledger_transaction(
                    session,
                    event_type="ContributionAllocated",
                    reference_id=f"donor-contribution:{contribution.id}",
                    mode=mode,
                    entries=ledger_entries,
                )
                receipt = ContributionReceipt(
                    id=str(uuid.uuid4()),
                    contribution_id=contribution.id,
                    ledger_transaction_id=ledger_id,
                    receipt_number=f"BJ-DONOR-SBX-{contribution.id}",
                    total_sats=amount_sats,
                    impact_sats=impact_sats,
                    liquidity_sats=liquidity_sats,
                    mode=mode,
                    issued_at=now,
                )
                session.add(receipt)
                session.add(
                    AuditEvent(
                        event_id=str(uuid.uuid4()),
                        actor_id=user.id,
                        action="DONOR_CONTRIBUTION_ALLOCATED",
                        aggregate_type="Contribution",
                        aggregate_id=contribution.id,
                        occurred_at=now,
                        details={
                            "impact_percentage_bps": impact_percentage_bps,
                            "liquidity_percentage_bps": liquidity_percentage_bps,
                            "mode": mode,
                        },
                    )
                )
                session.add(
                    OutboxEvent(
                        event_id=str(uuid.uuid4()),
                        event_type="ContributionAllocated",
                        version=1,
                        aggregate_id=contribution.id,
                        occurred_at=now,
                        payload={"contribution_id": contribution.id, "mode": mode},
                        attempts=0,
                    )
                )
                session.flush()
                result = {
                    "contribution": self._contribution_dict(contribution),
                    "allocations": [
                        self._contribution_allocation_dict(item) for item in allocations
                    ],
                    "receipt": self._contribution_receipt_dict(receipt),
                }
            return result
        except IntegrityError:
            with self.sessions() as session:
                repeated = session.scalar(
                    select(Contribution).where(Contribution.idempotency_key == idempotency_key)
                )
                if not repeated:
                    raise
                profile = session.get(DonorProfile, repeated.donor_profile_id)
                owner_pubkey = session.scalar(
                    select(User.nostr_pubkey).where(User.id == profile.user_id)
                )
                if owner_pubkey != normalized_pubkey:
                    raise IdempotencyConflict(
                        "idempotency key belongs to another donor"
                    ) from None
                return self._donor_contribution_bundle(session, repeated)

    def list_donor_contributions(self, pubkey: str) -> list[dict[str, Any]]:
        normalized_pubkey = normalize_nostr_pubkey(pubkey)
        if not self.has_any_role(normalized_pubkey, {"DONOR"}):
            raise PermissionError("DONOR role is required")
        with self.sessions() as session:
            contributions = session.scalars(
                select(Contribution)
                .join(DonorProfile, DonorProfile.id == Contribution.donor_profile_id)
                .join(User, User.id == DonorProfile.user_id)
                .where(User.nostr_pubkey == normalized_pubkey)
                .order_by(Contribution.created_at.desc(), Contribution.id.desc())
            ).all()
            return [self._donor_contribution_bundle(session, item) for item in contributions]

    def get_donor_dashboard(self, pubkey: str) -> dict[str, Any]:
        items = self.list_donor_contributions(pubkey)
        impact = sum(item["receipt"]["impact_sats"] for item in items)
        liquidity = sum(item["receipt"]["liquidity_sats"] for item in items)
        modes = {item["contribution"]["mode"] for item in items}
        return {
            "mode": modes.pop() if len(modes) == 1 else ("SANDBOX" if not modes else "MIXED"),
            "impact_fund_sats": impact,
            "liquidity_principal_sats": liquidity,
            "contribution_count": len(items),
        }

    def post_ledger_transaction(
        self,
        event_type: str,
        reference_id: str,
        mode: str,
        entries: Iterable[dict[str, Any]],
    ) -> str:
        with self.sessions.begin() as session:
            return self._add_ledger_transaction(
                session,
                event_type=event_type,
                reference_id=reference_id,
                mode=mode,
                entries=entries,
            )

    @staticmethod
    def _add_ledger_transaction(
        session: Session,
        *,
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
    def _normalize_invoice_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
        if metadata is None:
            return {}
        if not isinstance(metadata, dict):
            raise ValueError("invoice_metadata must be an object")
        normalized: dict[str, Any] = {}
        for name in ("invoice_hash", "payment_hash"):
            value = metadata.get(name)
            if value is None:
                continue
            candidate = str(value).strip().lower()
            if not re.fullmatch(r"[0-9a-f]{64}", candidate):
                raise ValueError(f"{name} must be 64 hexadecimal characters")
            normalized[name] = candidate
        network = metadata.get("network")
        if network is not None:
            candidate = str(network).strip().lower()
            if candidate not in {"regtest", "testnet", "signet", "mainnet"}:
                raise ValueError("invoice network is invalid")
            normalized["network"] = candidate
        amount_sats = metadata.get("amount_sats")
        if amount_sats is not None:
            if isinstance(amount_sats, bool) or not isinstance(amount_sats, int) or amount_sats <= 0:
                raise ValueError("invoice amount must be a positive integer")
            normalized["amount_sats"] = amount_sats
        expires_at = metadata.get("expires_at")
        if expires_at is not None:
            if not isinstance(expires_at, datetime) or expires_at.tzinfo is None:
                raise ValueError("invoice expires_at must be timezone-aware")
            if expires_at <= datetime.now(timezone.utc):
                raise ValueError("invoice is expired")
            normalized["expires_at"] = expires_at
        return normalized

    @staticmethod
    def _provider_event_hash(provider: str, event_id: str, attempt_id: str, outcome: str) -> str:
        return hashlib.sha256(
            f"{provider}:{event_id}:{attempt_id}:{outcome}".encode()
        ).hexdigest()

    @staticmethod
    def _ensure_user(session: Session, pubkey: str) -> str:
        normalized_pubkey = normalize_nostr_pubkey(pubkey)
        user_id = str(uuid.uuid4())
        session.execute(
            pg_insert(User)
            .values(id=user_id, nostr_pubkey=normalized_pubkey)
            .on_conflict_do_nothing(index_elements=[User.nostr_pubkey])
        )
        stored_user_id = session.scalar(
            select(User.id).where(User.nostr_pubkey == normalized_pubkey)
        )
        session.execute(
            text("SELECT bluejet_ensure_participant_role(:user_id)"),
            {"user_id": stored_user_id},
        )
        return stored_user_id

    @staticmethod
    def _user_role_dict(grant: UserRole, pubkey: str) -> dict[str, Any]:
        return {
            "id": grant.id,
            "pubkey": pubkey,
            "role": grant.role,
            "granted_at": grant.granted_at.isoformat(),
            "revoked_at": grant.revoked_at.isoformat() if grant.revoked_at else None,
        }

    @staticmethod
    def _company_membership_dict(
        membership: CompanyMembership, pubkey: str
    ) -> dict[str, Any]:
        return {
            "id": membership.id,
            "company_id": membership.company_id,
            "pubkey": pubkey,
            "membership_role": membership.membership_role,
            "created_at": membership.created_at.isoformat(),
            "revoked_at": (
                membership.revoked_at.isoformat() if membership.revoked_at else None
            ),
        }

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
            "payment_hash": attempt.payment_hash,
            "invoice_network": attempt.invoice_network,
            "invoice_amount_sats": attempt.invoice_amount_sats,
            "invoice_expires_at": attempt.invoice_expires_at.isoformat() if attempt.invoice_expires_at else None,
            "status": attempt.status,
            "mode": attempt.mode,
            "failure_code": attempt.failure_code,
        }

    @staticmethod
    def _payment_receipt_dict(receipt: PaymentReceipt) -> dict[str, Any]:
        return {
            "id": receipt.id,
            "receipt_number": receipt.receipt_number,
            "payment_obligation_id": receipt.payment_obligation_id,
            "payout_attempt_id": receipt.payout_attempt_id,
            "assignment_id": receipt.assignment_id,
            "amount_sats": receipt.amount_sats,
            "status": receipt.status,
            "mode": receipt.mode,
            "issued_at": receipt.issued_at.isoformat(),
        }

    @staticmethod
    def _contribution_dict(contribution: Contribution) -> dict[str, Any]:
        return {
            "id": contribution.id,
            "input_amount_sats": contribution.input_amount_sats,
            "input_currency": contribution.input_currency,
            "terms_version": contribution.terms_version,
            "status": contribution.status,
            "mode": contribution.mode,
            "created_at": contribution.created_at.isoformat(),
        }

    @staticmethod
    def _contribution_allocation_dict(
        allocation: ContributionAllocation,
    ) -> dict[str, Any]:
        return {
            "id": allocation.id,
            "allocation_type": allocation.allocation_type,
            "amount_sats": allocation.amount_sats,
            "percentage_bps": allocation.percentage_bps,
            "status": allocation.status,
        }

    @staticmethod
    def _contribution_receipt_dict(receipt: ContributionReceipt) -> dict[str, Any]:
        return {
            "id": receipt.id,
            "receipt_number": receipt.receipt_number,
            "contribution_id": receipt.contribution_id,
            "total_sats": receipt.total_sats,
            "impact_sats": receipt.impact_sats,
            "liquidity_sats": receipt.liquidity_sats,
            "mode": receipt.mode,
            "issued_at": receipt.issued_at.isoformat(),
        }

    @classmethod
    def _donor_contribution_bundle(
        cls, session: Session, contribution: Contribution
    ) -> dict[str, Any]:
        allocations = session.scalars(
            select(ContributionAllocation)
            .where(ContributionAllocation.contribution_id == contribution.id)
            .order_by(ContributionAllocation.allocation_type)
        ).all()
        receipt = session.scalar(
            select(ContributionReceipt).where(
                ContributionReceipt.contribution_id == contribution.id
            )
        )
        return {
            "contribution": cls._contribution_dict(contribution),
            "allocations": [cls._contribution_allocation_dict(item) for item in allocations],
            "receipt": cls._contribution_receipt_dict(receipt),
        }

    @staticmethod
    def _company_dict(company: Company) -> dict[str, Any]:
        return {
            "id": company.id,
            "name": company.name,
            "description": company.description,
            "created_at": company.created_at.isoformat(),
        }

    @staticmethod
    def _paid_task_dict(task: PaidTask, funded_sats: int) -> dict[str, Any]:
        return {
            "id": task.id,
            "company_id": task.company_id,
            "title": task.title,
            "instructions": task.instructions,
            "module_id": task.module_id,
            "reward_sats": task.reward_sats,
            "slots": task.slots,
            "status": task.status,
            "funded_sats": funded_sats,
            "created_at": task.created_at.isoformat(),
            "published_at": task.published_at.isoformat() if task.published_at else None,
        }

    @staticmethod
    def _assignment_dict(
        assignment: Assignment,
        reservation: AssignmentReservation,
        pubkey: str,
    ) -> dict[str, Any]:
        return {
            "id": assignment.id,
            "task_id": assignment.task_id,
            "pubkey": pubkey,
            "status": assignment.status,
            "reservation_id": reservation.id,
            "reservation_status": reservation.status,
            "reserved_until": reservation.reserved_until.isoformat(),
            "created_at": assignment.created_at.isoformat(),
            "submitted_at": assignment.submitted_at.isoformat() if assignment.submitted_at else None,
        }

    @staticmethod
    def _stored_object_dict(stored: StoredObject) -> dict[str, Any]:
        return {
            "id": stored.id,
            "upload_id": stored.id,
            "storage_key": stored.storage_key,
            "filename": stored.filename,
            "mime_type": stored.mime_type,
            "size": stored.size_bytes,
            "content_hash": stored.content_hash,
            "private": stored.private,
            "scan_status": stored.scan_status,
            "created_at": stored.created_at.isoformat(),
        }

    @staticmethod
    def _submission_draft_dict(draft: SubmissionDraft) -> dict[str, Any]:
        return {
            "id": draft.id,
            "assignment_id": draft.assignment_id,
            "content": draft.content,
            "filename": draft.filename,
            "mime_type": draft.mime_type,
            "status": "DRAFT",
            "private": draft.private,
            "updated_at": draft.updated_at.isoformat(),
        }

    @staticmethod
    def _submission_dict(submission: Submission) -> dict[str, Any]:
        return {
            "id": submission.id,
            "assignment_id": submission.assignment_id,
            "version": submission.version,
            "content_hash": submission.content_hash,
            "stored_object_id": submission.stored_object_id,
            "private": submission.private,
            "submitted_at": submission.submitted_at.isoformat(),
        }

    @staticmethod
    def _review_dict(review: Review) -> dict[str, Any]:
        return {
            "id": review.id,
            "submission_id": review.submission_id,
            "assignment_id": review.assignment_id,
            "decision": review.decision,
            "reason": review.reason,
            "previous_status": review.previous_status,
            "new_status": review.new_status,
            "created_at": review.created_at.isoformat(),
        }

    @staticmethod
    def _opportunity_listing_dict(
        listing: OpportunityListing, author_pubkey: str
    ) -> dict[str, Any]:
        return {
            "id": listing.id,
            "type": "EXTERNAL_OPPORTUNITY",
            "title": listing.title,
            "category": listing.category,
            "description": listing.description,
            "organization_name": listing.organization_name,
            "external_url": listing.external_url,
            "format": listing.format,
            "location": listing.location,
            "starts_at": listing.starts_at.isoformat() if listing.starts_at else None,
            "application_deadline": (
                listing.application_deadline.isoformat() if listing.application_deadline else None
            ),
            "tags": list(listing.tags or []),
            "requirements": listing.requirements,
            "non_remunerated_ack": listing.non_remunerated_ack,
            "moderation_status": listing.moderation_status,
            "status": listing.status,
            "publisher_pubkey": author_pubkey,
            "shared_by_pubkey": author_pubkey,
            "remunerated": False,
            "created_at": listing.created_at.isoformat(),
        }

    @staticmethod
    def _community_post_dict(
        post: CommunityPostReference, author_pubkey: str
    ) -> dict[str, Any]:
        return {
            "id": post.id,
            "nostr_event_id": post.nostr_event_id,
            "author_pubkey": author_pubkey,
            "category": post.category,
            "content": post.content,
            "moderation_status": post.moderation_status,
            "relay_status": post.relay_status,
            "mode": post.mode,
            "delivery": "LOCAL_ONLY",
            "created_at": post.created_at.isoformat(),
            "public_warning": "Conteúdo armazenado localmente; relays Nostr estão desabilitados.",
        }

    @staticmethod
    def _learning_enrollment_dict(enrollment: LearningEnrollment) -> dict[str, Any]:
        return {
            "id": enrollment.id,
            "course_id": enrollment.course_id,
            "course_version": enrollment.course_version,
            "status": enrollment.status,
            "progress": enrollment.progress,
            "attempt_count": enrollment.attempt_count,
            "started_at": enrollment.started_at.isoformat(),
            "completed_at": enrollment.completed_at.isoformat() if enrollment.completed_at else None,
        }

    @staticmethod
    def _quiz_attempt_dict(attempt: QuizAttempt) -> dict[str, Any]:
        return {
            "id": attempt.id,
            "enrollment_id": attempt.enrollment_id,
            "module_id": attempt.module_id,
            "assessment_version": attempt.assessment_version,
            "score": attempt.score,
            "attempt_number": attempt.attempt_number,
            "created_at": attempt.created_at.isoformat(),
        }

    @staticmethod
    def _skill_evidence_dict(evidence: SkillEvidence) -> dict[str, Any]:
        return {
            "id": evidence.id,
            "module_id": evidence.module_id,
            "assessment_version": evidence.assessment_version,
            "score": evidence.score,
            "quiz_attempt_id": evidence.quiz_attempt_id,
            "created_at": evidence.created_at.isoformat(),
        }

    @staticmethod
    def _learning_note_dict(note: LearningNote) -> dict[str, Any]:
        return {
            "id": note.id,
            "course_id": note.course_id,
            "lesson_id": note.lesson_id,
            "content": note.content,
            "updated_at": note.updated_at.isoformat(),
        }

    @staticmethod
    def _learning_activity_dict(submission: LearningActivitySubmission) -> dict[str, Any]:
        return {
            "id": submission.id,
            "course_id": submission.course_id,
            "activity_id": submission.activity_id,
            "content": submission.content,
            "status": submission.status,
            "created_at": submission.created_at.isoformat(),
        }

    @staticmethod
    def _badge_publication_dict(
        publication: BadgePublication,
        evidence_id: str,
        badge_definition_id: str,
    ) -> dict[str, Any]:
        return {
            "id": publication.id,
            "consent_id": publication.consent_id,
            "skill_evidence_id": evidence_id,
            "badge_definition_id": badge_definition_id,
            "status": publication.status,
            "mode": publication.mode,
            "nostr_event_id": publication.nostr_event_id,
            "relays": publication.relays,
            "acknowledged_relays": publication.acknowledged_relays,
            "requested_at": publication.requested_at.isoformat(),
            "notice": "Publicação Nostr real requer autorização S3 específica.",
        }

    @staticmethod
    def _onboarding_dict(draft: OnboardingDraft) -> dict[str, Any]:
        return {"id": draft.id, "status": draft.status, **draft.data}

    @staticmethod
    def _outbox_dict(event: OutboxEvent) -> dict[str, Any]:
        return {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "version": event.version,
            "aggregate_id": event.aggregate_id,
            "occurred_at": event.occurred_at.isoformat(),
            "payload": event.payload,
            "attempts": event.attempts,
        }
