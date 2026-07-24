from bluejet_api import create_app


def test_live_health():
    client = create_app().test_client()
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}
