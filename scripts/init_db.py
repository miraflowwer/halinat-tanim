"""Apply the baseline database migration once, without destructive operations."""

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "data" / "migrations" / "001_foundation.sql"
MIGRATION_NAME = MIGRATION.name


def main() -> int:
    load_dotenv(ROOT / ".env", override=False)
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        print(
            "Database initialization stopped: DATABASE_URL is not set in .env or the environment."
        )
        return 1

    if not MIGRATION.is_file():
        print(f"Database initialization stopped: migration file is missing: {MIGRATION}")
        return 1

    migration_sql = MIGRATION.read_text(encoding="utf-8")
    try:
        with psycopg.connect(database_url, connect_timeout=5) as connection:
            connection.execute("SELECT pg_advisory_xact_lock(732041, 1)")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tanim_schema_migrations (
                    migration_name TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            already_applied = connection.execute(
                "SELECT 1 FROM tanim_schema_migrations WHERE migration_name = %s",
                (MIGRATION_NAME,),
            ).fetchone()
            if already_applied:
                print(f"Database is ready. {MIGRATION_NAME} was already applied.")
                return 0

            connection.execute(migration_sql, prepare=False)
            connection.execute(
                "INSERT INTO tanim_schema_migrations (migration_name) VALUES (%s)",
                (MIGRATION_NAME,),
            )
    except psycopg.OperationalError as error:
        print(
            "Database initialization failed: PostgreSQL is not reachable. "
            f"Check DATABASE_URL and the local server ({type(error).__name__})."
        )
        return 1
    except psycopg.Error as error:
        code = error.sqlstate or "unknown"
        print(
            f"Database initialization failed while applying {MIGRATION_NAME} "
            f"(SQLSTATE {code}). Check the database permissions and migration."
        )
        return 1
    except ValueError:
        print(
            "Database initialization failed: DATABASE_URL is not a valid PostgreSQL connection URL."
        )
        return 1

    print(f"Database initialization complete. Applied {MIGRATION_NAME}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
