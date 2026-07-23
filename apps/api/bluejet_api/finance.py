from datetime import datetime, timezone
import uuid


class FinanceService:
    def __init__(self):
        self.reviews = []
        self.obligations = {}
        self.attempts = {}
        self.receipts = {}

    def review(self, submission_id, decision, reason=""):
        if decision in {"REQUEST_CHANGES", "REJECT"} and not reason.strip():
            raise ValueError("justification required")
        review = {"id": uuid.uuid4().hex, "submission_id": submission_id, "decision": decision, "reason": reason, "created_at": datetime.now(timezone.utc).isoformat()}
        self.reviews.append(review)
        return review

    def obligation(self, assignment_id, amount_sats):
        return self.obligations.setdefault(assignment_id, {"id": uuid.uuid4().hex, "assignment_id": assignment_id, "amount_sats": amount_sats, "status": "OPEN"})

    def attempt(self, obligation_id, invoice, idempotency_key):
        existing = next((a for a in self.attempts.values() if a["obligation_id"] == obligation_id and a["status"] in {"CREATED", "VALIDATED", "PROCESSING", "AMBIGUOUS"}), None)
        if existing:
            if existing["idempotency_key"] == idempotency_key: return existing
            raise RuntimeError("active payout attempt exists")
        obligation = next(o for o in self.obligations.values() if o["id"] == obligation_id)
        obligation["status"] = "CLEARING"
        item = {"id": uuid.uuid4().hex, "obligation_id": obligation_id, "invoice": invoice, "idempotency_key": idempotency_key, "status": "VALIDATED", "mode": "MOCK"}
        self.attempts[item["id"]] = item
        return item

    def settle(self, attempt_id):
        attempt = self.attempts[attempt_id]; attempt["status"] = "SETTLED"
        obligation = next(o for o in self.obligations.values() if o["id"] == attempt["obligation_id"]); obligation["status"] = "SETTLED"
        receipt = {"id": uuid.uuid4().hex, "attempt_id": attempt_id, "amount_sats": obligation["amount_sats"], "mode": attempt["mode"]}
        self.receipts[receipt["id"]] = receipt
        return receipt
