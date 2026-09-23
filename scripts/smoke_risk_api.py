"""Direct ASGI smoke test for the Phase 3 risk-check endpoint."""

import asyncio
from datetime import date
from decimal import Decimal

import httpx

import services.api.app as api_module
from services.engine.config import load_engine_config
from services.engine.models import CropRecord, GeographyRecord, PlanRecord, ReferenceRecord
from services.engine.service import RiskService


class SmokeRepository:
    def dataset_is_ready(self, dataset_version: str) -> bool:
        return dataset_version == "demo-2026-09-v4"

    def get_crop(self, crop_id: str):
        if crop_id != "tomato":
            return None
        return CropRecord("tomato", "Tomato")

    def get_geography(self, geography_id: str):
        if geography_id != "mun_0304903000":
            return None
        return GeographyRecord(geography_id, 1, "Cabanatuan City")

    def get_plans(self, crop_id, geography_id, geography_database_id, period_start, period_end):
        return [
            PlanRecord(
                "tomato",
                "mun_0304903000",
                Decimal("32"),
                date(2027, 1, 1),
                date(2027, 3, 31),
                "active",
            )
        ]

    def get_reference(
        self,
        crop_id,
        geography_database_id,
        period_start,
        period_end,
        dataset_version,
    ):
        return ReferenceRecord(Decimal("25"), "future_planning", "demo-2026-09-v4")


async def _request() -> httpx.Response:
    transport = httpx.ASGITransport(app=api_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://smoke") as client:
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


def main() -> int:
    original_builder = api_module.build_risk_service
    api_module.build_risk_service = lambda: RiskService(SmokeRepository(), load_engine_config())
    try:
        response = asyncio.run(_request())
    finally:
        api_module.build_risk_service = original_builder

    body = response.json()
    if response.status_code != 200:
        print(f"Risk API smoke failed: HTTP {response.status_code}: {body}")
        return 1
    if body.get("status") != "available" or body.get("ratio") != 1.6 or body.get("risk") != "high":
        print("Risk API smoke failed: the canonical Tomato result was unexpected.")
        return 1
    print("Risk API smoke passed: POST /risk/check returns the canonical 1.60 High result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
