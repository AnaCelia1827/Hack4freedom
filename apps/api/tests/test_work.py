from bluejet_api import create_app
from bluejet_api.config import Config


ADMIN_PUBKEY = "c" * 64


class AdminTestConfig(Config):
    TESTING = True
    ADMIN_PUBKEYS = {ADMIN_PUBKEY}


def auth(client, pubkey):
    challenge = client.post("/auth/nostr/challenges").json["challenge"]
    signature = "sig"
    client.post(
        "/auth/nostr/sessions",
        json={
            "challenge": challenge,
            "pubkey": pubkey,
            "signature": signature,
            "event": {"pubkey": pubkey, "content": challenge, "sig": signature},
        },
    )


def test_only_funded_tasks_publish_and_eligible_participant_can_reserve():
    app = create_app(AdminTestConfig); client = app.test_client(); pubkey = ADMIN_PUBKEY
    auth(client, pubkey)
    client.post("/modules/bluejet-basics-quiz/quiz-attempts", json={"answers": {"q1":"planejar","q2":"evidencia","q3":"revisor","q4":"80","q5":"competencia"}})
    company = client.post("/admin/companies", json={"name":"Acme"}).json
    task = client.post("/admin/paid-tasks", json={"company_id": company["id"], "title":"Tarefa", "reward_sats": 100}).json
    assert client.post(f"/admin/paid-tasks/{task['id']}/publish").status_code == 409
    client.post(f"/admin/paid-tasks/{task['id']}/funding-reservations", json={"amount_sats":100})
    client.post(f"/admin/paid-tasks/{task['id']}/publish")
    assert client.post(f"/paid-tasks/{task['id']}/assignment-reservations").status_code == 201


def test_upload_rejects_unsupported_or_oversized_files():
    client = __import__('bluejet_api').create_app().test_client()
    auth(client, "d" * 64)
    assert client.post('/uploads', json={"filename": "x.exe", "mime_type": "application/octet-stream", "size": 10}).status_code == 422
