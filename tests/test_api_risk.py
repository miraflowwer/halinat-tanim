import asyncio
from datetime import date
from decimal import Decimal

import httpx
import pytest

import services.api.app as api_module
from services.engine.config import load_engine_config
from services.engine.models import CropRecord, GeographyRecord, PlanRecord, ReferenceRecord
from services.engine.service import RiskService


class InMemoryRiskRepository:
    def __init__(self, plans=None, references=None):
        self.plans = plans or []
        self.references = references or {}
        self.crops = {"tomato": "Tomato", "eggplant": "Eggplant"}
        self.geography = GeographyRecord("mun_0304903000", 1, "Cabanatuan City")

    def dataset_is_ready(self, dataset_version):
        return dataset_version == "demo-2026-09-v4"

    def get_crop(self, crop_id):
        name = self.crops.get(crop_id)
        return CropRecord(crop_id, name) if name else None

    def get_geography(self, geography_id):
        return self.geography if geography_id == self.geography.geography_id else None

    def get_plans(self, crop_id, geography_id, geography_database_id, period_start, period_end):
        return [plan for plan in self.plans if plan.crop_id == crop_id]

    def get_reference(
        self,
        crop_id,
        geography_database_id,
        period_start,
        period_end,
        dataset_version,
    ):
        return self.references.get((crop_id, period_start, period_end))


def request(method: str, path: str, **kwargs) -> httpx.Response:
    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=api_module.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send_request())


@pytest.fixture
def install_in_memory_service(monkeypatch):
    plans = [
        PlanRecord(
            "tomato",
            "mun_0304903000",
            Decimal("8"),
            date(2027, 1, 1),
            date(2027, 1, 31),
            "active",
        ),
        PlanRecord(
            "tomato",
            "mun_0304903000",
            Decimal("8"),
            date(2027, 2, 1),
            date(2027, 2, 28),
            "active",
        ),
        PlanRecord(
            "tomato",
            "mun_0304903000",
            Decimal("8"),
            date(2027, 3, 1),
            date(2027, 3, 31),
            "active",
        ),
        PlanRecord(
            "tomato",
            "mun_0304903000",
            Decimal("8"),
            date(2027, 1, 15),
            date(2027, 2, 15),
            "active",
        ),
        PlanRecord(
            "eggplant",
            "mun_0304903000",
            Decimal("12"),
            date(2027, 1, 1),
            date(2027, 3, 31),
            "active",
        ),
    ]
    references = {
        ("tomato", date(2027, 1, 1), date(2027, 3, 31)): ReferenceRecord(
            Decimal("25"), "future_planning", "demo-2026-09-v4"
        ),
        ("eggplant", date(2027, 1, 1), date(2027, 3, 31)): ReferenceRecord(
            Decimal("18"), "future_planning", "demo-2026-09-v4"
        ),
    }
    repository = InMemoryRiskRepository(plans, references)
    monkeypatch.setattr(
        api_module,
        "build_risk_service",
        lambda: RiskService(repository, load_engine_config()),
    )


def test_risk_check_returns_canonical_tomato_result(install_in_memory_service):
    response = request(
        "POST",
        "/risk/check",
        json={
            "crop_id": "tomato",
            "geography_id": "mun_0304903000",
            "proposed_area_ha": 8,
            "harvest_start": "2027-01-15",
            "harvest_end": "2027-03-15",
            "comparison_crop_ids": ["eggplant"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert body["planning_period_start"] == "2027-01-01"
    assert body["planning_period_end"] == "2027-03-31"
    assert body["existing_planned_area_ha"] == 32
    assert body["projected_planned_area_ha"] == 40
    assert body["reference_area_ha"] == 25
    assert body["ratio"] == 1.6
    assert body["risk"] == "high"
    assert body["contributing_plan_count"] == 4
    assert body["assumption_version"] == "grci-v1"
    assert body["dataset_version"] == "demo-2026-09-v4"
    assert body["comparisons"][0]["crop_id"] == "eggplant"
    assert body["comparisons"][0]["current_risk"] == "low"
    assert body["comparisons"][0]["projected_risk_if_same_area"] == "high"


def test_risk_check_returns_unavailable_when_reference_is_missing(
    install_in_memory_service, monkeypatch
):
    repository = InMemoryRiskRepository(
        plans=[],
        references={
            ("eggplant", date(2027, 1, 1), date(2027, 3, 31)): ReferenceRecord(
                Decimal("18"), "future_planning", "demo-2026-09-v4"
            )
        },
    )
    monkeypatch.setattr(
        api_module,
        "build_risk_service",
        lambda: RiskService(repository, load_engine_config()),
    )

    response = request(
        "POST",
        "/risk/check",
        json={
            "crop_id": "tomato",
            "geography_id": "mun_0304903000",
            "proposed_area_ha": 8,
            "harvest_start": "2027-01-15",
            "harvest_end": "2027-03-15",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["reference_area_ha"] is None
    assert body["ratio"] is None
    assert body["risk"] is None
    assert "cannot calculate" in body["explanation"]


def test_comparison_with_missing_reference_stays_informationally_unavailable(
    install_in_memory_service,
    monkeypatch,
):
    repository = InMemoryRiskRepository(
        plans=[],
        references={
            ("tomato", date(2027, 1, 1), date(2027, 3, 31)): ReferenceRecord(
                Decimal("25"), "future_planning", "demo-2026-09-v4"
            )
        },
    )
    monkeypatch.setattr(
        api_module,
        "build_risk_service",
        lambda: RiskService(repository, load_engine_config()),
    )

    response = request(
        "POST",
        "/risk/check",
        json={
            "crop_id": "tomato",
            "geography_id": "mun_0304903000",
            "proposed_area_ha": 8,
            "harvest_start": "2027-01-15",
            "harvest_end": "2027-03-15",
            "comparison_crop_ids": ["eggplant"],
        },
    )

    comparison = response.json()["comparisons"][0]
    assert response.status_code == 200
    assert comparison["crop_id"] == "eggplant"
    assert comparison["reference_area_ha"] is None
    assert comparison["current_ratio"] is None
    assert comparison["projected_ratio_if_same_area"] is None


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        (
            {
                "crop_id": "tomato",
                "geography_id": "mun_0304903000",
                "proposed_area_ha": 0,
                "harvest_start": "2027-01-15",
                "harvest_end": "2027-03-15",
            },
            "INVALID_AREA",
        ),
        (
            {
                "crop_id": "tomato",
                "geography_id": "mun_0304903000",
                "proposed_area_ha": 8,
                "harvest_start": "2027-03-20",
                "harvest_end": "2027-04-10",
            },
            "HARVEST_PERIOD_SPANS_MULTIPLE_PERIODS",
        ),
        (
            {
                "crop_id": "tomato",
                "geography_id": "mun_0304903000",
                "proposed_area_ha": 8,
                "harvest_start": "2027-01-15",
                "harvest_end": "2027-03-15",
                "comparison_crop_ids": ["eggplant", "eggplant"],
            },
            "DUPLICATE_COMPARISON_CROP_IDS",
        ),
        (
            {
                "crop_id": "tomato",
                "geography_id": "mun_0304903000",
                "proposed_area_ha": 8,
                "harvest_start": "2027-01-15",
                "harvest_end": "2027-03-15",
                "comparison_crop_ids": ["tomato"],
            },
            "PRIMARY_CROP_IN_COMPARISONS",
        ),
    ],
)
def test_risk_check_returns_machine_readable_validation_errors(
    install_in_memory_service,
    payload,
    code,
):
    response = request("POST", "/risk/check", json=payload)

    assert response.status_code in {400, 422}
    assert response.json()["detail"]["code"] == code


@pytest.mark.parametrize(
    ("field", "value"),
    [("crop_id", "unsupported"), ("geography_id", "mun-unsupported")],
)
def test_risk_check_rejects_unsupported_crop_and_geography(
    install_in_memory_service,
    field,
    value,
):
    payload = {
        "crop_id": "tomato",
        "geography_id": "mun_0304903000",
        "proposed_area_ha": 8,
        "harvest_start": "2027-01-15",
        "harvest_end": "2027-03-15",
    }
    payload[field] = value

    response = request("POST", "/risk/check", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"]["code"] in {
        "UNSUPPORTED_CROP",
        "UNSUPPORTED_GEOGRAPHY",
    }
