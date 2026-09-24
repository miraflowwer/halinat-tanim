"""Create the two repeat-safe development demo accounts."""

import os
import sys
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.api.auth import normalize_email  # noqa: E402
from services.api.config import (  # noqa: E402
    DEMO_COOPERATIVE_EMAIL,
    DEMO_FARMER_EMAIL,
    PRIVACY_NOTICE_VERSION,
)
from services.api.passwords import hash_password  # noqa: E402


class DemoAccountSeedError(RuntimeError):
    """A safe, actionable demo-account seed failure."""


DEMO_ACCOUNTS = (
    {
        "email": DEMO_FARMER_EMAIL,
        "display_name": "TANIM Demo Farmer",
        "role": "farmer",
        "password_env": "TANIM_DEMO_FARMER_PASSWORD",
    },
    {
        "email": DEMO_COOPERATIVE_EMAIL,
        "display_name": "TANIM Demo Cooperative",
        "role": "cooperative",
        "password_env": "TANIM_DEMO_COOP_PASSWORD",
    },
)


def _existing_user(connection: Any, email: str) -> tuple[Any, ...] | None:
    return connection.execute(
        """
        SELECT id, display_name, role
        FROM users
        WHERE LOWER(email) = LOWER(%s)
        LIMIT 1
        """,
        (email,),
    ).fetchone()


def _ensure_demo_account(connection: Any, account: dict[str, str], password: str) -> str:
    email = normalize_email(account["email"])
    existing = _existing_user(connection, email)
    if existing:
        if existing[1] != account["display_name"] or existing[2] != account["role"]:
            raise DemoAccountSeedError(
                f"The configured demo email {email} belongs to a conflicting existing account."
            )
        consent = connection.execute(
            """
            SELECT 1 FROM privacy_consents
            WHERE user_id = %s AND privacy_notice_version = %s
            LIMIT 1
            """,
            (existing[0], PRIVACY_NOTICE_VERSION),
        ).fetchone()
        if consent is None:
            raise DemoAccountSeedError(
                f"The existing demo account {email} has no current privacy consent."
            )
        return "already present"

    user = connection.execute(
        """
        INSERT INTO users (email, password_hash, display_name, role, preferred_language)
        VALUES (%s, %s, %s, %s, 'en')
        RETURNING id
        """,
        (email, hash_password(password), account["display_name"], account["role"]),
    ).fetchone()
    if user is None:
        raise DemoAccountSeedError("A demo account could not be created.")
    connection.execute(
        """
        INSERT INTO privacy_consents (
            user_id, privacy_notice_version, optional_data_improvement_consent
        ) VALUES (%s, %s, FALSE)
        """,
        (user[0], PRIVACY_NOTICE_VERSION),
    )
    if account["role"] == "cooperative":
        organization = connection.execute(
            """
            INSERT INTO organizations (name, organization_type)
            VALUES ('TANIM Demo Cooperative', 'cooperative')
            RETURNING id
            """
        ).fetchone()
        if organization is None:
            raise DemoAccountSeedError("The cooperative demo account could not be created.")
        connection.execute(
            """
            INSERT INTO organization_members (organization_id, user_id)
            VALUES (%s, %s)
            """,
            (organization[0], user[0]),
        )
    return "created"


def seed_demo_accounts(
    connection: Any,
    farmer_password: str,
    cooperative_password: str,
) -> list[str]:
    """Seed both accounts in the caller's transaction."""
    passwords = [farmer_password, cooperative_password]
    results = []
    for account, password in zip(DEMO_ACCOUNTS, passwords, strict=True):
        results.append(_ensure_demo_account(connection, account, password))
    return results


def main() -> int:
    load_dotenv(ROOT / ".env", override=False)
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        print("Demo-account seeding stopped: DATABASE_URL is not configured.", file=sys.stderr)
        return 1
    passwords = [os.getenv(account["password_env"], "") for account in DEMO_ACCOUNTS]
    missing = [
        account["password_env"]
        for account, password in zip(DEMO_ACCOUNTS, passwords, strict=True)
        if not password
    ]
    if missing:
        print(
            "Demo-account seeding stopped: set the required password variables in .env: "
            + ", ".join(missing),
            file=sys.stderr,
        )
        return 1
    try:
        with psycopg.connect(database_url, connect_timeout=5) as connection:
            results = seed_demo_accounts(connection, passwords[0], passwords[1])
    except DemoAccountSeedError as error:
        print(f"Demo-account seeding stopped: {error}", file=sys.stderr)
        return 1
    except psycopg.OperationalError as error:
        print(
            "Demo-account seeding failed: PostgreSQL is not reachable. "
            f"Check the local database ({type(error).__name__}).",
            file=sys.stderr,
        )
        return 1
    except psycopg.Error as error:
        print(
            "Demo-account seeding failed while writing PostgreSQL. "
            f"Check the local database ({type(error).__name__}).",
            file=sys.stderr,
        )
        return 1
    except ValueError:
        print(
            "Demo-account seeding stopped: a configured demo password is invalid. "
            "Use at least 8 characters.",
            file=sys.stderr,
        )
        return 1

    print(
        "Demo-account seeding complete: farmer.demo@tanim.local and "
        f"coop.demo@tanim.local ({', '.join(results)})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
