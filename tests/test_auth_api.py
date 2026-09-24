import asyncio
from datetime import UTC, datetime

import httpx
import pytest

import services.api.app as api_module
from scripts.seed_demo_accounts import main as seed_demo_accounts_main
from services.api.auth import (
    AuthenticatedSession,
    AuthError,
    AuthResult,
    AuthUser,
    derive_csrf_token,
    hash_session_secret,
    normalize_email,
)
from services.api.config import PRIVACY_NOTICE_VERSION, SESSION_LIFETIME
from services.api.passwords import hash_password, verify_password


class MemoryAuthStore:
    def __init__(self):
        self.next_user_id = 1
        self.users: dict[str, AuthUser] = {}
        self.password_hashes: dict[str, str] = {}
        self.sessions: dict[str, AuthenticatedSession] = {}

    def _issue(self, user: AuthUser) -> AuthResult:
        import secrets

        token = secrets.token_urlsafe(32)
        csrf = derive_csrf_token(token)
        session = AuthenticatedSession(
            session_id=len(self.sessions) + 1,
            user=user,
            session_token_hash=hash_session_secret(token),
            csrf_token_hash=hash_session_secret(csrf),
            expires_at=datetime.now(UTC) + SESSION_LIFETIME,
            csrf_token=csrf,
        )
        self.sessions[session.session_token_hash] = session
        return AuthResult(user, token, csrf)

    def register(self, **kwargs) -> AuthResult:
        email = normalize_email(kwargs["email"])
        if email in self.users:
            raise AuthError(
                "EMAIL_ALREADY_REGISTERED",
                "An account with this email is already registered.",
            )
        if kwargs["privacy_notice_version"] != PRIVACY_NOTICE_VERSION:
            raise AuthError(
                "PRIVACY_NOTICE_VERSION_UNSUPPORTED",
                "The privacy notice is not supported.",
            )
        if not kwargs["privacy_accepted"]:
            raise AuthError("PRIVACY_CONSENT_REQUIRED", "Privacy consent is required.")
        password_hash = hash_password(kwargs["password"])
        user = AuthUser(
            self.next_user_id,
            kwargs["display_name"].strip(),
            email,
            kwargs["role"],
            kwargs.get("preferred_language", "en"),
            False,
        )
        self.next_user_id += 1
        self.users[email] = user
        self.password_hashes[email] = password_hash
        return self._issue(user)

    def login(self, *, email: str, password: str) -> AuthResult:
        normalized = email.strip().lower()
        user = self.users.get(normalized)
        if user is None or not verify_password(password, self.password_hashes[normalized]):
            raise AuthError("INVALID_CREDENTIALS", "Email or password is incorrect.", 401)
        return self._issue(user)

    def get_session(self, session_token: str | None, *, rotate_csrf: bool = False):
        if not session_token:
            return None
        session = self.sessions.get(hash_session_secret(session_token))
        if session is None or session.expires_at <= datetime.now(UTC):
            return None
        return session

    def revoke_session(self, session: AuthenticatedSession) -> None:
        self.sessions.pop(session.session_token_hash, None)

    def complete_demo(self, user_id: int) -> bool:
        for email, user in self.users.items():
            if user.user_id == user_id:
                self.users[email] = AuthUser(
                    user.user_id,
                    user.display_name,
                    user.email,
                    user.role,
                    user.preferred_language,
                    True,
                )
                return True
        raise AuthError("UNAUTHENTICATED", "Please sign in.", 401)


def request(store: MemoryAuthStore, method: str, path: str, **kwargs) -> httpx.Response:
    async def send() -> httpx.Response:
        original = api_module.build_auth_store
        api_module.build_auth_store = lambda: store
        try:
            transport = httpx.ASGITransport(app=api_module.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.request(method, path, **kwargs)
        finally:
            api_module.build_auth_store = original

    return asyncio.run(send())


def register_payload(**overrides):
    payload = {
        "display_name": "Juan Farmer",
        "email": "Juan@example.com",
        "password": "safe-password",
        "role": "farmer",
        "privacy_notice_version": PRIVACY_NOTICE_VERSION,
        "privacy_accepted": True,
        "optional_data_improvement_consent": False,
    }
    payload.update(overrides)
    return payload


def test_registration_normalizes_email_and_issues_hashed_session_cookie():
    store = MemoryAuthStore()
    response = request(store, "POST", "/auth/register", json=register_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["authenticated"] is True
    assert body["user"]["email"] == "juan@example.com"
    assert body["user"]["has_completed_demo"] is False
    assert "session_token" not in response.text
    raw_token = response.cookies.get("tanim_session")
    assert raw_token
    assert raw_token not in {session.session_token_hash for session in store.sessions.values()}
    assert any(value.startswith("$argon2id$") for value in store.password_hashes.values())


def test_registration_requires_current_privacy_consent():
    store = MemoryAuthStore()
    response = request(
        store,
        "POST",
        "/auth/register",
        json=register_payload(privacy_accepted=False),
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "PRIVACY_CONSENT_REQUIRED"
    assert store.users == {}


def test_cooperative_registration_requires_an_organization_name():
    response = request(
        MemoryAuthStore(),
        "POST",
        "/auth/register",
        json=register_payload(role="cooperative", organization_name=""),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "COOPERATIVE_ORGANIZATION_REQUIRED"


def test_demo_seed_fails_clearly_when_passwords_are_missing(monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", "postgresql://unused@127.0.0.1/unused")
    monkeypatch.setenv("TANIM_DEMO_FARMER_PASSWORD", "")
    monkeypatch.setenv("TANIM_DEMO_COOP_PASSWORD", "")

    assert seed_demo_accounts_main() == 1
    assert "TANIM_DEMO_FARMER_PASSWORD" in capsys.readouterr().err


def test_login_uses_generic_failure_for_wrong_password_and_unknown_email():
    store = MemoryAuthStore()
    request(store, "POST", "/auth/register", json=register_payload())

    for email in ["JUAN@example.com", "unknown@example.com"]:
        response = request(
            store,
            "POST",
            "/auth/login",
            json={"email": email, "password": "wrong-password"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == {
            "code": "INVALID_CREDENTIALS",
            "message": "Email or password is incorrect.",
        }


def test_session_restoration_returns_stable_csrf_but_not_session_token():
    store = MemoryAuthStore()
    original = api_module.build_auth_store
    api_module.build_auth_store = lambda: store

    async def flow():
        transport = httpx.ASGITransport(app=api_module.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            login = await client.post("/auth/register", json=register_payload())
            raw_token = client.cookies.get("tanim_session")
            restored = await client.get("/auth/session")
            return login, raw_token, restored

    try:
        login, raw_token, restored = asyncio.run(flow())
    finally:
        api_module.build_auth_store = original

    assert restored.status_code == 200
    assert restored.json()["authenticated"] is True
    assert restored.json()["csrf_token"]
    assert raw_token not in restored.text
    assert login.json()["csrf_token"] == restored.json()["csrf_token"]


def test_csrf_blocks_logout_and_logout_only_revokes_current_session():
    store = MemoryAuthStore()
    original = api_module.build_auth_store
    api_module.build_auth_store = lambda: store

    async def flow():
        transport = httpx.ASGITransport(app=api_module.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as first:
            await first.post("/auth/register", json=register_payload())
            first_session = await first.get("/auth/session")
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as second:
                await second.post(
                    "/auth/login",
                    json={"email": "juan@example.com", "password": "safe-password"},
                )
                missing = await first.post("/auth/logout")
                valid = await first.post(
                    "/auth/logout",
                    headers={"X-CSRF-Token": first_session.json()["csrf_token"]},
                )
                after = await first.get("/auth/session")
                still_active = await second.get("/auth/session")
        return missing, valid, after, still_active

    try:
        missing, valid, after, still_active = asyncio.run(flow())
    finally:
        api_module.build_auth_store = original

    assert missing.status_code == 403
    assert missing.json()["detail"]["code"] == "CSRF_INVALID"
    assert valid.status_code == 200
    assert after.json()["authenticated"] is False
    assert still_active.json()["authenticated"] is True


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("role", "admin", "INVALID_ROLE"),
        ("email", "not-an-email", "INVALID_EMAIL"),
        ("password", "", "INVALID_PASSWORD"),
    ],
)
def test_registration_rejects_untrusted_values(field, value, code):
    response = request(
        MemoryAuthStore(),
        "POST",
        "/auth/register",
        json=register_payload(**{field: value}),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == code
