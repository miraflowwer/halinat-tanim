import asyncio
import os
import uuid
from datetime import date
from pathlib import Path

import httpx
import psycopg
import pytest
from psycopg.sql import SQL, Identifier
from psycopg.types.json import Jsonb

import services.api.app as api_module
from services.engine.config import EngineConfig, load_engine_config
from services.engine.models import RiskCheckInput
from services.engine.repository import DatasetNotReadyError, PostgresRiskRepository
from services.engine.service import RiskService

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "data" / "migrations"


def _set_search_path(connection, schema: str) -> None:
    connection.execute(SQL("SET search_path TO {}, public").format(Identifier(schema)))


@pytest.fixture
def isolated_risk_service():
    database_url = os.getenv("TANIM_TEST_DATABASE_URL", "").strip()
    if not database_url:
        pytest.skip("TANIM_TEST_DATABASE_URL is required for PostgreSQL integration tests")

    schema = f"tanim_phase3_{uuid.uuid4().hex}"
    with psycopg.connect(database_url) as connection:
        connection.execute(SQL("CREATE SCHEMA {}").format(Identifier(schema)))
        _set_search_path(connection, schema)
        for migration in sorted(MIGRATION_DIR.glob("[0-9][0-9][0-9]_*.sql")):
            connection.execute(migration.read_text(encoding="utf-8"), prepare=False)
        _seed_isolated_rows(connection)

    def connection_factory(url: str, **kwargs):
        connection = psycopg.connect(url, **kwargs)
        _set_search_path(connection, schema)
        return connection

    repository = PostgresRiskRepository(
        database_url,
        connection_factory=connection_factory,
    )
    service = RiskService(repository, load_engine_config())
    try:
        yield service
    finally:
        with psycopg.connect(database_url) as connection:
            connection.execute(SQL("DROP SCHEMA {} CASCADE").format(Identifier(schema)))


def _seed_isolated_rows(connection) -> None:
    dataset_version = "demo-2026-09-v4"
    user_id = connection.execute(
        """
        INSERT INTO users (email, password_hash, display_name, role)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (f"phase3-{uuid.uuid4().hex}@test.invalid", "not-used", "Phase 3", "farmer"),
    ).fetchone()[0]
    connection.execute(
        """
        INSERT INTO crops (crop_id, canonical_name_en, category, active)
        VALUES
            ('tomato', 'Tomato', 'vegetable', TRUE),
            ('eggplant', 'Eggplant', 'vegetable', TRUE)
        """
    )
    connection.execute(
        """
        INSERT INTO geographies (
            name, level, code, country, island_group, active, geography_id
        ) VALUES (%s, 'municipality_city', %s, 'Philippines', 'Luzon', TRUE, %s)
        """,
        ("Cabanatuan City", "0304903000", "mun_0304903000"),
    )
    geography_id = connection.execute(
        "SELECT id FROM geographies WHERE geography_id = %s",
        ("mun_0304903000",),
    ).fetchone()[0]
    connection.execute(
        """
        INSERT INTO dataset_metadata (
            dataset_version, data_kind, seed, manifest_sha256, metadata
        ) VALUES (%s, 'synthetic_demo', %s, %s, %s)
        """,
        (dataset_version, 20260924, "0" * 64, Jsonb({"dataset_version": dataset_version})),
    )
    connection.executemany(
        """
        INSERT INTO crop_references (
            crop_id, geography_id, period_start, period_end, period_kind,
            reference_area_ha, area_unit, data_kind, dataset_version
        ) VALUES (%s, %s, %s, %s, 'future_planning', %s, 'ha', 'synthetic_demo', %s)
        """,
        [
            ("tomato", geography_id, date(2027, 1, 1), date(2027, 3, 31), 25, dataset_version),
            ("eggplant", geography_id, date(2027, 1, 1), date(2027, 3, 31), 18, dataset_version),
        ],
    )
    connection.executemany(
        """
        INSERT INTO planting_plans (
            user_id, crop_id, geography_id, area_ha, planting_date,
            harvest_start, harvest_end, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        [
            (
                user_id, "tomato", geography_id, 8, date(2026, 10, 1),
                date(2027, 1, 1), date(2027, 1, 31), "active"
            ),
            (
                user_id, "tomato", geography_id, 8, date(2026, 10, 1),
                date(2027, 2, 1), date(2027, 2, 28), "active"
            ),
            (
                user_id, "tomato", geography_id, 8, date(2026, 10, 1),
                date(2027, 3, 1), date(2027, 3, 31), "active"
            ),
            (
                user_id, "tomato", geography_id, 8, date(2026, 10, 1),
                date(2027, 1, 15), date(2027, 2, 15), "active"
            ),
            (
                user_id, "tomato", geography_id, 99, date(2026, 10, 1),
                date(2027, 1, 1), date(2027, 3, 31), "cancelled"
            ),
            (
                user_id, "eggplant", geography_id, 12, date(2026, 10, 1),
                date(2027, 1, 1), date(2027, 3, 31), "active"
            ),
        ],
    )


def test_post_risk_check_uses_isolated_postgresql_data(isolated_risk_service, monkeypatch):
    monkeypatch.setattr(api_module, "build_risk_service", lambda: isolated_risk_service)

    async def send_request():
        transport = httpx.ASGITransport(app=api_module.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/risk/check",
                json={
                    "crop_id": "tomato",
                    "geography_id": "mun_0304903000",
                    "proposed_area_ha": 8,
                    "harvest_start": "2027-01-15",
                    "harvest_end": "2027-03-15",
                },
            )

    response = asyncio.run(send_request())

    assert response.status_code == 200
    assert response.json()["projected_planned_area_ha"] == 40
    assert response.json()["ratio"] == 1.6
    assert response.json()["risk"] == "high"
    assert response.json()["contributing_plan_count"] == 4


def test_configured_dataset_version_is_required(isolated_risk_service):
    config = load_engine_config()
    missing_config = EngineConfig(
        assumption_version=config.assumption_version,
        dataset_version="missing-dataset-version",
        future_periods=config.future_periods,
        thresholds=config.thresholds,
    )
    service = RiskService(isolated_risk_service.repository, missing_config)

    with pytest.raises(DatasetNotReadyError):
        service.check(
            RiskCheckInput(
                crop_id="tomato",
                geography_id="mun_0304903000",
                proposed_area_ha=8,
                harvest_start=date(2027, 1, 15),
                harvest_end=date(2027, 3, 15),
            )
        )
