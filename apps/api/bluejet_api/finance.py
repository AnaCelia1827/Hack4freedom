from datetime import datetime, timezone
import hashlib
import uuid


class SandboxLightningGateway:
    """Deterministic local validator; this is deliberately not a BOLT11 decoder."""

    mode = "SANDBOX"

    def validate_invoice(self, invoice: str, expected_sats: int) -> dict:
        if not isinstance(invoice, str) or not invoice.strip():
            raise ValueError("invoice is required")
        parts = invoice.strip().split(":")
        if len(parts) != 5 or parts[0] != "lnsbx":
            raise ValueError("SANDBOX invoice must use lnsbx:network:amount:expires:payment_hash")
        _, network, amount_text, expires_text, payment_hash = parts
        if network not in {"regtest", "testnet", "signet"}:
            raise ValueError("SANDBOX invoice network is invalid")
        try:
            amount_sats = int(amount_text)
            expires_at = datetime.fromtimestamp(int(expires_text), tz=timezone.utc)
        except (ValueError, OverflowError):
            raise ValueError("SANDBOX invoice amount or expiry is invalid") from None
        if amount_sats != expected_sats:
            raise ValueError("invoice amount does not match obligation")
        if expires_at <= datetime.now(timezone.utc):
            raise ValueError("invoice is expired")
        normalized_payment_hash = payment_hash.strip().lower()
        if len(normalized_payment_hash) != 64 or any(
            character not in "0123456789abcdef" for character in normalized_payment_hash
        ):
            raise ValueError("payment_hash must be 64 hexadecimal characters")
        return {
            "invoice_hash": hashlib.sha256(invoice.strip().encode()).hexdigest(),
            "payment_hash": normalized_payment_hash,
            "network": network,
            "amount_sats": amount_sats,
            "expires_at": expires_at,
        }


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

    def attempt(self, obligation_id, invoice_metadata, idempotency_key):
        existing = next((a for a in self.attempts.values() if a["obligation_id"] == obligation_id and a["status"] in {"CREATED", "VALIDATED", "PROCESSING", "AMBIGUOUS"}), None)
        if existing:
            if existing["idempotency_key"] == idempotency_key: return existing
            raise RuntimeError("active payout attempt exists")
        obligation = next(o for o in self.obligations.values() if o["id"] == obligation_id)
        obligation["status"] = "CLEARING"
        item = {
            "id": uuid.uuid4().hex,
            "obligation_id": obligation_id,
            "invoice_hash": invoice_metadata.get("invoice_hash"),
            "payment_hash": invoice_metadata.get("payment_hash"),
            "invoice_network": invoice_metadata.get("network"),
            "invoice_amount_sats": invoice_metadata.get("amount_sats"),
            "idempotency_key": idempotency_key,
            "status": "VALIDATED",
            "mode": "SANDBOX",
        }
        self.attempts[item["id"]] = item
        return item

    def settle(self, attempt_id):
        attempt = self.attempts[attempt_id]; attempt["status"] = "SETTLED"
        obligation = next(o for o in self.obligations.values() if o["id"] == attempt["obligation_id"]); obligation["status"] = "SETTLED"
        receipt = {"id": uuid.uuid4().hex, "attempt_id": attempt_id, "amount_sats": obligation["amount_sats"], "mode": attempt["mode"]}
        self.receipts[receipt["id"]] = receipt
        return receipt
