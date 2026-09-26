"""Application configuration loaded from environment variables."""

import os

from dotenv import load_dotenv


load_dotenv()


def database_url() -> str:
    """Return the required PostgreSQL SQLAlchemy URL."""
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        raise RuntimeError(
            "DATABASE_URL is required. Copy .env.example to .env or export it."
        )
    if value.startswith("postgres://"):
        value = "postgresql+psycopg://" + value.removeprefix("postgres://")
    if not value.startswith(("postgresql://", "postgresql+psycopg://")):
        raise RuntimeError("DATABASE_URL must be a PostgreSQL URL")
    return value


def secret_key() -> str:
    return os.getenv("SECRET_KEY", "dev-only-change-me")
