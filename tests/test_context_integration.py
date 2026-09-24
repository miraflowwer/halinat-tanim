"""PostgreSQL-backed checks for Phase 6 context queries."""

from __future__ import annotations

import os

import pytest

from services.api.context import PostgresContextRepository, load_context_configuration

DATABASE_URL = os.getenv("TANIM_TEST_DATABASE_URL", "").strip()


@pytest.fixture()
def context_repository():
    if not DATABASE_URL:
        pytest.skip("TANIM_TEST_DATABASE_URL is required for PostgreSQL integration tests")
    configuration = load_context_configuration()
    return PostgresContextRepository(DATABASE_URL, configuration)


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
