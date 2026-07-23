from bluejet_api import create_app


def test_challenge_auth_me_and_logout():
    client = create_app().test_client()
    challenge = client.post("/auth/nostr/challenges").json["challenge"]
    response = client.post("/auth/nostr/sessions", json={"challenge": challenge, "pubkey": "a" * 64, "signature": "sig", "event": {"pubkey": "a" * 64, "content": challenge, "sig": "sig"}})
    assert response.status_code == 201
    assert client.get("/me").json["pubkey"] == "a" * 64
    assert client.delete("/sessions/current").status_code == 200
    assert client.get("/me").status_code == 401


def test_challenge_cannot_be_replayed_or_receive_private_key():
    client = create_app().test_client()
    challenge = client.post("/auth/nostr/challenges").json["challenge"]
    payload = {"challenge": challenge, "pubkey": "a" * 64, "signature": "sig", "event": {"pubkey": "a" * 64, "content": challenge, "sig": "sig"}}
    assert client.post("/auth/nostr/sessions", json=payload).status_code == 201
    assert client.post("/auth/nostr/sessions", json=payload).status_code == 401
    challenge = client.post("/auth/nostr/challenges").json["challenge"]
    assert client.post("/auth/nostr/sessions", json={**payload, "challenge": challenge, "signature": "nsec1secret"}).status_code == 401
