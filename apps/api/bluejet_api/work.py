from datetime import datetime, timedelta, timezone
import hashlib
import uuid


class WorkService:
    def __init__(self, store=None):
        self.store = store
        self.companies = {}
        self.tasks = {}
        self.funding = {}
        self.assignments = {}
        self.submissions = []
        self.submission_drafts = {}
        self.applications = {}
        self.drafts = {}

    def company(self, name, description=""):
        if self.store:
            return self.store.create_company(name, description)
        value = {"id": uuid.uuid4().hex, "name": name, "description": description}
        self.companies[value["id"]] = value
        return value

    def task(self, company_id, title, instructions, reward_sats, module_id="bluejet-basics-quiz"):
        if self.store:
            return self.store.create_paid_task(
                company_id, title, instructions, reward_sats, module_id
            )
        if company_id not in self.companies or reward_sats <= 0:
            raise ValueError("invalid company or reward")
        value = {"id": uuid.uuid4().hex, "company_id": company_id, "title": title,
                 "instructions": instructions, "reward_sats": reward_sats, "module_id": module_id,
                 "status": "DRAFT", "slots": 1, "funded_sats": 0, "reserved_until": None}
        self.tasks[value["id"]] = value
        return value

    def fund(self, task_id, amount_sats, sources=None):
        if self.store:
            return self.store.reserve_task_funding(task_id, amount_sats, sources)
        task = self.tasks[task_id]
        if amount_sats != task["reward_sats"]:
            raise ValueError("funding must equal the task reward")
        reservation = {"id": uuid.uuid4().hex, "task_id": task_id, "amount_sats": amount_sats, "status": "RESERVED"}
        self.funding[reservation["id"]] = reservation
        task["funded_sats"] = amount_sats
        return reservation

    def publish(self, task_id):
        if self.store:
            return self.store.publish_paid_task(task_id)
        task = self.tasks[task_id]
        if task["funded_sats"] != task["reward_sats"]:
            raise ValueError("task is not fully funded")
        task["status"] = "PUBLISHED"
        return task

    def reserve(self, task_id, pubkey, eligible):
        if self.store:
            return self.store.reserve_assignment(task_id, pubkey)
        task = self.tasks[task_id]
        now = datetime.now(timezone.utc)
        if task["status"] != "PUBLISHED" or not eligible:
            raise ValueError("task unavailable or participant ineligible")
        active = [a for a in self.assignments.values() if a["task_id"] == task_id and a["status"] == "RESERVED" and a["reserved_until"] > now]
        if active:
            raise RuntimeError("task already reserved")
        assignment = {"id": uuid.uuid4().hex, "task_id": task_id, "pubkey": pubkey, "status": "RESERVED",
                      "reserved_until": now + timedelta(minutes=60)}
        self.assignments[assignment["id"]] = assignment
        return assignment

    def submit(self, assignment_id, pubkey, content, filename, mime_type, stored_object_id=None):
        if self.store:
            return self.store.create_submission(
                assignment_id, pubkey, content, stored_object_id
            )
        assignment = self.assignments.get(assignment_id)
        if (
            not assignment
            or assignment["pubkey"] != pubkey
            or assignment["status"] not in {"RESERVED", "CHANGES_REQUESTED"}
        ):
            raise ValueError("assignment not owned by participant")
        is_correction = assignment["status"] == "CHANGES_REQUESTED"
        prior_submissions = [s for s in self.submissions if s["assignment_id"] == assignment_id]
        if (not is_correction and prior_submissions) or (is_correction and len(prior_submissions) != 1):
            raise ValueError("assignment already submitted")
        if not is_correction and assignment["reserved_until"] <= datetime.now(timezone.utc):
            assignment["status"] = "EXPIRED"
            raise ValueError("reservation expired")
        if mime_type not in {"image/png", "image/jpeg", "application/pdf", "video/mp4"} or len(content.encode()) > 10 * 1024 * 1024:
            raise ValueError("unsupported or oversized upload")
        item = {"id": uuid.uuid4().hex, "assignment_id": assignment_id, "filename": filename,
                "mime_type": mime_type, "content_hash": hashlib.sha256(content.encode()).hexdigest(),
                "private": True, "version": 2 if is_correction else 1,
                "submitted_at": datetime.now(timezone.utc).isoformat()}
        self.submissions.append(item)
        assignment["status"] = "RESUBMITTED" if is_correction else "SUBMITTED"
        return item

    def upload(self, pubkey, filename, mime_type, size, content_hash):
        if self.store:
            return self.store.create_stored_object(
                pubkey, filename, mime_type, size, content_hash
            )
        if mime_type not in {"image/png", "image/jpeg", "application/pdf", "video/mp4"} or size > 10 * 1024 * 1024:
            raise ValueError("unsupported or oversized upload")
        if len(content_hash) != 64:
            raise ValueError("a SHA-256 content_hash is required")
        return {
            "upload_id": uuid.uuid4().hex,
            "filename": filename,
            "mime_type": mime_type,
            "size": size,
            "content_hash": content_hash,
            "private": True,
            "scan_status": "QUARANTINED",
        }

    def list_tasks(self, pubkey=None, eligible_only=False):
        if self.store:
            return self.store.list_paid_tasks(pubkey, eligible_only)
        return [
            {**task, "eligible": bool(pubkey)}
            for task in self.tasks.values()
            if task["status"] == "PUBLISHED" and (not eligible_only or pubkey)
        ]

    def get_task(self, task_id):
        if self.store:
            return self.store.get_paid_task(task_id)
        return self.tasks.get(task_id)

    def get_company(self, company_id):
        if self.store:
            return self.store.get_company(company_id)
        return self.companies.get(company_id)

    def get_assignment(self, assignment_id):
        if self.store:
            return self.store.get_assignment(assignment_id)
        return self.assignments.get(assignment_id)

    def get_submission(self, submission_id):
        if self.store:
            return self.store.get_submission(submission_id)
        return next((item for item in self.submissions if item["id"] == submission_id), None)

    def pending_submissions(self):
        if self.store:
            return self.store.list_pending_submissions()
        return [item for item in self.submissions if item.get("review_status") != "APPROVED"]

    def approve_assignment(self, assignment_id):
        if self.store:
            raise RuntimeError("approval must use the transactional review operation")
        assignment = self.assignments[assignment_id]
        assignment["status"] = "APPROVED"
        return assignment

    def expire_reservations(self, now=None):
        if self.store:
            return self.store.expire_assignment_reservations(now)
        current = now or datetime.now(timezone.utc)
        expired = 0
        for assignment in self.assignments.values():
            if assignment["status"] == "RESERVED" and assignment["reserved_until"] <= current:
                assignment["status"] = "EXPIRED"
                expired += 1
        return expired

    def save_submission_draft(self, assignment_id, pubkey, content, filename="submission.txt", mime_type="text/plain"):
        if self.store:
            return self.store.save_submission_draft(
                assignment_id, pubkey, content, filename, mime_type
            )
        assignment = self.assignments.get(assignment_id)
        if not assignment or assignment["pubkey"] != pubkey:
            raise ValueError("assignment not owned by participant")
        if assignment["status"] not in {"RESERVED", "SUBMITTED"}:
            raise ValueError("assignment does not accept drafts")
        draft = self.submission_drafts.get(assignment_id, {"id": uuid.uuid4().hex, "assignment_id": assignment_id})
        draft.update({"content": content, "filename": filename, "mime_type": mime_type, "status": "DRAFT", "updated_at": datetime.now(timezone.utc).isoformat(), "private": True})
        self.submission_drafts[assignment_id] = draft
        return draft

    def submission_draft(self, assignment_id, pubkey):
        if self.store:
            return self.store.get_submission_draft(assignment_id, pubkey)
        assignment = self.assignments.get(assignment_id)
        if not assignment or assignment["pubkey"] != pubkey:
            raise ValueError("assignment not owned by participant")
        return self.submission_drafts.get(assignment_id)

    def apply(self, task_id, pubkey, message="", assignment_id=None):
        key = (task_id, pubkey)
        if key in self.applications:
            raise RuntimeError("application already exists")
        if task_id not in self.tasks or self.tasks[task_id]["status"] != "PUBLISHED":
            raise ValueError("task unavailable")
        if assignment_id:
            assignment = self.assignments.get(assignment_id)
            if not assignment or assignment["task_id"] != task_id or assignment["pubkey"] != pubkey or assignment["status"] != "RESERVED":
                raise ValueError("assignment unavailable")
        item = {"id": uuid.uuid4().hex, "task_id": task_id, "assignment_id": assignment_id, "pubkey": pubkey, "message": message, "status": "SUBMITTED"}
        self.applications[key] = item
        return item

    def create_draft(self, owner_pubkey=None):
        value = {
            "id": uuid.uuid4().hex,
            "owner_pubkey": owner_pubkey,
            "title": "",
            "instructions": "",
            "requirements": "",
            "reward_sats": 0,
            "media_name": "",
            "status": "DRAFT",
        }
        self.drafts[value["id"]] = value
        return value

    def update_draft(self, draft_id, changes):
        draft = self.drafts.get(draft_id)
        if not draft or draft["status"] != "DRAFT":
            raise KeyError(draft_id)
        allowed = {"title", "instructions", "requirements", "reward_sats", "media_name"}
        for key, value in changes.items():
            if key in allowed:
                draft[key] = value
        return draft

    def publish_draft(self, draft_id):
        draft = self.drafts.get(draft_id)
        if not draft or draft["status"] != "DRAFT":
            raise KeyError(draft_id)
        if not draft["title"].strip() or not draft["requirements"].strip() or int(draft["reward_sats"] or 0) <= 0:
            raise ValueError("draft is incomplete")
        company = self.company("Organização Bluejet")
        task = self.task(company["id"], draft["title"], draft["instructions"], int(draft["reward_sats"]))
        task["requirements"] = draft["requirements"]
        draft["status"] = "PUBLISHED"
        draft["task_id"] = task["id"]
        return task
