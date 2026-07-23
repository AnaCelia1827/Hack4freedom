import os


def _csv_env(name: str, default: str) -> tuple[str, ...]:
    return tuple(value.strip() for value in os.getenv(name, default).split(",") if value.strip())


class Config:
    TESTING = False
    ENVIRONMENT = os.getenv("BLUEJET_ENV", "development")
    DATABASE_URL = os.getenv("DATABASE_URL")
    DATABASE_LOCK_TIMEOUT_MS = int(os.getenv("DATABASE_LOCK_TIMEOUT_MS", "1000"))
    CORS_ORIGINS = _csv_env("CORS_ORIGINS", "http://localhost:5173")
    SESSION_COOKIE_NAME = "bluejet_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_PATH = "/"
    ADMIN_PUBKEYS = {value.strip() for value in os.getenv("BLUEJET_ADMIN_PUBKEYS", "").split(",") if value.strip()}


def validate_config(config) -> None:
    environment = config.get("ENVIRONMENT")
    if environment == "production":
        if not config.get("DATABASE_URL"):
            raise RuntimeError("DATABASE_URL is required in production")
        if any(not origin.startswith("https://") for origin in config.get("CORS_ORIGINS", ())):
            raise RuntimeError("CORS_ORIGINS must use HTTPS in production")
    if "*" in config.get("CORS_ORIGINS", ()):
        raise RuntimeError("CORS_ORIGINS cannot contain a wildcard")
    timeout = config.get("DATABASE_LOCK_TIMEOUT_MS")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
        raise RuntimeError("DATABASE_LOCK_TIMEOUT_MS must be a positive integer")
