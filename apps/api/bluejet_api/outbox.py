"""Small, provider-agnostic outbox dispatcher."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .database import DatabaseManager


OutboxHandler = Callable[[dict[str, Any]], None]


class OutboxWorker:
    def __init__(self, database: DatabaseManager, worker_id: str, handler: OutboxHandler):
        self.database = database
        self.worker_id = worker_id
        self.handler = handler

    def run_once(self, limit: int = 20) -> dict[str, int]:
        events = self.database.claim_outbox(self.worker_id, limit=limit)
        published = 0
        failed = 0
        for event in events:
            try:
                self.handler(event)
            except Exception as error:
                failed += 1
                self.database.release_outbox(event["event_id"], self.worker_id, type(error).__name__)
            else:
                if self.database.mark_outbox_published(event["event_id"], self.worker_id):
                    published += 1
        return {"claimed": len(events), "published": published, "failed": failed}
