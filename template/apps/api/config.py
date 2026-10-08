import logging
import os
from dataclasses import dataclass

LOCAL_DATABASE_URL = (
    "postgresql+asyncpg://app:local-development-only@127.0.0.1:5432/app"
)
LOCAL_SECRET = "local-development-only-change-me"
ACCESS_TOKEN_LIFETIME_SECONDS = 3600

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    database_url: str
    secret: str
    access_token_lifetime_seconds: int
    cors_origins: tuple[str, ...]
    cors_origin_regex: str | None
    spa_origin: str
    csrf_cookie_secure: bool | None
    google: tuple[str, str] | None
    github: tuple[str, str] | None


def _pair(client_id_name: str, client_secret_name: str) -> tuple[str, str] | None:
    client_id = os.environ.get(client_id_name, "").strip()
    client_secret = os.environ.get(client_secret_name, "").strip()
    if client_id and client_secret:
        return (client_id, client_secret)
    return None


def _csrf_cookie_secure() -> bool | None:
    raw = os.environ.get("AUTH_CSRF_COOKIE_SECURE", "").strip().lower()
    if raw in {"1", "true", "yes"}:
        return True
    if raw in {"0", "false", "no"}:
        return False
    return None


def _origins(raw: str) -> tuple[str, ...]:
    return tuple(part.strip().rstrip("/") for part in raw.split(",") if part.strip())


def _origin_regex() -> str | None:
    value = os.environ.get("CORS_ORIGIN_REGEX", "").strip()
    if value == "":
        return None
    return value


def load_settings() -> Settings:
    secret = os.environ.get("SECRET", LOCAL_SECRET)
    if secret == LOCAL_SECRET:
        logger.warning(
            "SECRET is the local development default. Set SECRET before production."
        )
    return Settings(
        database_url=os.environ.get("DATABASE_URL", LOCAL_DATABASE_URL),
        secret=secret,
        access_token_lifetime_seconds=ACCESS_TOKEN_LIFETIME_SECONDS,
        cors_origins=_origins(os.environ.get("CORS_ORIGINS", "http://localhost:5173")),
        cors_origin_regex=_origin_regex(),
        spa_origin=os.environ.get("SPA_ORIGIN", "http://localhost:5173").rstrip("/"),
        csrf_cookie_secure=_csrf_cookie_secure(),
        google=_pair("GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET"),
        github=_pair("GITHUB_OAUTH_CLIENT_ID", "GITHUB_OAUTH_CLIENT_SECRET"),
    )
