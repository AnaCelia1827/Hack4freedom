"""Provider-agnostic background workers for paid work."""

from __future__ import annotations

from datetime import datetime

from .database import DatabaseManager


class AssignmentExpiryWorker:
    def __init__(self, database: DatabaseManager):
        self.database = database

    def run_once(self, now: datetime | None = None, limit: int = 100) -> dict[str, int]:
        expired = self.database.expire_assignment_reservations(now=now, limit=limit)
        return {"expired": expired}
