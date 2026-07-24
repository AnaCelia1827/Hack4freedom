"""Learning domain with deterministic assessment and pluggable persistence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Protocol
import uuid


@dataclass(frozen=True)
class Course:
    id: str
    version: str
    title: str
    objective: str
    duration_minutes: int
    module_id: str
    assessment_version: str
    questions: tuple[dict, ...]

    @property
    def modules(self):
        lesson = {
            "id": "bluejet-basics-lesson",
            "title": "Evidências e entrega",
            "order": 1,
            "activity_ids": ["bluejet-basics-activity"],
        }
        return [{"id": self.module_id, "title": "Primeiro módulo", "order": 1, "lessons": [lesson]}]


class LearningStore(Protocol):
    def enroll_learning(self, pubkey: str, course_id: str, course_version: str) -> dict: ...

    def list_learning_enrollments(self, pubkey: str) -> list[dict]: ...

    def record_quiz_attempt(
        self,
        pubkey: str,
        course_id: str,
        course_version: str,
        module_id: str,
        assessment_version: str,
        score: int,
        answers_hash: str,
    ) -> tuple[dict, dict | None]: ...

    def list_skill_evidence(self, pubkey: str) -> list[dict]: ...

    def save_learning_note(
        self, pubkey: str, course_id: str, lesson_id: str, content: str
    ) -> dict: ...

    def get_learning_note(self, pubkey: str, course_id: str, lesson_id: str) -> dict: ...

    def submit_learning_activity(
        self, pubkey: str, course_id: str, activity_id: str, content: str
    ) -> dict: ...

    def consent_badge_publication(
        self, pubkey: str, evidence_id: str, badge_definition: dict
    ) -> dict: ...

    def get_badge_publication(self, pubkey: str, evidence_id: str) -> dict | None: ...


class MemoryLearningStore:
    """Explicit fallback for local development without DATABASE_URL."""

    def __init__(self):
        self.enrollments: dict[tuple[str, str, str], dict] = {}
        self.attempts: list[dict] = []
        self.evidence: dict[tuple[str, str, str], dict] = {}
        self.activity_submissions: dict[tuple[str, str, str], dict] = {}
        self.notes: dict[tuple[str, str, str], dict] = {}
        self.outbox: list[dict] = []
        self.badge_definitions: dict[str, dict] = {}
        self.badge_consents: dict[tuple[str, str, str], dict] = {}
        self.badge_publications: dict[str, dict] = {}

    def enroll_learning(self, pubkey: str, course_id: str, course_version: str) -> dict:
        key = (pubkey, course_id, course_version)
        self.enrollments.setdefault(
            key,
            {
                "id": uuid.uuid4().hex,
                "course_id": course_id,
                "course_version": course_version,
                "status": "IN_PROGRESS",
                "progress": 0,
                "attempt_count": 0,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
            },
        )
        return dict(self.enrollments[key])

    def list_learning_enrollments(self, pubkey: str) -> list[dict]:
        return [
            dict(enrollment)
            for (owner_pubkey, _, _), enrollment in self.enrollments.items()
            if owner_pubkey == pubkey
        ]

    def record_quiz_attempt(
        self,
        pubkey: str,
        course_id: str,
        course_version: str,
        module_id: str,
        assessment_version: str,
        score: int,
        answers_hash: str,
    ) -> tuple[dict, dict | None]:
        enrollment = self.enroll_learning(pubkey, course_id, course_version)
        key = (pubkey, course_id, course_version)
        stored_enrollment = self.enrollments[key]
        now = datetime.now(timezone.utc)
        attempt = {
            "id": uuid.uuid4().hex,
            "enrollment_id": enrollment["id"],
            "module_id": module_id,
            "assessment_version": assessment_version,
            "score": score,
            "attempt_number": stored_enrollment["attempt_count"] + 1,
            "created_at": now.isoformat(),
        }
        self.attempts.append(attempt)
        stored_enrollment["attempt_count"] = attempt["attempt_number"]
        stored_enrollment["progress"] = 100 if score >= 80 else max(stored_enrollment["progress"], 50)
        if score >= 80:
            stored_enrollment["status"] = "COMPLETED"
            stored_enrollment["completed_at"] = stored_enrollment["completed_at"] or now.isoformat()
            evidence_key = (pubkey, module_id, assessment_version)
            if evidence_key not in self.evidence:
                self.evidence[evidence_key] = {
                    "id": uuid.uuid4().hex,
                    "module_id": module_id,
                    "score": score,
                    "assessment_version": assessment_version,
                    "quiz_attempt_id": attempt["id"],
                    "created_at": now.isoformat(),
                }
                self.outbox.extend(
                    [
                        {"type": "QuizPassed", "aggregate_id": attempt["id"]},
                        {"type": "SkillEvidenceCreated", "aggregate_id": self.evidence[evidence_key]["id"]},
                    ]
                )
        return dict(attempt), dict(self.evidence.get((pubkey, module_id, assessment_version))) if (pubkey, module_id, assessment_version) in self.evidence else None

    def list_skill_evidence(self, pubkey: str) -> list[dict]:
        return [dict(value) for key, value in self.evidence.items() if key[0] == pubkey]

    def save_learning_note(self, pubkey: str, course_id: str, lesson_id: str, content: str) -> dict:
        key = (pubkey, course_id, lesson_id)
        item = self.notes.setdefault(
            key,
            {"id": uuid.uuid4().hex, "course_id": course_id, "lesson_id": lesson_id},
        )
        item["content"] = content
        item["updated_at"] = datetime.now(timezone.utc).isoformat()
        return dict(item)

    def get_learning_note(self, pubkey: str, course_id: str, lesson_id: str) -> dict:
        return dict(self.notes.get((pubkey, course_id, lesson_id), {"content": ""}))

    def submit_learning_activity(
        self, pubkey: str, course_id: str, activity_id: str, content: str
    ) -> dict:
        key = (pubkey, course_id, activity_id)
        if key in self.activity_submissions:
            raise ValueError("activity already submitted")
        item = {
            "id": uuid.uuid4().hex,
            "course_id": course_id,
            "activity_id": activity_id,
            "content": content,
            "status": "SUBMITTED",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.activity_submissions[key] = item
        return dict(item)

    def consent_badge_publication(
        self, pubkey: str, evidence_id: str, badge_definition: dict
    ) -> dict:
        evidence = next(
            (item for item in self.list_skill_evidence(pubkey) if item["id"] == evidence_id),
            None,
        )
        if not evidence:
            raise ValueError("skill evidence not found")
        definition = dict(badge_definition)
        self.badge_definitions.setdefault(definition["id"], definition)
        consent_key = (pubkey, evidence_id, definition["id"])
        consent = self.badge_consents.setdefault(
            consent_key,
            {
                "id": uuid.uuid4().hex,
                "skill_evidence_id": evidence_id,
                "badge_definition_id": definition["id"],
                "consented_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        publication = self.badge_publications.get(consent["id"])
        if publication is None:
            publication = {
                "id": uuid.uuid4().hex,
                "consent_id": consent["id"],
                "skill_evidence_id": evidence_id,
                "badge_definition_id": definition["id"],
                "status": "PUBLISH_PENDING",
                "mode": "SANDBOX",
                "nostr_event_id": None,
                "relays": [],
                "acknowledged_relays": [],
                "requested_at": datetime.now(timezone.utc).isoformat(),
                "notice": "Publicação Nostr real requer autorização S3 específica.",
            }
            self.badge_publications[consent["id"]] = publication
            self.outbox.append(
                {
                    "type": "BadgePublicationRequested",
                    "aggregate_id": publication["id"],
                    "mode": "SANDBOX",
                }
            )
        return dict(publication)

    def get_badge_publication(self, pubkey: str, evidence_id: str) -> dict | None:
        consent = next(
            (
                item
                for (owner, stored_evidence_id, _), item in self.badge_consents.items()
                if owner == pubkey and stored_evidence_id == evidence_id
            ),
            None,
        )
        return dict(self.badge_publications[consent["id"]]) if consent else None


class LearningService:
    def __init__(self, store: LearningStore | None = None):
        self.course = Course(
            "bluejet-basics",
            "v1",
            "Primeiros passos profissionais",
            "Comprovar uma competência prática",
            20,
            "bluejet-basics-quiz",
            "v1",
            (
                {"id": "q1", "prompt": "Qual é o primeiro passo?", "answer": "planejar"},
                {"id": "q2", "prompt": "Como registrar a entrega?", "answer": "evidencia"},
                {"id": "q3", "prompt": "Quem aprova o trabalho?", "answer": "revisor"},
                {"id": "q4", "prompt": "Qual é a nota mínima?", "answer": "80"},
                {"id": "q5", "prompt": "O que a evidence comprova?", "answer": "competencia"},
            ),
        )
        self.store = store or MemoryLearningStore()
        self.badge_definition = {
            "id": "bluejet-basics-v1",
            "identifier": "bluejet-basics-v1",
            "name": "Primeiros passos profissionais",
            "description": "Conclusão da trilha Primeiros passos profissionais.",
            "mode": "SANDBOX",
        }

    def enroll(self, pubkey: str) -> dict:
        return self.store.enroll_learning(pubkey, self.course.id, self.course.version)

    def list_enrollments(self, pubkey: str) -> list[dict]:
        return self.store.list_learning_enrollments(pubkey)

    def submit(self, pubkey: str, answers: dict) -> tuple[dict, dict | None]:
        normalized_answers = answers if isinstance(answers, dict) else {}
        expected = {question["id"]: question["answer"] for question in self.course.questions}
        correct = sum(normalized_answers.get(question_id) == answer for question_id, answer in expected.items())
        score = correct * 100 // len(expected)
        answers_hash = hashlib.sha256(
            json.dumps(normalized_answers, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return self.store.record_quiz_attempt(
            pubkey,
            self.course.id,
            self.course.version,
            self.course.module_id,
            self.course.assessment_version,
            score,
            answers_hash,
        )

    def list_evidence(self, pubkey: str) -> list[dict]:
        return self.store.list_skill_evidence(pubkey)

    def has_evidence(self, pubkey: str) -> bool:
        return any(
            evidence["module_id"] == self.course.module_id
            and evidence["assessment_version"] == self.course.assessment_version
            for evidence in self.list_evidence(pubkey)
        )

    def consent_badge(self, pubkey: str, evidence_id: str) -> dict:
        return self.store.consent_badge_publication(
            pubkey, evidence_id, self.badge_definition
        )

    def badge_publication(self, pubkey: str, evidence_id: str) -> dict | None:
        return self.store.get_badge_publication(pubkey, evidence_id)

    def submit_activity(self, pubkey: str, course_id: str, activity_id: str, content: str) -> dict:
        return self.store.submit_learning_activity(pubkey, course_id, activity_id, content)

    def save_note(self, pubkey: str, course_id: str, lesson_id: str, content: str) -> dict:
        return self.store.save_learning_note(pubkey, course_id, lesson_id, content)

    def note(self, pubkey: str, course_id: str, lesson_id: str) -> dict:
        return self.store.get_learning_note(pubkey, course_id, lesson_id)
