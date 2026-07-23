"""Nostr challenge/session boundary.

The cryptographic verifier is an adapter; production wires a NIP-01/NIP-07
compatible verifier. This module deliberately accepts only public material.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import secrets
import uuid


@dataclass
class Challenge:
    value: str
    expires_at: datetime
    used: bool = False


@dataclass
class Session:
    token: str
    pubkey: str
    expires_at: datetime
    revoked: bool = False


class NostrAuth:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self.challenges: dict[str, Challenge] = {}
        self.sessions: dict[str, Session] = {}

    def issue_challenge(self) -> Challenge:
        value = secrets.token_urlsafe(32)
        challenge = Challenge(value, datetime.now(timezone.utc) + timedelta(seconds=self.ttl))
        self.challenges[value] = challenge
        return challenge

    def authenticate(self, challenge_value: str, pubkey: str, signature: str, event: dict | None = None) -> Session:
        challenge = self.challenges.get(challenge_value)
        now = datetime.now(timezone.utc)
        if not challenge or challenge.used or challenge.expires_at <= now:
            raise ValueError("invalid or expired challenge")
        if not pubkey or not signature or len(pubkey) > 128:
            raise ValueError("invalid Nostr signature envelope")
        # Cryptographic verification belongs to the NostrSigner adapter.
        if signature.startswith("nsec"):
            raise ValueError("private keys are not accepted")
        if not isinstance(event, dict) or event.get("pubkey") != pubkey or event.get("content") != challenge_value or event.get("sig") != signature:
            raise ValueError("signed event does not match challenge")
        challenge.used = True
        token = uuid.uuid4().hex + secrets.token_urlsafe(24)
        session = Session(token, pubkey, now + timedelta(hours=12))
        self.sessions[token] = session
        return session

    def revoke(self, token: str) -> None:
        if token in self.sessions:
            self.sessions[token].revoked = True

    def current(self, token: str | None) -> Session | None:
        session = self.sessions.get(token or "")
        if not session or session.revoked or session.expires_at <= datetime.now(timezone.utc):
            return None
        return session
