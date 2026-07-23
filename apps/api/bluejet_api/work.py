from datetime import datetime, timedelta, timezone
import hashlib
import uuid


class WorkService:
    def __init__(self):
        self.companies = {}
        self.tasks = {}
        self.funding = {}
        self.assignments = {}
        self.submissions = []
        self.submission_drafts = {}
        self.applications = {}
        self.drafts = {}

    def company(self, name, description=""):
        value = {"id": uuid.uuid4().hex, "name": name, "description": description}
        self.companies[value["id"]] = value
        return value

    def task(self, company_id, title, instructions, reward_sats, module_id="bluejet-basics-quiz"):
        if company_id not in self.companies or reward_sats <= 0:
            raise ValueError("invalid company or reward")
        value = {"id": uuid.uuid4().hex, "company_id": company_id, "title": title,
                 "instructions": instructions, "reward_sats": reward_sats, "module_id": module_id,
                 "status": "DRAFT", "slots": 1, "funded_sats": 0, "reserved_until": None}
        self.tasks[value["id"]] = value
        return value

    def fund(self, task_id, amount_sats):
        task = self.tasks[task_id]
        if amount_sats != task["reward_sats"]:
            raise ValueError("funding must equal the task reward")
        reservation = {"id": uuid.uuid4().hex, "task_id": task_id, "amount_sats": amount_sats, "status": "RESERVED"}
        self.funding[reservation["id"]] = reservation
        task["funded_sats"] = amount_sats
        return reservation

    def publish(self, task_id):
        task = self.tasks[task_id]
        if task["funded_sats"] != task["reward_sats"]:
            raise ValueError("task is not fully funded")
        task["status"] = "PUBLISHED"
        return task

    def reserve(self, task_id, pubkey, eligible):
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

    def submit(self, assignment_id, pubkey, content, filename, mime_type):
        assignment = self.assignments.get(assignment_id)
        if not assignment or assignment["pubkey"] != pubkey or assignment["status"] != "RESERVED":
            raise ValueError("assignment not owned by participant")
        if any(s["assignment_id"] == assignment_id for s in self.submissions):
            raise ValueError("assignment already submitted")
        if assignment["reserved_until"] <= datetime.now(timezone.utc):
            assignment["status"] = "EXPIRED"
            raise ValueError("reservation expired")
        if mime_type not in {"image/png", "image/jpeg", "application/pdf", "video/mp4"} or len(content.encode()) > 10 * 1024 * 1024:
            raise ValueError("unsupported or oversized upload")
        item = {"id": uuid.uuid4().hex, "assignment_id": assignment_id, "filename": filename,
                "mime_type": mime_type, "content_hash": hashlib.sha256(content.encode()).hexdigest(),
                "private": True, "submitted_at": datetime.now(timezone.utc).isoformat()}
        self.submissions.append(item)
        assignment["status"] = "SUBMITTED"
        return item

    def save_submission_draft(self, assignment_id, pubkey, content, filename="submission.txt", mime_type="text/plain"):
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
