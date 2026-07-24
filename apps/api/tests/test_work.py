from bluejet_api import create_app
from bluejet_api.config import Config
from nostr_test_utils import pubkey_for_private_key, signed_auth_payload


ADMIN_PUBKEY = pubkey_for_private_key(3)


class AdminTestConfig(Config):
    TESTING = True
    ADMIN_PUBKEYS = {ADMIN_PUBKEY}


def auth(client, private_key):
    challenge = client.post("/auth/nostr/challenges").json
    client.post("/auth/nostr/sessions", json=signed_auth_payload(challenge, private_key))


def admin_auth(client, private_key):
    challenge = client.post("/admin/auth/nostr/challenges").json
    return client.post(
        "/admin/auth/nostr/sessions",
        json=signed_auth_payload(challenge, private_key),
    )


def test_only_funded_tasks_publish_and_eligible_participant_can_reserve():
    app = create_app(AdminTestConfig); client = app.test_client()
    assert admin_auth(client, 3).status_code == 201
    company = client.post("/admin/companies", json={"name":"Acme"}).json
    task = client.post("/admin/paid-tasks", json={"company_id": company["id"], "title":"Tarefa", "reward_sats": 100}).json
    assert client.post(f"/admin/paid-tasks/{task['id']}/publish").status_code == 409
    client.post(f"/admin/paid-tasks/{task['id']}/funding-reservations", json={"amount_sats":100})
    client.post(f"/admin/paid-tasks/{task['id']}/publish")
    auth(client, 3)
    assert client.post(f"/paid-tasks/{task['id']}/assignment-reservations").status_code == 409
    client.post("/modules/bluejet-basics-quiz/quiz-attempts", json={"answers": {"q1":"planejar","q2":"evidencia","q3":"revisor","q4":"80","q5":"competencia"}})
    assert client.post(f"/paid-tasks/{task['id']}/assignment-reservations").status_code == 201


def test_participant_session_cannot_be_reused_as_administrative_session():
    app = create_app(AdminTestConfig)
    client = app.test_client()
    auth(client, 3)

    assert client.post("/admin/companies", json={"name": "Acme"}).status_code == 403


def test_non_admin_pubkey_cannot_create_administrative_session():
    app = create_app(AdminTestConfig)
    client = app.test_client()

    assert admin_auth(client, 4).status_code == 403


def test_client_cannot_choose_a_privileged_role_during_login():
    client = create_app(AdminTestConfig).test_client()
    challenge = client.post("/auth/nostr/challenges").json
    payload = signed_auth_payload(challenge, 4)
    payload["role"] = "ADMIN"

    assert client.post("/auth/nostr/sessions", json=payload).status_code == 422


def test_upload_rejects_unsupported_or_oversized_files():
    client = __import__('bluejet_api').create_app().test_client()
    auth(client, 4)
    assert client.post('/uploads', json={"filename": "x.exe", "mime_type": "application/octet-stream", "size": 10}).status_code == 422
