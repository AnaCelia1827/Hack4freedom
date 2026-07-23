from bluejet_api import create_app


def login(client):
    challenge = client.post("/auth/nostr/challenges").json["challenge"]
    pubkey = "b" * 64
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


def test_quiz_pass_creates_unique_evidence_and_badge_is_opt_in():
    client = create_app().test_client()
    login(client)
    client.post("/courses/bluejet-basics/enrollments")
    answers = {"q1": "planejar", "q2": "evidencia", "q3": "revisor", "q4": "80", "q5": "competencia"}
    response = client.post("/modules/bluejet-basics-quiz/quiz-attempts", json={"answers": answers})
    assert response.json["passed"] is True
    evidence = response.json["skill_evidence"]
    assert client.get("/skill-evidence").json["items"]
    assert client.put(f"/skill-evidence/{evidence['id']}/badge-consent").status_code == 202


def test_failed_quiz_keeps_history_without_evidence():
    client = create_app().test_client()
    login(client)
    response = client.post("/modules/bluejet-basics-quiz/quiz-attempts", json={"answers": {"q1": "wrong"}})
    assert response.json["passed"] is False
    assert response.json["skill_evidence"] is None
