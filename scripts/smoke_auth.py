"""Smoke-test registration, session restoration, and logout without touching a live DB."""

import asyncio
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import services.api.app as api_module  # noqa: E402
from services.api.auth import (  # noqa: E402
    AuthenticatedSession,
    AuthResult,
    AuthUser,
    hash_session_secret,
)
from services.api.config import PRIVACY_NOTICE_VERSION, SESSION_LIFETIME  # noqa: E402
from services.api.passwords import hash_password, verify_password  # noqa: E402


class SmokeAuthStore:
    """A disposable store for the API contract smoke test."""

    def __init__(self):
        self.user = AuthUser(1, "Smoke Farmer", "smoke@example.test", "farmer", "en", False)
        self.password_hash = hash_password("smoke-password")
        self.sessions: dict[str, AuthenticatedSession] = {}

    @staticmethod
    def _issue(user: AuthUser) -> AuthResult:
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(32)
        return AuthResult(user, token, csrf)

    def register(self, **kwargs) -> AuthResult:
        assert kwargs["privacy_notice_version"] == PRIVACY_NOTICE_VERSION
        assert kwargs["privacy_accepted"] is True
        assert verify_password(kwargs["password"], self.password_hash)
        result = self._issue(self.user)
        self.sessions[hash_session_secret(result.session_token)] = AuthenticatedSession(
            session_id=1,
            user=self.user,
            session_token_hash=hash_session_secret(result.session_token),
            csrf_token_hash=hash_session_secret(result.csrf_token),
            expires_at=datetime.now(UTC) + SESSION_LIFETIME,
            csrf_token=result.csrf_token,
        )
        return result

    def get_session(self, session_token: str | None, *, rotate_csrf: bool = False):
        if not session_token:
            return None
        session = self.sessions.get(hash_session_secret(session_token))
        if session is None or session.expires_at <= datetime.now(UTC):
            return None
        if rotate_csrf:
            csrf = secrets.token_urlsafe(32)
            session = AuthenticatedSession(
                session_id=session.session_id,
                user=session.user,
                session_token_hash=session.session_token_hash,
                csrf_token_hash=hash_session_secret(csrf),
                expires_at=session.expires_at,
                csrf_token=csrf,
            )
            self.sessions[session.session_token_hash] = session
        return session

    def revoke_session(self, session: AuthenticatedSession) -> None:
        self.sessions.pop(session.session_token_hash, None)

    def complete_demo(self, user_id: int) -> bool:
        return user_id == self.user.user_id


async def run_smoke() -> None:
    store = SmokeAuthStore()
    original_builder = api_module.build_auth_store
    api_module.build_auth_store = lambda: store
    try:
        transport = httpx.ASGITransport(app=api_module.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://127.0.0.1:3001",
        ) as client:
            register = await client.post(
                "/auth/register",
                json={
                    "display_name": "Smoke Farmer",
                    "email": "smoke@example.test",
                    "password": "smoke-password",
                    "role": "farmer",
                    "privacy_notice_version": PRIVACY_NOTICE_VERSION,
                    "privacy_accepted": True,
                    "optional_data_improvement_consent": False,
                },
            )
            assert register.status_code == 200, register.text
            assert "session_token" not in register.text
            assert client.cookies.get("tanim_session")

            restored = await client.get("/auth/session")
            assert restored.status_code == 200
            assert restored.json()["authenticated"] is True
            csrf_token = restored.json()["csrf_token"]

            logout = await client.post("/auth/logout", headers={"X-CSRF-Token": csrf_token})
            assert logout.status_code == 200
            assert logout.json() == {"authenticated": False}

            after_logout = await client.get("/auth/session")
            assert after_logout.status_code == 200
            assert after_logout.json()["authenticated"] is False
    finally:
        api_module.build_auth_store = original_builder


def main() -> int:
    asyncio.run(run_smoke())
    print("Auth smoke passed: registration, session restoration, and logout are working.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
