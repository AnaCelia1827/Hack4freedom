import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from bluejet_api import create_app
from bluejet_api.auth import normalize_nostr_pubkey
from nostr_test_utils import signed_auth_payload


def test_pubkey_normalization_is_canonical_and_rejects_private_or_invalid_values():
    assert normalize_nostr_pubkey("  " + ("A" * 64) + "  ") == "a" * 64

    for value in ("f" * 63, "g" * 64, "nsec1private", "seed phrase"):
        with pytest.raises(ValueError):
            normalize_nostr_pubkey(value)


def test_challenge_auth_me_and_logout():
    client = create_app().test_client()
    challenge = client.post("/auth/nostr/challenges").json
    payload = signed_auth_payload(challenge)
    response = client.post("/auth/nostr/sessions", json=payload)
    assert response.status_code == 201
    assert response.json["mode"] == "REAL"
    current = client.get("/me").json
    assert current["pubkey"] == payload["pubkey"]
    assert current["mode"] == "REAL"
    assert current["onboarding_completed"] is False
    assert current["expires_at"]
    assert client.delete("/sessions/current").status_code == 200
    assert client.get("/me").status_code == 401


def test_challenge_cannot_be_replayed_or_receive_private_key():
    client = create_app().test_client()
    challenge = client.post("/auth/nostr/challenges").json
    payload = signed_auth_payload(challenge)
    assert client.post("/auth/nostr/sessions", json=payload).status_code == 201
    assert client.post("/auth/nostr/sessions", json=payload).status_code == 401
    challenge = client.post("/auth/nostr/challenges").json
    assert client.post(
        "/auth/nostr/sessions",
        json={**signed_auth_payload(challenge), "signature": "nsec1secret"},
    ).status_code == 401


def test_invalid_signature_timestamp_and_request_binding_are_rejected():
    client = create_app().test_client()
    challenge = client.post("/auth/nostr/challenges").json
    invalid_signature = signed_auth_payload(challenge)
    invalid_signature["event"]["sig"] = "00" * 64
    invalid_signature["signature"] = "00" * 64
    assert client.post("/auth/nostr/sessions", json=invalid_signature).status_code == 401

    challenge = client.post("/auth/nostr/challenges").json
    stale = signed_auth_payload(
        challenge,
        created_at=int((datetime.now(timezone.utc) - timedelta(minutes=6)).timestamp()),
    )
    assert client.post("/auth/nostr/sessions", json=stale).status_code == 401

    challenge = client.post("/auth/nostr/challenges").json
    wrong_request = signed_auth_payload(challenge)
    wrong_request["event"]["tags"][0][1] = "https://attacker.invalid/session"
    assert client.post("/auth/nostr/sessions", json=wrong_request).status_code == 401


def test_challenge_authentication_attempts_are_bounded():
    app = create_app()
    client = app.test_client()
    challenge = client.post("/auth/nostr/challenges").json
    invalid = signed_auth_payload(challenge)
    invalid["event"]["sig"] = "00" * 64
    invalid["signature"] = "00" * 64

    for _ in range(5):
        assert client.post("/auth/nostr/sessions", json=invalid).status_code == 401
    valid = signed_auth_payload(challenge)
    exhausted = client.post("/auth/nostr/sessions", json=valid)

    assert exhausted.status_code == 401
    assert "exhausted challenge" in exhausted.json["detail"]


def test_demo_session_is_explicit_and_only_enabled_outside_production():
    client = create_app().test_client()
    response = client.post("/auth/demo/sessions")
    assert response.status_code == 201
    assert response.json["mode"] == "DEMO"
    assert client.get("/me").json["mode"] == "DEMO"


def test_onboarding_requires_session_and_stays_bound_to_its_pubkey():
    app = create_app()
    anonymous = app.test_client()
    first = app.test_client()
    second = app.test_client()
    assert anonymous.post("/onboarding/drafts").status_code == 401

    first_challenge = first.post("/auth/nostr/challenges").json
    second_challenge = second.post("/auth/nostr/challenges").json
    assert first.post(
        "/auth/nostr/sessions", json=signed_auth_payload(first_challenge, 5)
    ).status_code == 201
    assert second.post(
        "/auth/nostr/sessions", json=signed_auth_payload(second_challenge, 6)
    ).status_code == 201

    draft = first.post("/onboarding/drafts").json
    fields = {
        "name": "Ada",
        "email": "ada@example.test",
        "identity": "Mulher",
        "skills": ["Tecnologia"],
        "verification": "manual",
        "consent": True,
        "password": "must-not-be-stored",
    }
    updated = first.patch(f"/onboarding/drafts/{draft['id']}", json=fields)
    assert updated.status_code == 200
    assert "password" not in updated.json
    assert second.patch(f"/onboarding/drafts/{draft['id']}", json={"name": "Mallory"}).status_code == 404
    assert first.post(f"/onboarding/drafts/{draft['id']}/complete").status_code == 201
    assert first.get("/me").json["onboarding_completed"] is True


def test_memory_fallback_keeps_only_hashes_of_bearer_material():
    app = create_app()
    client = app.test_client()
    auth = app.config["NOSTR_AUTH"]
    challenge_response = client.post("/auth/nostr/challenges").json
    challenge = challenge_response["challenge"]
    assert challenge not in auth.store.challenges
    assert hashlib.sha256(challenge.encode()).hexdigest() in auth.store.challenges

    response = client.post(
        "/auth/nostr/sessions",
        json=signed_auth_payload(challenge_response, 2),
    )
    raw_token = response.headers["Set-Cookie"].split("=", 1)[1].split(";", 1)[0]
    assert raw_token not in auth.store.sessions
    assert hashlib.sha256(raw_token.encode()).hexdigest() in auth.store.sessions
