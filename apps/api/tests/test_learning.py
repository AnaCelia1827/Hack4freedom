from bluejet_api import create_app
from nostr_test_utils import signed_auth_payload


def login(client):
    challenge = client.post("/auth/nostr/challenges").json
    client.post("/auth/nostr/sessions", json=signed_auth_payload(challenge, 2))


def test_quiz_pass_creates_unique_evidence_and_badge_is_opt_in():
    app = create_app()
    client = app.test_client()
    login(client)
    client.post("/courses/bluejet-basics/enrollments")
    answers = {"q1": "planejar", "q2": "evidencia", "q3": "revisor", "q4": "80", "q5": "competencia"}
    response = client.post("/modules/bluejet-basics-quiz/quiz-attempts", json={"answers": answers})
    assert response.json["passed"] is True
    evidence = response.json["skill_evidence"]
    assert client.get("/skill-evidence").json["items"]
    assert client.put(
        f"/skill-evidence/{evidence['id']}/badge-consent", json={}
    ).status_code == 422
    badge = client.put(
        f"/skill-evidence/{evidence['id']}/badge-consent", json={"consent": True}
    )
    assert badge.status_code == 202
    assert badge.json["mode"] == "SANDBOX"
    repeated = client.post("/modules/bluejet-basics-quiz/quiz-attempts", json={"answers": answers})
    assert repeated.json["attempt"]["attempt_number"] == 2
    assert repeated.json["skill_evidence"]["id"] == evidence["id"]
    learning = app.config["LEARNING"]
    assert len(learning.store.attempts) == 2
    assert len(learning.store.evidence) == 1
    repeated_badge = client.put(
        f"/skill-evidence/{evidence['id']}/badge-consent", json={"consent": True}
    )
    assert repeated_badge.json["id"] == badge.json["id"]
    status = client.get(f"/skill-evidence/{evidence['id']}/badge-publication")
    assert status.json["status"] == "PUBLISH_PENDING"
    assert len(
        [event for event in learning.store.outbox if event["type"] == "BadgePublicationRequested"]
    ) == 1


def test_badge_consent_is_bound_to_the_skill_evidence_owner():
    app = create_app()
    owner = app.test_client()
    other = app.test_client()
    login(owner)
    challenge = other.post("/auth/nostr/challenges").json
    other.post("/auth/nostr/sessions", json=signed_auth_payload(challenge, 3))
    answers = {
        "q1": "planejar",
        "q2": "evidencia",
        "q3": "revisor",
        "q4": "80",
        "q5": "competencia",
    }
    evidence = owner.post(
        "/modules/bluejet-basics-quiz/quiz-attempts", json={"answers": answers}
    ).json["skill_evidence"]

    assert other.put(
        f"/skill-evidence/{evidence['id']}/badge-consent", json={"consent": True}
    ).status_code == 404
    assert other.get(
        f"/skill-evidence/{evidence['id']}/badge-publication"
    ).status_code == 404


def test_failed_quiz_keeps_history_without_evidence():
    app = create_app()
    client = app.test_client()
    login(client)
    response = client.post("/modules/bluejet-basics-quiz/quiz-attempts", json={"answers": {"q1": "wrong"}})
    assert response.json["passed"] is False
    assert response.json["skill_evidence"] is None
    assert app.config["LEARNING"].store.attempts[0]["score"] == 0


def test_quiz_rejects_unbounded_or_invalid_answer_payloads():
    client = create_app().test_client()
    login(client)
    assert client.post(
        "/modules/bluejet-basics-quiz/quiz-attempts", json={"answers": []}
    ).status_code == 422
    assert client.post(
        "/modules/bluejet-basics-quiz/quiz-attempts",
        json={"answers": {f"q{number}": "x" for number in range(21)}},
    ).status_code == 422
    assert client.post(
        "/courses/bluejet-basics/activities/bluejet-basics-activity/submissions",
        json={"content": "x" * 20001},
    ).status_code == 422
