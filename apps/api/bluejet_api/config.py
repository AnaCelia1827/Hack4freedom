import os


class Config:
    TESTING = False
    ENVIRONMENT = os.getenv("BLUEJET_ENV", "development")
    DATABASE_URL = os.getenv("DATABASE_URL")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    ADMIN_PUBKEYS = {value.strip() for value in os.getenv("BLUEJET_ADMIN_PUBKEYS", "").split(",") if value.strip()}


def validate_config(config) -> None:
    if config.get("ENVIRONMENT") == "production" and not config.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is required in production")
