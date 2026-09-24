"""Central local authentication and privacy configuration."""

import os
from datetime import timedelta

PRIVACY_NOTICE_VERSION = "privacy-2026-09-v1"
CURRENT_PRIVACY_NOTICE_VERSION = PRIVACY_NOTICE_VERSION

SESSION_COOKIE_NAME = "tanim_session"
SESSION_LIFETIME_DAYS = 7
SESSION_LIFETIME = timedelta(days=SESSION_LIFETIME_DAYS)
SESSION_LIFETIME_SECONDS = int(SESSION_LIFETIME.total_seconds())

DEFAULT_ALLOWED_ORIGINS = (
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
    "http://127.0.0.1:3003",
)

DEMO_FARMER_EMAIL = "farmer.demo@tanim.local"
DEMO_COOPERATIVE_EMAIL = "coop.demo@tanim.local"


def allowed_origins() -> list[str]:
    configured = os.getenv("TANIM_ALLOWED_ORIGINS", "").strip()
    if not configured:
        return list(DEFAULT_ALLOWED_ORIGINS)
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    safe_origins = [origin for origin in origins if origin != "*"]
    return safe_origins or list(DEFAULT_ALLOWED_ORIGINS)


def session_cookie_secure() -> bool:
    value = os.getenv("TANIM_SESSION_COOKIE_SECURE", "false").strip().lower()
    return value in {"1", "true", "yes", "on"}
