"""Structured logging helpers that keep bearer and payment material out of logs."""

from __future__ import annotations

import json
import logging
from typing import Any


SENSITIVE_MARKERS = (
    "authorization",
    "cookie",
    "invoice",
    "mnemonic",
    "nsec",
    "password",
    "preimage",
    "rune",
    "secret",
    "seed",
    "signature",
    "token",
)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: ("[REDACTED]" if any(marker in key.lower() for marker in SENSITIVE_MARKERS) else redact(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            payload.update(redact(fields))
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging(app) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.propagate = False
