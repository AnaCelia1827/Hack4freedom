import pytest
from sqlalchemy.exc import OperationalError

from bluejet_api import create_app
from bluejet_api.auth import MemoryAuthStore
from bluejet_api.config import Config, validate_config
from nostr_test_utils import signed_auth_payload


def _login(client):
    challenge = client.post("/auth/nostr/challenges").json
    return client.post("/auth/nostr/sessions", json=signed_auth_payload(challenge))


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
        AUTH_STORE = MemoryAuthStore()
        CORS_ORIGINS = ("https://app.bluejet.example",)
        NOSTR_AUTH_AUDIENCE = "https://app.bluejet.example/api/auth/nostr/sessions"
        ADMIN_NOSTR_AUTH_AUDIENCE = "https://app.bluejet.example/api/admin/auth/nostr/sessions"
        DEMO_AUTH_ENABLED = False
        LIGHTNING_MODE = "REAL"
        LIGHTNING_GATEWAY = object()

    response = _login(create_app(ProductionConfig).test_client())

    assert "Secure" in response.headers["Set-Cookie"]


def test_production_cookie_requests_require_a_trusted_origin():
    class ParticipantOnlyRbacStore:
        @staticmethod
        def has_any_role(pubkey, roles):
            return "PARTICIPANT" in roles

    class ProductionConfig(Config):
        TESTING = True
        ENVIRONMENT = "production"
        DATABASE_URL = "postgresql+psycopg://configured-but-auth-store-is-injected"
        AUTH_STORE = MemoryAuthStore()
        RBAC_STORE = ParticipantOnlyRbacStore()
        CORS_ORIGINS = ("https://app.bluejet.example",)
        NOSTR_AUTH_AUDIENCE = "https://app.bluejet.example/api/auth/nostr/sessions"
        ADMIN_NOSTR_AUTH_AUDIENCE = "https://app.bluejet.example/api/admin/auth/nostr/sessions"
        DEMO_AUTH_ENABLED = False
        LIGHTNING_MODE = "REAL"
        LIGHTNING_GATEWAY = object()

    client = create_app(ProductionConfig).test_client()
    challenge = client.post(
        "/auth/nostr/challenges", base_url="https://app.bluejet.example"
    ).json
    login = client.post(
        "/auth/nostr/sessions",
        base_url="https://app.bluejet.example",
        json=signed_auth_payload(challenge),
    )
    assert login.status_code == 201

    rejected = client.post(
        "/community/posts",
        base_url="https://app.bluejet.example",
        json={"category": "learning", "content": "hello"},
    )
    accepted = client.post(
        "/community/posts",
        base_url="https://app.bluejet.example",
        headers={"Origin": "https://app.bluejet.example"},
        json={"category": "learning", "content": "hello"},
    )
    assert rejected.status_code == 403
    assert accepted.status_code == 201


def test_configured_database_does_not_fallback_to_memory():
    class UnavailableDatabaseConfig(Config):
        TESTING = True
        ENVIRONMENT = "production"
        DATABASE_URL = "postgresql+psycopg://bluejet:bluejet@127.0.0.1:1/bluejet"
        CORS_ORIGINS = ("https://app.bluejet.example",)
        NOSTR_AUTH_AUDIENCE = "https://app.bluejet.example/api/auth/nostr/sessions"
        ADMIN_NOSTR_AUTH_AUDIENCE = "https://app.bluejet.example/api/admin/auth/nostr/sessions"
        DEMO_AUTH_ENABLED = False
        LIGHTNING_MODE = "REAL"
        LIGHTNING_GATEWAY = object()

    with pytest.raises(OperationalError):
        create_app(UnavailableDatabaseConfig).test_client().post("/auth/nostr/challenges")


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"ENVIRONMENT": "development", "CORS_ORIGINS": ("*",)}, "wildcard"),
        (
            {
                "ENVIRONMENT": "production",
                "DATABASE_URL": "postgresql://configured",
                "CORS_ORIGINS": ("http://app.bluejet.example",),
                "DEMO_AUTH_ENABLED": False,
                "NOSTR_AUTH_AUDIENCE": "https://app.bluejet.example/api/auth/nostr/sessions",
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
