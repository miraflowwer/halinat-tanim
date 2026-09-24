import asyncio
import os
import uuid
from pathlib import Path

import httpx
import psycopg
import pytest
from psycopg.sql import SQL, Identifier

import services.api.app as api_module
from scripts.seed_demo_accounts import DemoAccountSeedError, seed_demo_accounts
from services.api.auth import AuthStore, hash_session_secret
from services.api.config import PRIVACY_NOTICE_VERSION

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "data" / "migrations"


def _set_search_path(connection, schema: str) -> None:
    connection.execute(SQL("SET search_path TO {}, public").format(Identifier(schema)))


@pytest.fixture
def isolated_auth_store():
    database_url = os.getenv("TANIM_TEST_DATABASE_URL", "").strip()
    if not database_url:
        pytest.skip("TANIM_TEST_DATABASE_URL is required for PostgreSQL integration tests")

    schema = f"tanim_phase4_auth_{uuid.uuid4().hex}"
    with psycopg.connect(database_url) as connection:
        connection.execute(SQL("CREATE SCHEMA {}").format(Identifier(schema)))
        _set_search_path(connection, schema)
        for migration in sorted(MIGRATION_DIR.glob("[0-9][0-9][0-9]_*.sql")):
            connection.execute(migration.read_text(encoding="utf-8"), prepare=False)

    def connection_factory(url: str, **kwargs):
        connection = psycopg.connect(url, **kwargs)
        _set_search_path(connection, schema)
        return connection

    store = AuthStore(database_url, connection_factory=connection_factory)
    try:
        yield store, connection_factory
    finally:
        with psycopg.connect(database_url) as connection:
            connection.execute(SQL("DROP SCHEMA {} CASCADE").format(Identifier(schema)))


def _request(store: AuthStore, method: str, path: str, **kwargs) -> httpx.Response:
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


def _registration_payload(email: str, role: str = "farmer") -> dict[str, object]:
    return {
        "display_name": "Integration User",
        "email": email,
        "password": "integration-password",
        "role": role,
        "privacy_notice_version": PRIVACY_NOTICE_VERSION,
        "privacy_accepted": True,
        "optional_data_improvement_consent": role == "cooperative",
        "preferred_language": "tl",
        "organization_name": "Integration Cooperative" if role == "cooperative" else None,
    }


def test_registration_is_transactional_and_stores_only_argon2_hash(isolated_auth_store):
    store, connection_factory = isolated_auth_store
    response = _request(
        store,
        "POST",
        "/auth/register",
        json=_registration_payload(" Farmer@Example.com "),
    )

    assert response.status_code == 200
    raw_token = response.cookies.get("tanim_session")
    assert raw_token
    with connection_factory(store.database_url) as connection:
        user = connection.execute(
            "SELECT id, email, password_hash, has_completed_demo FROM users"
        ).fetchone()
        consent = connection.execute(
            """
            SELECT privacy_notice_version, optional_data_improvement_consent
            FROM privacy_consents WHERE user_id = %s
            """,
            (user[0],),
        ).fetchone()
        session = connection.execute(
            "SELECT session_token_hash FROM auth_sessions WHERE user_id = %s",
            (user[0],),
        ).fetchone()
    assert user[1] == "farmer@example.com"
    assert user[2].startswith("$argon2id$")
    assert user[3] is False
    assert consent == (PRIVACY_NOTICE_VERSION, False)
    assert session[0] == hash_session_secret(raw_token)
    assert raw_token not in session[0]


def test_cooperative_registration_creates_membership_and_optional_consent(isolated_auth_store):
    store, connection_factory = isolated_auth_store
    response = _request(
        store,
        "POST",
        "/auth/register",
        json=_registration_payload("coop@example.com", role="cooperative"),
    )

    assert response.status_code == 200
    with connection_factory(store.database_url) as connection:
        membership = connection.execute(
            """
            SELECT om.user_id, o.name
            FROM organization_members AS om
            JOIN organizations AS o ON o.id = om.organization_id
            """
        ).fetchone()
        consent = connection.execute(
            "SELECT optional_data_improvement_consent FROM privacy_consents"
        ).fetchone()
    assert membership[1] == "Integration Cooperative"
    assert consent == (True,)


def test_expired_and_revoked_sessions_are_unauthenticated(isolated_auth_store):
    store, connection_factory = isolated_auth_store
    response = _request(
        store,
        "POST",
        "/auth/register",
        json=_registration_payload("expire@example.com"),
    )
    raw_token = response.cookies.get("tanim_session")
    assert raw_token
    with connection_factory(store.database_url) as connection:
        connection.execute(
            "UPDATE auth_sessions SET expires_at = NOW() - INTERVAL '1 minute'"
        )
    expired = _request(store, "GET", "/auth/session", cookies={"tanim_session": raw_token})
    assert expired.json()["authenticated"] is False

    login = _request(
        store,
        "POST",
        "/auth/login",
        json={"email": "expire@example.com", "password": "integration-password"},
    )
    token = login.cookies.get("tanim_session")
    assert token
    session = _request(store, "GET", "/auth/session", cookies={"tanim_session": token})
    csrf = session.json()["csrf_token"]
    logout = _request(
        store,
        "POST",
        "/auth/logout",
        cookies={"tanim_session": token},
        headers={"X-CSRF-Token": csrf},
    )
    assert logout.status_code == 200
    revoked = _request(store, "GET", "/auth/session", cookies={"tanim_session": token})
    assert revoked.json()["authenticated"] is False


def test_demo_completion_is_csrf_protected_and_writes_no_plan(isolated_auth_store):
    store, connection_factory = isolated_auth_store
    response = _request(
        store,
        "POST",
        "/auth/register",
        json=_registration_payload("demo@example.com"),
    )
    token = response.cookies.get("tanim_session")
    assert token
    session = _request(store, "GET", "/auth/session", cookies={"tanim_session": token})
    csrf = session.json()["csrf_token"]

    blocked = _request(store, "POST", "/demo/complete", cookies={"tanim_session": token})
    assert blocked.status_code == 403
    completed = _request(
        store,
        "POST",
        "/demo/complete",
        cookies={"tanim_session": token},
        headers={"X-CSRF-Token": csrf},
    )
    repeated = _request(
        store,
        "POST",
        "/demo/complete",
        cookies={"tanim_session": token},
        headers={"X-CSRF-Token": csrf},
    )
    assert completed.json() == {"has_completed_demo": True}
    assert repeated.json() == {"has_completed_demo": True}
    with connection_factory(store.database_url) as connection:
        assert connection.execute("SELECT count(*) FROM planting_plans").fetchone()[0] == 0
        assert connection.execute("SELECT has_completed_demo FROM users").fetchone() == (True,)


def test_demo_account_seeding_is_repeat_safe_and_conflict_safe(isolated_auth_store):
    store, connection_factory = isolated_auth_store
    with connection_factory(store.database_url) as connection:
        assert seed_demo_accounts(connection, "farmer-seed-password", "coop-seed-password") == [
            "created",
            "created",
        ]
    with connection_factory(store.database_url) as connection:
        assert seed_demo_accounts(connection, "different-password", "different-password") == [
            "already present",
            "already present",
        ]
        assert connection.execute("SELECT count(*) FROM users").fetchone() == (2,)
        connection.execute(
            "UPDATE users SET display_name = 'Changed' WHERE email = 'farmer.demo@tanim.local'"
        )
    with connection_factory(store.database_url) as connection:
        with pytest.raises(DemoAccountSeedError, match="conflicting existing account"):
            seed_demo_accounts(connection, "farmer-seed-password", "coop-seed-password")
