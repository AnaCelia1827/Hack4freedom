"""Nostr challenge/session boundary using public material only."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import secrets
from typing import Callable, Protocol
import uuid


NIP98_AUTH_KIND = 27235
SECP256K1_FIELD = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
SECP256K1_G = (
    0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
    0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,
)


class AuthorizationDenied(ValueError):
    """A signed public identity lacks the backend authorization required."""


def normalize_nostr_pubkey(value: str) -> str:
    """Return the canonical 32-byte x-only Nostr public key representation."""

    if not isinstance(value, str):
        raise ValueError("Nostr public key must be text")
    normalized = value.strip().lower()
    if normalized.startswith(("nsec", "seed", "mnemonic")):
        raise ValueError("private keys are not accepted")
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError("Nostr public key must be 64 lowercase hexadecimal characters")
    return normalized


@dataclass
class Challenge:
    value: str
    expires_at: datetime


@dataclass
class Session:
    token: str
    pubkey: str
    expires_at: datetime
    mode: str = "REAL"


class AuthStore(Protocol):
    def save_challenge(self, challenge_hash: str, expires_at: datetime) -> None: ...

    def register_auth_attempt(
        self, challenge_hash: str, now: datetime, max_attempts: int
    ) -> bool: ...

    def consume_challenge_and_create_session(
        self,
        challenge_hash: str,
        now: datetime,
        token_hash: str,
        pubkey: str,
        session_expires_at: datetime,
        auth_mode: str,
        session_scope: str,
    ) -> bool: ...

    def create_session(
        self,
        token_hash: str,
        pubkey: str,
        session_expires_at: datetime,
        auth_mode: str,
        session_scope: str,
    ) -> None: ...

    def get_session(
        self, token_hash: str, now: datetime, session_scope: str
    ) -> tuple[str, datetime, str] | None: ...

    def revoke_session(self, token_hash: str, now: datetime, session_scope: str) -> None: ...


class NostrEventVerifier(Protocol):
    def verify(
        self,
        event: dict,
        *,
        challenge: str,
        expected_url: str,
        expected_method: str,
        now: datetime,
    ) -> str: ...


def _point_add(
    left: tuple[int, int] | None, right: tuple[int, int] | None
) -> tuple[int, int] | None:
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2 and y1 != y2:
        return None
    if left == right:
        if y1 == 0:
            return None
        slope = (3 * x1 * x1) * pow(2 * y1, SECP256K1_FIELD - 2, SECP256K1_FIELD)
    else:
        slope = (y2 - y1) * pow(x2 - x1, SECP256K1_FIELD - 2, SECP256K1_FIELD)
    slope %= SECP256K1_FIELD
    x3 = (slope * slope - x1 - x2) % SECP256K1_FIELD
    return x3, (slope * (x1 - x3) - y1) % SECP256K1_FIELD


def _point_multiply(scalar: int, point: tuple[int, int] | None) -> tuple[int, int] | None:
    result = None
    current = point
    while scalar:
        if scalar & 1:
            result = _point_add(result, current)
        current = _point_add(current, current)
        scalar >>= 1
    return result


def _lift_x(x: int) -> tuple[int, int] | None:
    if x >= SECP256K1_FIELD:
        return None
    y_squared = (pow(x, 3, SECP256K1_FIELD) + 7) % SECP256K1_FIELD
    y = pow(y_squared, (SECP256K1_FIELD + 1) // 4, SECP256K1_FIELD)
    if pow(y, 2, SECP256K1_FIELD) != y_squared:
        return None
    return x, y if y % 2 == 0 else SECP256K1_FIELD - y


def _tagged_hash(tag: str, data: bytes) -> bytes:
    tag_hash = hashlib.sha256(tag.encode("utf-8")).digest()
    return hashlib.sha256(tag_hash + tag_hash + data).digest()


def verify_bip340(pubkey_hex: str, message: bytes, signature_hex: str) -> bool:
    """Verify a BIP-340 Schnorr signature over a 32-byte message."""

    try:
        if len(message) != 32 or len(pubkey_hex) != 64 or len(signature_hex) != 128:
            return False
        pubkey_bytes = bytes.fromhex(pubkey_hex)
        signature = bytes.fromhex(signature_hex)
    except ValueError:
        return False
    public_point = _lift_x(int.from_bytes(pubkey_bytes, "big"))
    if public_point is None:
        return False
    r = int.from_bytes(signature[:32], "big")
    s = int.from_bytes(signature[32:], "big")
    if r >= SECP256K1_FIELD or s >= SECP256K1_ORDER:
        return False
    challenge = int.from_bytes(
        _tagged_hash("BIP0340/challenge", signature[:32] + pubkey_bytes + message), "big"
    ) % SECP256K1_ORDER
    candidate = _point_add(
        _point_multiply(s, SECP256K1_G),
        _point_multiply(SECP256K1_ORDER - challenge, public_point),
    )
    return candidate is not None and candidate[1] % 2 == 0 and candidate[0] == r


def nostr_event_id(event: dict) -> str:
    serialized = json.dumps(
        [0, event["pubkey"], event["created_at"], event["kind"], event["tags"], event["content"]],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


class Bip340NostrEventVerifier:
    def __init__(self, max_clock_skew_seconds: int = 300):
        self.max_clock_skew_seconds = max_clock_skew_seconds

    @staticmethod
    def _single_tag(event: dict, name: str) -> str | None:
        values = [tag[1] for tag in event["tags"] if len(tag) == 2 and tag[0] == name]
        return values[0] if len(values) == 1 else None

    def verify(
        self,
        event: dict,
        *,
        challenge: str,
        expected_url: str,
        expected_method: str,
        now: datetime,
    ) -> str:
        required = {"id", "pubkey", "created_at", "kind", "tags", "content", "sig"}
        if not isinstance(event, dict) or not required.issubset(event):
            raise ValueError("incomplete Nostr event")
        if not isinstance(event["created_at"], int) or isinstance(event["created_at"], bool):
            raise ValueError("invalid Nostr event timestamp")
        if not isinstance(event["tags"], list) or any(
            not isinstance(tag, list) or any(not isinstance(value, str) for value in tag)
            for tag in event["tags"]
        ):
            raise ValueError("invalid Nostr event tags")
        if event["kind"] != NIP98_AUTH_KIND or event["content"] != challenge:
            raise ValueError("Nostr event does not match challenge")
        if any(
            not isinstance(event[field], str)
            or len(event[field]) != expected_length
            or any(character not in "0123456789abcdef" for character in event[field])
            for field, expected_length in (("id", 64), ("pubkey", 64), ("sig", 128))
        ):
            raise ValueError("invalid Nostr hexadecimal field")
        try:
            event_time = datetime.fromtimestamp(event["created_at"], timezone.utc)
        except (OverflowError, OSError, ValueError):
            raise ValueError("invalid Nostr event timestamp") from None
        if abs((now - event_time).total_seconds()) > self.max_clock_skew_seconds:
            raise ValueError("Nostr event timestamp is outside the allowed window")
        payload_hash = hashlib.sha256(challenge.encode("utf-8")).hexdigest()
        if (
            self._single_tag(event, "u") != expected_url
            or self._single_tag(event, "method") != expected_method
            or self._single_tag(event, "challenge") != challenge
            or self._single_tag(event, "payload") != payload_hash
        ):
            raise ValueError("Nostr event is not bound to this request")
        try:
            computed_id = nostr_event_id(event)
        except (KeyError, TypeError, ValueError):
            raise ValueError("invalid Nostr event") from None
        if not secrets.compare_digest(str(event["id"]), computed_id):
            raise ValueError("invalid Nostr event id")
        if not verify_bip340(str(event["pubkey"]), bytes.fromhex(computed_id), str(event["sig"])):
            raise ValueError("invalid Nostr signature")
        return str(event["pubkey"])


class MemoryAuthStore:
    """Explicit development fallback used only without DATABASE_URL."""

    def __init__(self):
        self.challenges: dict[str, tuple[datetime, datetime | None, int]] = {}
        self.sessions: dict[str, tuple[str, datetime, datetime | None, str, str]] = {}

    def save_challenge(self, challenge_hash: str, expires_at: datetime) -> None:
        self.challenges[challenge_hash] = (expires_at, None, 0)

    def register_auth_attempt(
        self, challenge_hash: str, now: datetime, max_attempts: int
    ) -> bool:
        challenge = self.challenges.get(challenge_hash)
        if (
            not challenge
            or challenge[1] is not None
            or challenge[0] <= now
            or challenge[2] >= max_attempts
        ):
            return False
        self.challenges[challenge_hash] = (challenge[0], challenge[1], challenge[2] + 1)
        return True

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
        challenge = self.challenges.get(challenge_hash)
        if not challenge or challenge[1] is not None or challenge[0] <= now:
            return False
        self.challenges[challenge_hash] = (challenge[0], now, challenge[2])
        self.sessions[token_hash] = (
            pubkey,
            session_expires_at,
            None,
            auth_mode,
            session_scope,
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
        self.sessions[token_hash] = (
            pubkey,
            session_expires_at,
            None,
            auth_mode,
            session_scope,
        )

    def get_session(
        self, token_hash: str, now: datetime, session_scope: str
    ) -> tuple[str, datetime, str] | None:
        session = self.sessions.get(token_hash)
        if (
            not session
            or session[2] is not None
            or session[1] <= now
            or session[4] != session_scope
        ):
            return None
        return session[0], session[1], session[3]

    def revoke_session(self, token_hash: str, now: datetime, session_scope: str) -> None:
        session = self.sessions.get(token_hash)
        if session and session[4] == session_scope:
            self.sessions[token_hash] = (
                session[0],
                session[1],
                now,
                session[3],
                session[4],
            )


class NostrAuth:
    def __init__(
        self,
        store: AuthStore | None = None,
        verifier: NostrEventVerifier | None = None,
        ttl_seconds: int = 300,
        session_seconds: int = 43200,
        max_attempts_per_challenge: int = 5,
        expected_url: str = "http://localhost:5173/api/auth/nostr/sessions",
        session_scope: str = "PARTICIPANT",
        pubkey_authorizer: Callable[[str], bool] | None = None,
    ):
        self.ttl = ttl_seconds
        self.session_seconds = session_seconds
        self.max_attempts_per_challenge = max_attempts_per_challenge
        self.expected_url = expected_url
        self.session_scope = session_scope
        self.pubkey_authorizer = pubkey_authorizer
        self.store = store or MemoryAuthStore()
        self.verifier = verifier or Bip340NostrEventVerifier()

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def issue_challenge(self) -> Challenge:
        value = secrets.token_urlsafe(32)
        challenge = Challenge(value, datetime.now(timezone.utc) + timedelta(seconds=self.ttl))
        self.store.save_challenge(self._hash(value), challenge.expires_at)
        return challenge

    def signing_contract(self, challenge: str) -> dict:
        return {
            "kind": NIP98_AUTH_KIND,
            "url": self.expected_url,
            "method": "POST",
            "payload_hash": self._hash(challenge),
        }

    def authenticate(
        self,
        challenge_value: str,
        pubkey: str,
        signature: str,
        event: dict | None = None,
    ) -> Session:
        now = datetime.now(timezone.utc)
        if not challenge_value or not pubkey or not signature:
            raise ValueError("invalid Nostr signature envelope")
        if str(signature).startswith("nsec") or str(pubkey).startswith("nsec"):
            raise ValueError("private keys are not accepted")
        if not self.store.register_auth_attempt(
            self._hash(challenge_value), now, self.max_attempts_per_challenge
        ):
            raise ValueError("invalid, expired, or exhausted challenge")
        verified_pubkey = normalize_nostr_pubkey(self.verifier.verify(
            event or {},
            challenge=challenge_value,
            expected_url=self.expected_url,
            expected_method="POST",
            now=now,
        ))
        envelope_pubkey = normalize_nostr_pubkey(pubkey)
        if not secrets.compare_digest(envelope_pubkey, verified_pubkey) or not secrets.compare_digest(
            signature, str(event.get("sig"))
        ):
            raise ValueError("signed event does not match envelope")
        if self.pubkey_authorizer and not self.pubkey_authorizer(verified_pubkey):
            raise AuthorizationDenied("public key is not authorized for this session")
        token = uuid.uuid4().hex + secrets.token_urlsafe(24)
        session = Session(token, verified_pubkey, now + timedelta(seconds=self.session_seconds), "REAL")
        created = self.store.consume_challenge_and_create_session(
            self._hash(challenge_value),
            now,
            self._hash(token),
            verified_pubkey,
            session.expires_at,
            session.mode,
            self.session_scope,
        )
        if not created:
            raise ValueError("invalid or expired challenge")
        return session

    def authenticate_demo(self, pubkey: str) -> Session:
        now = datetime.now(timezone.utc)
        normalized_pubkey = normalize_nostr_pubkey(pubkey)
        token = uuid.uuid4().hex + secrets.token_urlsafe(24)
        session = Session(
            token,
            normalized_pubkey,
            now + timedelta(seconds=self.session_seconds),
            "DEMO",
        )
        if self.pubkey_authorizer and not self.pubkey_authorizer(normalized_pubkey):
            raise AuthorizationDenied("public key is not authorized for this session")
        self.store.create_session(
            self._hash(token),
            normalized_pubkey,
            session.expires_at,
            session.mode,
            self.session_scope,
        )
        return session

    def revoke(self, token: str | None) -> None:
        if token:
            self.store.revoke_session(
                self._hash(token), datetime.now(timezone.utc), self.session_scope
            )

    def current(self, token: str | None) -> Session | None:
        if not token:
            return None
        stored = self.store.get_session(
            self._hash(token), datetime.now(timezone.utc), self.session_scope
        )
        if not stored:
            return None
        pubkey, expires_at, mode = stored
        return Session(token, pubkey, expires_at, mode)
