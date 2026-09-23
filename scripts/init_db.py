"""Apply all numbered database migrations once, without destructive operations."""

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "data" / "migrations"


def main() -> int:
    load_dotenv(ROOT / ".env", override=False)
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        print(
            "Database initialization stopped: DATABASE_URL is not set in .env or the environment."
        )
        return 1

    migrations = sorted(MIGRATION_DIR.glob("[0-9][0-9][0-9]_*.sql"))
    if not migrations:
        print(f"Database initialization stopped: no migrations were found in {MIGRATION_DIR}")
        return 1

    try:
        with psycopg.connect(database_url, connect_timeout=5) as connection:
            connection.execute("SELECT pg_advisory_lock(732041, 1)")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tanim_schema_migrations (
                    migration_name TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            applied = []
            skipped = []
            for migration in migrations:
                migration_name = migration.name
                already_applied = connection.execute(
                    "SELECT 1 FROM tanim_schema_migrations WHERE migration_name = %s",
                    (migration_name,),
                ).fetchone()
                if already_applied:
                    skipped.append(migration_name)
                    continue
                migration_sql = migration.read_text(encoding="utf-8")
                connection.execute(migration_sql, prepare=False)
                connection.execute(
                    "INSERT INTO tanim_schema_migrations (migration_name) VALUES (%s)",
                    (migration_name,),
                )
                applied.append(migration_name)
            connection.execute("SELECT pg_advisory_unlock(732041, 1)")
    except psycopg.OperationalError as error:
        print(
            "Database initialization failed: PostgreSQL is not reachable. "
            f"Check DATABASE_URL and the local server ({type(error).__name__})."
        )
        return 1
    except psycopg.Error as error:
        code = error.sqlstate or "unknown"
        print(
            "Database initialization failed while applying a migration "
            f"(SQLSTATE {code}). Check the database permissions and migration files."
        )
        return 1
    except ValueError:
        print(
            "Database initialization failed: DATABASE_URL is not a valid PostgreSQL connection URL."
        )
        return 1

    if applied:
        print(f"Database initialization complete. Applied: {', '.join(applied)}.")
    else:
        print(f"Database is ready. Already applied: {', '.join(skipped)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
