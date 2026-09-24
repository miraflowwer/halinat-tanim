"""PostgreSQL-backed authentication, consent, and session operations."""

import hashlib
import hmac
import logging
import os
import re
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import psycopg

from .config import PRIVACY_NOTICE_VERSION, SESSION_LIFETIME
from .passwords import hash_password, password_needs_rehash, verify_password

logger = logging.getLogger(__name__)

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_ALLOWED_ROLES = {"farmer", "cooperative"}
_ALLOWED_LANGUAGES = {"en", "tl"}


class AuthError(RuntimeError):
    """A safe, machine-readable authentication failure."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class AuthUser:
    user_id: int
    display_name: str
    email: str
    role: str
    preferred_language: str
    has_completed_demo: bool


@dataclass(frozen=True)
class AuthenticatedSession:
    session_id: int
    user: AuthUser
    session_token_hash: str
    csrf_token_hash: str
    expires_at: datetime
    csrf_token: str | None = None


@dataclass(frozen=True)
class AuthResult:
    user: AuthUser
    session_token: str
    csrf_token: str


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if not _EMAIL_PATTERN.fullmatch(normalized):
        raise ValueError("email must be a valid email address")
    return normalized


def hash_session_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def derive_csrf_token(session_token: str) -> str:
    """Derive one stable CSRF token from the HttpOnly session secret."""
    return hmac.new(
        b"tanim-csrf-v1",
        session_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_csrf_token(session: AuthenticatedSession, csrf_token: str | None) -> bool:
    if not csrf_token:
        return False
    return hmac.compare_digest(session.csrf_token_hash, hash_session_secret(csrf_token))


def _utc_now() -> datetime:
    return datetime.now(UTC)


class AuthStore:
    """Keep SQL and transaction boundaries in one small authentication adapter."""

    def __init__(
        self,
        database_url: str,
        *,
        connection_factory: Callable[..., Any] | None = None,
    ):
        self.database_url = database_url.strip()
        self.connection_factory = connection_factory or psycopg.connect

    @classmethod
    def from_environment(cls) -> "AuthStore":
        return cls(os.getenv("DATABASE_URL", ""))

    def _connection(self) -> Any:
        if not self.database_url:
            raise AuthError(
                "DATABASE_UNAVAILABLE",
                (
                    "TANIM cannot connect to the local data service right now. "
                    "Check PostgreSQL and retry."
                ),
                503,
            )
        try:
            return self.connection_factory(self.database_url, connect_timeout=5)
        except (psycopg.Error, ValueError):
            logger.warning("Authentication database connection failed.")
            raise AuthError(
                "DATABASE_UNAVAILABLE",
                (
                    "TANIM cannot connect to the local data service right now. "
                    "Check PostgreSQL and retry."
                ),
                503,
            ) from None

    @staticmethod
    def _user_from_row(row: tuple[Any, ...]) -> AuthUser:
        return AuthUser(
            user_id=int(row[0]),
            email=str(row[1]),
            display_name=str(row[2]),
            role=str(row[3]),
            preferred_language=str(row[4]),
            has_completed_demo=bool(row[5]),
        )

    @staticmethod
    def _cleanup_sessions(connection: Any) -> None:
        connection.execute(
            """
            DELETE FROM auth_sessions
            WHERE revoked_at IS NOT NULL OR expires_at <= NOW()
            """
        )

    @staticmethod
    def _create_session(connection: Any, user_id: int) -> tuple[str, str]:
        session_token = secrets.token_urlsafe(32)
        csrf_token = derive_csrf_token(session_token)
        expires_at = _utc_now() + SESSION_LIFETIME
        connection.execute(
            """
            INSERT INTO auth_sessions (
                user_id, session_token_hash, csrf_token_hash, expires_at
            ) VALUES (%s, %s, %s, %s)
            """,
            (
                user_id,
                hash_session_secret(session_token),
                hash_session_secret(csrf_token),
                expires_at,
            ),
        )
        return session_token, csrf_token

    def register(
        self,
        *,
        display_name: str,
        email: str,
        password: str,
        role: str,
        privacy_notice_version: str,
        privacy_accepted: bool,
        optional_data_improvement_consent: bool,
        preferred_language: str = "en",
        organization_name: str | None = None,
    ) -> AuthResult:
        cleaned_name = display_name.strip()
        if not cleaned_name:
            raise AuthError("INVALID_DISPLAY_NAME", "Name is required.")
        try:
            normalized_email = normalize_email(email)
        except ValueError:
            raise AuthError("INVALID_EMAIL", "Enter a valid email address.") from None
        if role not in _ALLOWED_ROLES:
            raise AuthError("INVALID_ROLE", "Choose Farmer or Cooperative.")
        if preferred_language not in _ALLOWED_LANGUAGES:
            raise AuthError("INVALID_LANGUAGE", "Choose English or Tagalog.")
        if privacy_notice_version != PRIVACY_NOTICE_VERSION:
            raise AuthError(
                "PRIVACY_NOTICE_VERSION_UNSUPPORTED",
                (
                    "This privacy notice version is no longer supported. "
                    "Open the privacy notice again."
                ),
            )
        if not privacy_accepted:
            raise AuthError(
                "PRIVACY_CONSENT_REQUIRED",
                "You must accept the Privacy Notice before creating an account.",
            )
        try:
            password_hash = hash_password(password)
        except ValueError:
            raise AuthError(
                "INVALID_PASSWORD",
                "Password must be at least 8 characters and must not be blank.",
            ) from None

        cleaned_organization = (organization_name or "").strip() or None
        if role == "cooperative" and cleaned_organization is None:
            raise AuthError(
                "COOPERATIVE_ORGANIZATION_REQUIRED",
                "Cooperative accounts need an organization name.",
            )
        connection = self._connection()
        try:
            with connection:
                self._cleanup_sessions(connection)
                existing = connection.execute(
                    "SELECT 1 FROM users WHERE LOWER(email) = LOWER(%s) LIMIT 1",
                    (normalized_email,),
                ).fetchone()
                if existing:
                    raise AuthError(
                        "EMAIL_ALREADY_REGISTERED",
                        "An account with this email is already registered.",
                    )
                row = connection.execute(
                    """
                    INSERT INTO users (email, password_hash, display_name, role, preferred_language)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, email, display_name, role, preferred_language, has_completed_demo
                    """,
                    (normalized_email, password_hash, cleaned_name, role, preferred_language),
                ).fetchone()
                if row is None:
                    raise AuthError("REGISTRATION_FAILED", "The account could not be created.", 500)
                user = self._user_from_row(row)
                connection.execute(
                    """
                    INSERT INTO privacy_consents (
                        user_id, privacy_notice_version, optional_data_improvement_consent
                    ) VALUES (%s, %s, %s)
                    """,
                    (user.user_id, PRIVACY_NOTICE_VERSION, optional_data_improvement_consent),
                )
                if role == "cooperative" and cleaned_organization:
                    organization = connection.execute(
                        """
                        INSERT INTO organizations (name, organization_type)
                        VALUES (%s, 'cooperative')
                        RETURNING id
                        """,
                        (cleaned_organization,),
                    ).fetchone()
                    if organization is None:
                        raise AuthError(
                            "REGISTRATION_FAILED",
                            "The account could not be created.",
                            500,
                        )
                    connection.execute(
                        """
                        INSERT INTO organization_members (organization_id, user_id)
                        VALUES (%s, %s)
                        """,
                        (organization[0], user.user_id),
                    )
                session_token, csrf_token = self._create_session(connection, user.user_id)
                return AuthResult(user=user, session_token=session_token, csrf_token=csrf_token)
        except AuthError:
            raise
        except psycopg.errors.UniqueViolation:
            raise AuthError(
                "EMAIL_ALREADY_REGISTERED",
                "An account with this email is already registered.",
            ) from None
        except psycopg.Error as error:
            logger.warning("Registration database operation failed (%s).", type(error).__name__)
            raise AuthError(
                "DATABASE_UNAVAILABLE",
                "TANIM cannot save the account right now. Check PostgreSQL and retry.",
                503,
            ) from None
        finally:
            connection.close()

    def login(self, *, email: str, password: str) -> AuthResult:
        try:
            normalized_email = normalize_email(email)
        except ValueError:
            raise AuthError("INVALID_CREDENTIALS", "Email or password is incorrect.", 401) from None
        connection = self._connection()
        try:
            with connection:
                row = connection.execute(
                    """
                    SELECT id, email, display_name, role, preferred_language,
                           has_completed_demo, password_hash
                    FROM users
                    WHERE LOWER(email) = LOWER(%s)
                    LIMIT 1
                    """,
                    (normalized_email,),
                ).fetchone()
                if row is None or not verify_password(password, row[6]):
                    raise AuthError("INVALID_CREDENTIALS", "Email or password is incorrect.", 401)
                if password_needs_rehash(row[6]):
                    connection.execute(
                        "UPDATE users SET password_hash = %s WHERE id = %s",
                        (hash_password(password), row[0]),
                    )
                self._cleanup_sessions(connection)
                user = self._user_from_row(row)
                session_token, csrf_token = self._create_session(connection, user.user_id)
                return AuthResult(user=user, session_token=session_token, csrf_token=csrf_token)
        except AuthError:
            raise
        except psycopg.Error as error:
            logger.warning("Login database operation failed (%s).", type(error).__name__)
            raise AuthError(
                "DATABASE_UNAVAILABLE",
                "TANIM cannot sign you in right now. Check PostgreSQL and retry.",
                503,
            ) from None
        finally:
            connection.close()

    def get_session(
        self,
        session_token: str | None,
        *,
        rotate_csrf: bool = False,
    ) -> AuthenticatedSession | None:
        if not session_token:
            return None
        connection = self._connection()
        try:
            with connection:
                row = connection.execute(
                    """
                    SELECT s.id, s.session_token_hash, s.csrf_token_hash, s.expires_at,
                           u.id, u.email, u.display_name, u.role,
                           u.preferred_language, u.has_completed_demo
                    FROM auth_sessions AS s
                    JOIN users AS u ON u.id = s.user_id
                    WHERE s.session_token_hash = %s
                      AND s.revoked_at IS NULL
                      AND s.expires_at > NOW()
                    LIMIT 1
                    """,
                    (hash_session_secret(session_token),),
                ).fetchone()
                if row is None:
                    return None
                # Keep the token stable for the lifetime of the session. The
                # argument remains for compatibility with older callers, but
                # restoring a session must not invalidate another browser tab.
                csrf_token = derive_csrf_token(session_token)
                connection.execute(
                    "UPDATE auth_sessions SET last_seen_at = NOW() WHERE id = %s",
                    (row[0],),
                )
                return AuthenticatedSession(
                    session_id=int(row[0]),
                    session_token_hash=str(row[1]),
                    csrf_token_hash=str(row[2]),
                    expires_at=row[3],
                    user=self._user_from_row(row[4:10]),
                    csrf_token=csrf_token,
                )
        except psycopg.Error as error:
            logger.warning("Session lookup failed (%s).", type(error).__name__)
            raise AuthError(
                "DATABASE_UNAVAILABLE",
                "TANIM cannot restore your session right now. Check PostgreSQL and retry.",
                503,
            ) from None
        finally:
            connection.close()

    def revoke_session(self, session: AuthenticatedSession) -> None:
        connection = self._connection()
        try:
            with connection:
                connection.execute(
                    """
                    UPDATE auth_sessions
                    SET revoked_at = COALESCE(revoked_at, NOW()), last_seen_at = NOW()
                    WHERE id = %s AND user_id = %s
                    """,
                    (session.session_id, session.user.user_id),
                )
        except psycopg.Error as error:
            logger.warning("Session revocation failed (%s).", type(error).__name__)
            raise AuthError(
                "DATABASE_UNAVAILABLE",
                "TANIM could not finish logout. Check PostgreSQL and retry.",
                503,
            ) from None
        finally:
            connection.close()

    def complete_demo(self, user_id: int) -> bool:
        connection = self._connection()
        try:
            with connection:
                row = connection.execute(
                    """
                    UPDATE users
                    SET has_completed_demo = TRUE
                    WHERE id = %s
                    RETURNING has_completed_demo
                    """,
                    (user_id,),
                ).fetchone()
                if row is None:
                    raise AuthError("UNAUTHENTICATED", "Please sign in to continue.", 401)
                return bool(row[0])
        except AuthError:
            raise
        except psycopg.Error as error:
            logger.warning("Demo completion update failed (%s).", type(error).__name__)
            raise AuthError(
                "DATABASE_UNAVAILABLE",
                "TANIM could not save demo completion. Check PostgreSQL and retry.",
                503,
            ) from None
        finally:
            connection.close()

    def update_preferred_language(self, user_id: int, preferred_language: str) -> AuthUser:
        if preferred_language not in _ALLOWED_LANGUAGES:
            raise AuthError("INVALID_LANGUAGE", "Choose English or Tagalog.")
        connection = self._connection()
        try:
            with connection:
                row = connection.execute(
                    """
                    UPDATE users
                    SET preferred_language = %s
                    WHERE id = %s
                    RETURNING id, email, display_name, role, preferred_language,
                              has_completed_demo
                    """,
                    (preferred_language, user_id),
                ).fetchone()
                if row is None:
                    raise AuthError("UNAUTHENTICATED", "Please sign in to continue.", 401)
                return self._user_from_row(row)
        except AuthError:
            raise
        except psycopg.Error as error:
            logger.warning("Language preference update failed (%s).", type(error).__name__)
            raise AuthError(
                "DATABASE_UNAVAILABLE",
                "TANIM could not save your language preference. Check PostgreSQL and retry.",
                503,
            ) from None
        finally:
            connection.close()

    def get_membership(self, user_id: int) -> dict[str, Any] | None:
        connection = self._connection()
        try:
            with connection:
                row = connection.execute(
                    """
                    SELECT o.id, o.name, o.join_code
                    FROM organization_members AS om
                    JOIN organizations AS o ON o.id = om.organization_id
                    WHERE om.user_id = %s
                    """,
                    (user_id,),
                ).fetchone()
                if row is None:
                    return None
                return {
                    "organization_id": int(row[0]),
                    "organization_name": str(row[1]),
                    "join_code": str(row[2]),
                }
        except psycopg.Error as error:
            logger.warning("Membership lookup failed (%s).", type(error).__name__)
            raise AuthError(
                "DATABASE_UNAVAILABLE",
                "TANIM could not load cooperative membership. Check PostgreSQL and retry.",
                503,
            ) from None
        finally:
            connection.close()

    def join_organization(self, user_id: int, join_code: str) -> dict[str, Any]:
        normalized_code = join_code.strip().upper()
        if not normalized_code:
            raise AuthError("INVALID_JOIN_CODE", "Enter a cooperative join code.")
        connection = self._connection()
        try:
            with connection:
                user = connection.execute(
                    "SELECT role FROM users WHERE id = %s FOR UPDATE",
                    (user_id,),
                ).fetchone()
                if user is None:
                    raise AuthError("UNAUTHENTICATED", "Please sign in to continue.", 401)
                if user[0] != "farmer":
                    raise AuthError(
                        "FARMER_ROLE_REQUIRED",
                        "Only Farmer accounts can join a cooperative.",
                        403,
                    )
                existing = connection.execute(
                    "SELECT 1 FROM organization_members WHERE user_id = %s LIMIT 1",
                    (user_id,),
                ).fetchone()
                if existing is not None:
                    raise AuthError(
                        "MEMBERSHIP_ALREADY_EXISTS",
                        "This Farmer account already belongs to a cooperative.",
                        409,
                    )
                organization = connection.execute(
                    """
                    SELECT id, name, join_code
                    FROM organizations
                    WHERE UPPER(join_code) = %s
                    LIMIT 1
                    """,
                    (normalized_code,),
                ).fetchone()
                if organization is None:
                    raise AuthError("INVALID_JOIN_CODE", "That cooperative join code is not valid.")
                try:
                    connection.execute(
                        """
                        INSERT INTO organization_members (organization_id, user_id)
                        VALUES (%s, %s)
                        """,
                        (organization[0], user_id),
                    )
                except psycopg.errors.UniqueViolation:
                    raise AuthError(
                        "MEMBERSHIP_ALREADY_EXISTS",
                        "This Farmer account already belongs to a cooperative.",
                        409,
                    ) from None
                connection.execute(
                    """
                    UPDATE planting_plans
                    SET organization_id = %s, updated_at = NOW()
                    WHERE user_id = %s AND organization_id IS NULL AND status = 'active'
                    """,
                    (organization[0], user_id),
                )
                return {
                    "organization_id": int(organization[0]),
                    "organization_name": str(organization[1]),
                    "join_code": str(organization[2]),
                }
        except AuthError:
            raise
        except psycopg.Error as error:
            logger.warning("Cooperative join failed (%s).", type(error).__name__)
            raise AuthError(
                "DATABASE_UNAVAILABLE",
                "TANIM could not join the cooperative. Check PostgreSQL and retry.",
                503,
            ) from None
        finally:
            connection.close()

    def cleanup_sessions(self) -> int:
        connection = self._connection()
        try:
            with connection:
                cursor = connection.execute(
                    """
                    DELETE FROM auth_sessions
                    WHERE revoked_at IS NOT NULL OR expires_at <= NOW()
                    """
                )
                return cursor.rowcount
        except psycopg.Error as error:
            logger.warning("Session cleanup failed (%s).", type(error).__name__)
            raise AuthError(
                "DATABASE_UNAVAILABLE",
                "TANIM could not clean old sessions. Check PostgreSQL and retry.",
                503,
            ) from None
        finally:
            connection.close()
