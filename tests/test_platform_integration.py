import os
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest
from psycopg.sql import SQL, Identifier
from psycopg.types.json import Jsonb

from services.api.platform_repository import PostgresPlatformRepository
from services.engine.config import load_engine_config
from services.engine.models import RiskCheckInput
from services.engine.repository import PostgresRiskRepository
from services.engine.service import RiskService

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "data" / "migrations"


def _set_search_path(connection, schema: str) -> None:
    connection.execute(SQL("SET search_path TO {}, public").format(Identifier(schema)))


@pytest.fixture
def isolated_platform_database():
    database_url = os.getenv("TANIM_TEST_DATABASE_URL", "").strip()
    if not database_url:
        pytest.skip("TANIM_TEST_DATABASE_URL is required for PostgreSQL integration tests")

    schema = f"tanim_phase5_{uuid.uuid4().hex}"
    with psycopg.connect(database_url) as connection:
        connection.execute(SQL("CREATE SCHEMA {}").format(Identifier(schema)))
        _set_search_path(connection, schema)
        for migration in sorted(MIGRATION_DIR.glob("[0-9][0-9][0-9]_*.sql")):
            connection.execute(migration.read_text(encoding="utf-8"), prepare=False)
        users = _seed_rows(connection)

    def connection_factory(url: str, **kwargs):
        connection = psycopg.connect(url, **kwargs)
        _set_search_path(connection, schema)
        return connection

    repository = PostgresPlatformRepository(
        database_url,
        connection_factory=connection_factory,
    )
    engine = RiskService(
        PostgresRiskRepository(database_url, connection_factory=connection_factory),
        load_engine_config(),
    )
    try:
        yield repository, engine, connection_factory, users
    finally:
        with psycopg.connect(database_url) as connection:
            connection.execute(SQL("DROP SCHEMA {} CASCADE").format(Identifier(schema)))


def _seed_rows(connection):
    seeded_users = {}
    for email, role in [
        ("farmer@phase5.test", "farmer"),
        ("other@phase5.test", "farmer"),
        ("coop-one@phase5.test", "cooperative"),
        ("coop-two@phase5.test", "cooperative"),
    ]:
        user_id = connection.execute(
            """
            INSERT INTO users (email, password_hash, display_name, role, has_completed_demo)
            VALUES (%s, 'test-hash', %s, %s, TRUE)
            RETURNING id
            """,
            (email, email, role),
        ).fetchone()[0]
        seeded_users[email] = user_id
    farmer_id = seeded_users["farmer@phase5.test"]
    other_farmer_id = seeded_users["other@phase5.test"]
    first_coop_id = seeded_users["coop-one@phase5.test"]
    second_coop_id = seeded_users["coop-two@phase5.test"]

    org_ids = []
    for name, user_id in [
        ("Cooperative One", first_coop_id),
        ("Cooperative Two", second_coop_id),
    ]:
        org_id = connection.execute(
            "INSERT INTO organizations (name) VALUES (%s) RETURNING id",
            (name,),
        ).fetchone()[0]
        connection.execute(
            "INSERT INTO organization_members (organization_id, user_id) VALUES (%s, %s)",
            (org_id, user_id),
        )
        org_ids.append(org_id)

    region_id = connection.execute(
        """
        INSERT INTO geographies (name, level, code, country, island_group, geography_id)
        VALUES ('Central Luzon', 'region', '03', 'Philippines', 'Luzon', 'region_iii')
        RETURNING id
        """
    ).fetchone()[0]
    province_id = connection.execute(
        """
        INSERT INTO geographies (
            name, level, code, parent_id, country, island_group, geography_id
        ) VALUES ('Nueva Ecija', 'province', '0300', %s, 'Philippines', 'Luzon', 'province_ne')
        RETURNING id
        """,
        (region_id,),
    ).fetchone()[0]
    geography_id = connection.execute(
        """
        INSERT INTO geographies (
            name, level, code, parent_id, country, island_group, geography_id
        ) VALUES (
            'Cabanatuan City', 'municipality_city', '0304903000', %s,
            'Philippines', 'Luzon', 'mun_0304903000'
        ) RETURNING id
        """,
        (province_id,),
    ).fetchone()[0]
    connection.execute(
        """
        INSERT INTO crops (crop_id, canonical_name_en, category, active)
        VALUES ('tomato', 'Tomato', 'vegetable', TRUE)
        """
    )
    dataset_version = load_engine_config().dataset_version
    connection.execute(
        """
        INSERT INTO dataset_metadata (dataset_version, data_kind, seed, manifest_sha256, metadata)
        VALUES (%s, 'synthetic_demo', 20260924, %s, %s)
        """,
        (dataset_version, "0" * 64, Jsonb({"dataset_version": dataset_version})),
    )
    connection.execute(
        """
        INSERT INTO crop_references (
            crop_id, geography_id, period_start, period_end, period_kind,
            reference_area_ha, area_unit, data_kind, dataset_version
        ) VALUES (
            'tomato', %s, '2027-01-01', '2027-03-31', 'future_planning',
            25, 'ha', 'synthetic_demo', %s
        )
        """,
        (geography_id, dataset_version),
    )
    return {
        "farmer_id": farmer_id,
        "other_farmer_id": other_farmer_id,
        "first_coop_id": first_coop_id,
        "second_coop_id": second_coop_id,
        "geography_id": "mun_0304903000",
        "organization_ids": org_ids,
        "dataset_version": dataset_version,
    }


def _plan_values(user_id: int, role: str = "farmer", area_ha: Decimal = Decimal("8")):
    return {
        "user_id": user_id,
        "role": role,
        "crop_id": "tomato",
        "geography_id": "mun_0304903000",
        "area_ha": area_ha,
        "planting_date": date(2026, 10, 1),
        "harvest_start": date(2027, 1, 1),
        "harvest_end": date(2027, 3, 31),
    }


def test_postgres_plan_crud_ownership_cancellation_and_updated_timestamp(
    isolated_platform_database,
):
    repository, engine, connection_factory, users = isolated_platform_database
    plan = repository.create_plan(**_plan_values(users["farmer_id"]))
    assert plan.status == "active"
    assert repository.get_plan(users["farmer_id"], plan.plan_id) == plan
    assert repository.get_plan(users["other_farmer_id"], plan.plan_id) is None
    assert [item.plan_id for item in repository.list_plans(users["farmer_id"])] == [plan.plan_id]

    with connection_factory(os.getenv("TANIM_TEST_DATABASE_URL", "")) as connection:
        original_updated = connection.execute(
            "SELECT updated_at FROM planting_plans WHERE id = %s",
            (plan.plan_id,),
        ).fetchone()[0]

    updated = repository.update_plan(
        user_id=users["farmer_id"],
        plan_id=plan.plan_id,
        crop_id="tomato",
        geography_id=users["geography_id"],
        area_ha=Decimal("20"),
        planting_date=date(2026, 10, 1),
        harvest_start=date(2027, 1, 1),
        harvest_end=date(2027, 3, 31),
    )
    assert updated is not None
    assert updated.area_ha == Decimal("20.0000")
    risk = engine.check(
        RiskCheckInput(
            crop_id="tomato",
            geography_id=users["geography_id"],
            proposed_area_ha=Decimal("8"),
            harvest_start=date(2027, 1, 1),
            harvest_end=date(2027, 3, 31),
        )
    )
    assert risk.existing_planned_area_ha == Decimal("20.0000")
    assert risk.risk == "high"

    cancelled = repository.cancel_plan(users["farmer_id"], plan.plan_id)
    assert cancelled is not None
    assert cancelled.status == "cancelled"
    assert repository.cancel_plan(users["farmer_id"], plan.plan_id).status == "cancelled"
    after_cancel = engine.check(
        RiskCheckInput(
            crop_id="tomato",
            geography_id=users["geography_id"],
            proposed_area_ha=Decimal("8"),
            harvest_start=date(2027, 1, 1),
            harvest_end=date(2027, 3, 31),
        )
    )
    assert after_cancel.existing_planned_area_ha == Decimal("0")
    assert after_cancel.risk == "low"
    with connection_factory(os.getenv("TANIM_TEST_DATABASE_URL", "")) as connection:
        updated_timestamp = connection.execute(
            "SELECT updated_at FROM planting_plans WHERE id = %s",
            (plan.plan_id,),
        ).fetchone()[0]
    assert updated_timestamp >= original_updated


def test_postgres_cooperative_aggregation_uses_membership_scope(isolated_platform_database):
    repository, _engine, _connection_factory, users = isolated_platform_database
    first = repository.create_plan(
        **_plan_values(users["first_coop_id"], role="cooperative", area_ha=Decimal("5"))
    )
    repository.create_plan(
        **_plan_values(users["second_coop_id"], role="cooperative", area_ha=Decimal("25"))
    )

    first_overview = repository.cooperative_plans(users["first_coop_id"])
    second_overview = repository.cooperative_plans(users["second_coop_id"])
    assert first_overview is not None
    assert second_overview is not None
    assert first_overview[0].name == "Cooperative One"
    assert len(first_overview[1]) == 1
    assert first_overview[1][0].area_ha == Decimal("5.0000")
    assert second_overview[1][0].area_ha == Decimal("25.0000")
    assert repository.get_plan(users["second_coop_id"], first.plan_id) is None
