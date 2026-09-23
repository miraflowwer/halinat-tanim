import logging
import os

import psycopg
from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)
app = FastAPI(title="TANIM API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the API process can serve requests."""
    return {"status": "healthy"}


@app.get("/health/db")
def database_health() -> dict[str, str]:
    """Check PostgreSQL without returning connection details to the caller."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "unavailable",
                "message": "DATABASE_URL is not configured.",
            },
        )

    try:
        with psycopg.connect(database_url, connect_timeout=3) as connection:
            connection.execute("SELECT 1")
    except (psycopg.Error, ValueError) as error:
        logger.warning("Database health check failed (%s).", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "unavailable",
                "message": "PostgreSQL is not reachable. Check DATABASE_URL and the local server.",
            },
        ) from None

    return {"status": "healthy", "database": "reachable"}
