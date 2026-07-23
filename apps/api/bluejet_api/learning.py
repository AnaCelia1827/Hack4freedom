from dataclasses import dataclass
from datetime import datetime, timezone
import uuid


@dataclass(frozen=True)
class Course:
    id: str
    title: str
    objective: str
    duration_minutes: int
    module_id: str
    assessment_version: str
    questions: tuple[dict, ...]

    @property
    def modules(self):
        lesson = {"id": "bluejet-basics-lesson", "title": "Evidências e entrega", "order": 1,
                  "activity_ids": ["bluejet-basics-activity"]}
        return [{"id": self.module_id, "title": "Primeiro módulo", "order": 1, "lessons": [lesson]}]


class LearningService:
    def __init__(self):
        self.course = Course(
            "bluejet-basics", "Primeiros passos profissionais", "Comprovar uma competência prática", 20,
            "bluejet-basics-quiz", "v1",
            ({"id": "q1", "prompt": "Qual é o primeiro passo?", "answer": "planejar"},
             {"id": "q2", "prompt": "Como registrar a entrega?", "answer": "evidencia"},
             {"id": "q3", "prompt": "Quem aprova o trabalho?", "answer": "revisor"},
             {"id": "q4", "prompt": "Qual é a nota mínima?", "answer": "80"},
             {"id": "q5", "prompt": "O que a evidence comprova?", "answer": "competencia"})
        )
        self.enrollments = {}
        self.attempts = []
        self.evidence = {}
        self.badges = {}
        self.outbox = []
        self.activity_submissions = {}
        self.notes = {}

    def enroll(self, pubkey):
        self.enrollments.setdefault((pubkey, self.course.id), {"id": uuid.uuid4().hex, "progress": 0})
        return self.enrollments[(pubkey, self.course.id)]

    def submit(self, pubkey, answers):
        enrollment = self.enroll(pubkey)
        expected = {q["id"]: q["answer"] for q in self.course.questions}
        score = round(sum(answers.get(k) == v for k, v in expected.items()) / len(expected) * 100)
        attempt = {"id": uuid.uuid4().hex, "enrollment_id": enrollment["id"], "score": score,
                   "created_at": datetime.now(timezone.utc).isoformat()}
        self.attempts.append(attempt)
        enrollment["progress"] = 100 if score >= 80 else max(enrollment["progress"], 50)
        if score >= 80 and pubkey not in self.evidence:
            self.evidence[pubkey] = {"id": uuid.uuid4().hex, "module_id": self.course.module_id,
                                     "score": score, "assessment_version": self.course.assessment_version}
            self.outbox.append({"type": "SkillEvidenceCreated", "aggregate_id": self.evidence[pubkey]["id"]})
        return attempt, self.evidence.get(pubkey)

    def consent_badge(self, pubkey, evidence_id):
        evidence = self.evidence.get(pubkey)
        if not evidence or evidence["id"] != evidence_id:
            raise ValueError("skill evidence not found")
        badge = self.badges.setdefault(pubkey, {"id": uuid.uuid4().hex, "status": "PUBLISH_PENDING"})
        self.outbox.append({"type": "BadgePublicationRequested", "aggregate_id": badge["id"]})
        return badge

    def submit_activity(self, pubkey, course_id, activity_id, content):
        key = (pubkey, course_id, activity_id)
        if key in self.activity_submissions:
            raise ValueError("activity already submitted")
        item = {"id": uuid.uuid4().hex, "course_id": course_id, "activity_id": activity_id,
                "pubkey": pubkey, "content": content, "status": "SUBMITTED",
                "created_at": datetime.now(timezone.utc).isoformat()}
        self.activity_submissions[key] = item
        return item

    def save_note(self, pubkey, course_id, lesson_id, content):
        key = (pubkey, course_id, lesson_id)
        item = self.notes.setdefault(key, {"id": uuid.uuid4().hex, "pubkey": pubkey, "course_id": course_id, "lesson_id": lesson_id})
        item["content"] = content
        item["updated_at"] = datetime.now(timezone.utc).isoformat()
        return item

    def note(self, pubkey, course_id, lesson_id):
        return self.notes.get((pubkey, course_id, lesson_id), {"content": ""})
