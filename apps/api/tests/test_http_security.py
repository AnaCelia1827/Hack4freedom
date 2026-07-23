import pytest

from bluejet_api import create_app
from bluejet_api.config import Config, validate_config


def _login(client):
    challenge = client.post("/auth/nostr/challenges").json["challenge"]
    return client.post(
        "/auth/nostr/sessions",
        json={
            "challenge": challenge,
            "pubkey": "a" * 64,
            "signature": "sig",
            "event": {"pubkey": "a" * 64, "content": challenge, "sig": "sig"},
        },
    )


def test_cors_allows_configured_origin_with_credentials():
    client = create_app().test_client()
    response = client.options(
        "/auth/nostr/sessions",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert response.headers["Access-Control-Allow-Credentials"] == "true"
    assert "Content-Type" in response.headers["Access-Control-Allow-Headers"]
    assert "POST" in response.headers["Access-Control-Allow-Methods"]
    assert "Origin" in response.headers["Vary"]


def test_cors_does_not_reflect_an_unconfigured_origin():
    client = create_app().test_client()
    response = client.get("/health/live", headers={"Origin": "https://attacker.invalid"})

    assert "Access-Control-Allow-Origin" not in response.headers
    assert "Access-Control-Allow-Credentials" not in response.headers


def test_development_session_cookie_is_http_only_and_same_site_lax():
    response = _login(create_app().test_client())
    cookie = response.headers["Set-Cookie"]

    assert "bluejet_session=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert "Path=/" in cookie
    assert "Secure" not in cookie


def test_production_session_cookie_is_secure():
    class ProductionConfig(Config):
        TESTING = True
        ENVIRONMENT = "production"
        DATABASE_URL = "postgresql+psycopg://bluejet:bluejet@127.0.0.1:1/bluejet"
        CORS_ORIGINS = ("https://app.bluejet.example",)

    response = _login(create_app(ProductionConfig).test_client())

    assert "Secure" in response.headers["Set-Cookie"]


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"ENVIRONMENT": "development", "CORS_ORIGINS": ("*",)}, "wildcard"),
        (
            {
                "ENVIRONMENT": "production",
                "DATABASE_URL": "postgresql://configured",
                "CORS_ORIGINS": ("http://app.bluejet.example",),
            },
            "HTTPS",
        ),
    ],
)
def test_invalid_cors_configuration_fails_closed(overrides, message):
    config = {
        "ENVIRONMENT": "development",
        "DATABASE_URL": None,
        "DATABASE_LOCK_TIMEOUT_MS": 1000,
        "CORS_ORIGINS": ("http://localhost:5173",),
        **overrides,
    }

    with pytest.raises(RuntimeError, match=message):
        validate_config(config)
