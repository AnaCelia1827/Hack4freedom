import os

from .auth import normalize_nostr_pubkey


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv_env(name: str, default: str) -> tuple[str, ...]:
    return tuple(value.strip() for value in os.getenv(name, default).split(",") if value.strip())


def _pubkey_set_env(name: str) -> set[str]:
    return {
        normalize_nostr_pubkey(value)
        for value in os.getenv(name, "").split(",")
        if value.strip()
    }


class Config:
    TESTING = False
    ENVIRONMENT = os.getenv("BLUEJET_ENV", "development")
    DATABASE_URL = os.getenv("DATABASE_URL")
    DATABASE_LOCK_TIMEOUT_MS = int(os.getenv("DATABASE_LOCK_TIMEOUT_MS", "1000"))
    LIGHTNING_MODE = os.getenv("LIGHTNING_MODE", "SANDBOX").strip().upper()
    CORS_ORIGINS = _csv_env("CORS_ORIGINS", "http://localhost:5173")
    SESSION_COOKIE_NAME = "bluejet_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_PATH = "/"
    ADMIN_SESSION_COOKIE_NAME = "bluejet_admin_session"
    NOSTR_AUTH_AUDIENCE = os.getenv(
        "NOSTR_AUTH_AUDIENCE", "http://localhost:5173/api/auth/nostr/sessions"
    )
    ADMIN_NOSTR_AUTH_AUDIENCE = os.getenv(
        "ADMIN_NOSTR_AUTH_AUDIENCE",
        "http://localhost:5173/api/admin/auth/nostr/sessions",
    )
    NOSTR_MAX_CLOCK_SKEW_SECONDS = int(os.getenv("NOSTR_MAX_CLOCK_SKEW_SECONDS", "300"))
    NOSTR_MAX_AUTH_ATTEMPTS = int(os.getenv("NOSTR_MAX_AUTH_ATTEMPTS", "5"))
    DEMO_AUTH_ENABLED = _bool_env("DEMO_AUTH_ENABLED", ENVIRONMENT != "production")
    DEMO_AUTH_PUBKEY = os.getenv("DEMO_AUTH_PUBKEY", "d" * 64)
    ADMIN_PUBKEYS = _pubkey_set_env("BLUEJET_ADMIN_PUBKEYS")


def validate_config(config) -> None:
    environment = config.get("ENVIRONMENT")
    if environment == "production":
        if not config.get("DATABASE_URL"):
            raise RuntimeError("DATABASE_URL is required in production")
        if any(not origin.startswith("https://") for origin in config.get("CORS_ORIGINS", ())):
            raise RuntimeError("CORS_ORIGINS must use HTTPS in production")
        if config.get("DEMO_AUTH_ENABLED"):
            raise RuntimeError("DEMO_AUTH_ENABLED must be disabled in production")
        if not str(config.get("NOSTR_AUTH_AUDIENCE", "")).startswith("https://"):
            raise RuntimeError("NOSTR_AUTH_AUDIENCE must use HTTPS in production")
        if not str(config.get("ADMIN_NOSTR_AUTH_AUDIENCE", "")).startswith("https://"):
            raise RuntimeError("ADMIN_NOSTR_AUTH_AUDIENCE must use HTTPS in production")
        if config.get("LIGHTNING_MODE") != "REAL":
            raise RuntimeError("LIGHTNING_MODE must be REAL in production")
    if "*" in config.get("CORS_ORIGINS", ()):
        raise RuntimeError("CORS_ORIGINS cannot contain a wildcard")
    timeout = config.get("DATABASE_LOCK_TIMEOUT_MS")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
        raise RuntimeError("DATABASE_LOCK_TIMEOUT_MS must be a positive integer")
    if config.get("LIGHTNING_MODE") not in {"MOCK", "SANDBOX", "REAL"}:
        raise RuntimeError("LIGHTNING_MODE must be MOCK, SANDBOX or REAL")
    skew = config.get("NOSTR_MAX_CLOCK_SKEW_SECONDS")
    if isinstance(skew, bool) or not isinstance(skew, int) or not 30 <= skew <= 300:
        raise RuntimeError("NOSTR_MAX_CLOCK_SKEW_SECONDS must be between 30 and 300")
    attempts = config.get("NOSTR_MAX_AUTH_ATTEMPTS", 5)
    if isinstance(attempts, bool) or not isinstance(attempts, int) or not 1 <= attempts <= 10:
        raise RuntimeError("NOSTR_MAX_AUTH_ATTEMPTS must be between 1 and 10")
    demo_pubkey = str(config.get("DEMO_AUTH_PUBKEY", ""))
    try:
        normalize_nostr_pubkey(demo_pubkey)
    except ValueError:
        raise RuntimeError("DEMO_AUTH_PUBKEY must be a 64-character lowercase hex public key")
    try:
        normalized_admins = {
            normalize_nostr_pubkey(pubkey) for pubkey in config.get("ADMIN_PUBKEYS", set())
        }
    except ValueError:
        raise RuntimeError(
            "BLUEJET_ADMIN_PUBKEYS must contain 64-character hexadecimal public keys"
        ) from None
    config["ADMIN_PUBKEYS"] = normalized_admins
