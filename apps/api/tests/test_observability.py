import json
import logging

from bluejet_api import create_app
from bluejet_api.observability import JsonFormatter, redact


def test_redact_masks_nested_bearer_and_payment_material():
    value = {
        "invoice": "lnbc-secret",
        "nested": {"session_token": "bearer", "safe": "visible"},
        "items": [{"nsec": "private-key"}],
    }
    assert redact(value) == {
        "invoice": "[REDACTED]",
        "nested": {"session_token": "[REDACTED]", "safe": "visible"},
        "items": [{"nsec": "[REDACTED]"}],
    }


def test_json_formatter_redacts_extra_fields():
    record = logging.LogRecord("bluejet", logging.INFO, __file__, 1, "event", (), None)
    record.fields = {"path": "/health/live", "authorization": "Bearer secret"}
    payload = json.loads(JsonFormatter().format(record))
    assert payload["path"] == "/health/live"
    assert payload["authorization"] == "[REDACTED]"


def test_api_responses_include_defensive_headers():
    response = create_app().test_client().get("/health/live")
    assert response.headers["Content-Security-Policy"] == "default-src 'none'; frame-ancestors 'none'"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
