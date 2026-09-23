import asyncio

import httpx
import psycopg

from services.api.app import app


def request(path: str) -> httpx.Response:
    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(path)

    return asyncio.run(send_request())


def test_health_does_not_require_a_database(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("The API health endpoint must not connect to PostgreSQL.")

    monkeypatch.setattr("services.api.app.psycopg.connect", fail_if_called)
    response = request("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_database_health_returns_safe_failure(monkeypatch):
    connection_url = "postgresql://tanim@127.0.0.1:65432/tanim"
    monkeypatch.setenv("DATABASE_URL", connection_url)

    def fail_connection(*args, **kwargs):
        raise psycopg.OperationalError("connection refused")

    monkeypatch.setattr("services.api.app.psycopg.connect", fail_connection)
    response = request("/health/db")

    assert response.status_code == 503
    assert response.json()["detail"]["status"] == "unhealthy"
    assert response.json()["detail"]["database"] == "unavailable"
    assert connection_url not in response.text
    assert "tanim@" not in response.text
