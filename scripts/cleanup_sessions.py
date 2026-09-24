"""Remove revoked and expired TANIM authentication sessions."""

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.api.auth import AuthError, AuthStore  # noqa: E402


def main() -> int:
    load_dotenv(ROOT / ".env", override=False)
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        print("Session cleanup stopped: DATABASE_URL is not configured.", file=sys.stderr)
        return 1
    try:
        removed = AuthStore(database_url).cleanup_sessions()
    except (AuthError, psycopg.Error):
        print("Session cleanup failed: PostgreSQL is not reachable.", file=sys.stderr)
        return 1
    print(f"Session cleanup complete: removed {removed} old session(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
