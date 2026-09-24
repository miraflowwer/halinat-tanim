"""PostgreSQL-backed checks for Phase 6 context queries."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg.sql import SQL, Identifier
from psycopg.types.json import Jsonb

from services.api.context import PostgresContextRepository, load_context_configuration

DATABASE_URL = os.getenv("TANIM_TEST_DATABASE_URL", "").strip()
ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "data" / "migrations"


def _set_search_path(connection, schema: str) -> None:
    connection.execute(SQL("SET search_path TO {}, public").format(Identifier(schema)))


@pytest.fixture()
def context_repository():
    if not DATABASE_URL:
        pytest.skip("TANIM_TEST_DATABASE_URL is required for PostgreSQL integration tests")
    configuration = load_context_configuration()
    schema = f"tanim_phase6_context_{uuid.uuid4().hex}"
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(SQL("CREATE SCHEMA {}").format(Identifier(schema)))
        _set_search_path(connection, schema)
        for migration in sorted(MIGRATION_DIR.glob("[0-9][0-9][0-9]_*.sql")):
            connection.execute(migration.read_text(encoding="utf-8"), prepare=False)

    def connection_factory(url: str, **kwargs):
        connection = psycopg.connect(url, **kwargs)
        _set_search_path(connection, schema)
        return connection

    with connection_factory(DATABASE_URL) as connection:
        region_id = connection.execute(
            """
            INSERT INTO geographies (
                name, level, code, parent_id, country, island_group, active, geography_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                "Region I (Ilocos Region)",
                "region",
                "0100000000",
                None,
                "Philippines",
                "Luzon",
                True,
                "region_0100000000",
            ),
        ).fetchone()[0]
        province_id = connection.execute(
            """
            INSERT INTO geographies (
                name, level, code, parent_id, country, island_group, active, geography_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                "Ilocos Norte",
                "province",
                "0102800000",
                region_id,
                "Philippines",
                "Luzon",
                True,
                "province_0102800000",
            ),
        ).fetchone()[0]
        connection.execute(
            """
            INSERT INTO crops (
                crop_id, canonical_name_en, canonical_name_tl, scientific_name,
                category, aliases_en, aliases_tl, active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                "arrowroot",
                "Arrowroot",
                "Araro",
                "Maranta arundinacea",
                "root_crop",
                ["araro"],
                [],
                True,
            ),
        )
        connection.execute(
            """
            INSERT INTO dataset_metadata (
                dataset_version, data_kind, seed, manifest_sha256, metadata, content_fingerprints
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                configuration.dataset_version,
                "synthetic_demo",
                20260924,
                "test-fixture",
                Jsonb({"provenance": {"price_history": {}}}),
                Jsonb({}),
            ),
        )
        connection.execute(
            """
            INSERT INTO price_history (
                crop_id, geography_id, price_date, price_php_per_kg, currency, price_unit,
                data_kind, dataset_version, reference_sources
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                "arrowroot",
                province_id,
                "2026-08-01",
                "25.5000",
                "PHP",
                "PHP/kg",
                "synthetic_demo",
                configuration.dataset_version,
                None,
            ),
        )

    try:
        yield PostgresContextRepository(
            DATABASE_URL, configuration, connection_factory=connection_factory
        )
    finally:
        with psycopg.connect(DATABASE_URL) as connection:
            connection.execute(SQL("DROP SCHEMA {} CASCADE").format(Identifier(schema)))


def test_price_geography_filter_accepts_a_crop_id(context_repository):
    result = context_repository.list_geographies(
        level=None,
        search=None,
        for_prices=True,
        crop_id="arrowroot",
        limit=1000,
    )

    assert result["dataset_version"] == "demo-2026-09-v4"
    assert result["items"]


def test_price_geography_filter_accepts_all_crops(context_repository):
    result = context_repository.list_geographies(
        level=None,
        search=None,
        for_prices=True,
        crop_id=None,
        limit=1000,
    )

    assert result["dataset_version"] == "demo-2026-09-v4"
    assert result["items"]
