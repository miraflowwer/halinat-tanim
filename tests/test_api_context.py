import asyncio
from datetime import date
from decimal import Decimal

import httpx
import pytest

import services.api.app as api_module
import services.api.context as context_module
from services.api.context import ContextServiceError
from services.api.weather_provider import WeatherProviderError


class InMemoryContextRepository:
    def __init__(self):
        self.price_calls = []
        self.suitability_class = "suitable"

    def list_crops(self, search, category, limit, offset):
        items = [
            {
                "crop_id": "tomato",
                "canonical_name_en": "Tomato",
                "canonical_name_tl": "Kamatis",
                "scientific_name": "Solanum lycopersicum",
                "category": "vegetable",
                "aliases_en": [],
                "aliases_tl": [],
                "data_kind": "synthetic_demo",
                "dataset_version": "demo-2026-09-v4",
            },
            {
                "crop_id": "eggplant",
                "canonical_name_en": "Eggplant",
                "canonical_name_tl": "Talong",
                "scientific_name": "Solanum melongena",
                "category": "vegetable",
                "aliases_en": [],
                "aliases_tl": [],
                "data_kind": "synthetic_demo",
                "dataset_version": "demo-2026-09-v4",
            },
        ]
        if search:
            items = [
                item
                for item in items
                if search.casefold() in item["canonical_name_en"].casefold()
            ]
        if category:
            items = [item for item in items if item["category"] == category]
        return {
            "items": items[offset : offset + limit],
            "total": len(items),
            "categories": ["vegetable"],
            "dataset_version": "demo-2026-09-v4",
        }

    def get_crop(self, crop_id):
        if crop_id != "tomato":
            return None
        return {
            "crop_id": "tomato",
            "canonical_name_en": "Tomato",
            "canonical_name_tl": "Kamatis",
            "scientific_name": "Solanum lycopersicum",
            "category": "vegetable",
            "aliases_en": [],
            "aliases_tl": [],
            "summary_en": "Tomatoes are edible fruits used as vegetables.",
            "summary_tl": "Ang kamatis ay prutas na ginagamit na gulay.",
            "growing_conditions_en": "Warm and sunny places support tomato growth.",
            "growing_conditions_tl": "Nakatutulong sa kamatis ang mainit at maaraw na lugar.",
            "soil_notes_en": "Use soil that drains well.",
            "soil_notes_tl": "Gumamit ng lupang may maayos na paagusan.",
            "reference_sources": "TANIM-SYNTH-CROP-PROFILE-V1",
            "source_ids": ["TANIM-SYNTH-CROP-PROFILE-V1"],
            "method_note": "General crop context.",
            "data_kind": "synthetic_demo",
            "dataset_version": "demo-2026-09-v4",
            "dataset_provenance": {},
            "links": {
                "prices": "/prices?crop_id=tomato",
                "supply": "/supply-map?crop_id=tomato",
                "suitability": "/suitability?crop_id=tomato",
            },
        }

    def list_geographies(self, level, search, for_prices, crop_id, limit):
        items = [
            {
                "geography_id": "province_0304900000",
                "name": "Nueva Ecija",
                "level": "province",
                "code": "0304900000",
                "parent_geography_id": "region_0300000000",
                "parent_name": "Central Luzon",
            }
        ]
        return {"items": items[:limit], "dataset_version": "demo-2026-09-v4"}

    def get_prices(self, crop_id, geography_id, time_range, start_date, end_date, limit):
        self.price_calls.append((crop_id, geography_id, time_range, start_date, end_date, limit))
        records = []
        if crop_id == "tomato" and geography_id == "province_0304900000":
            records = [
                {
                    "date": date(2026, 8, 1),
                    "price_php_per_kg": Decimal("42.50"),
                    "currency": "PHP",
                    "price_unit": "PHP/kg",
                    "data_kind": "synthetic_demo",
                    "dataset_version": "demo-2026-09-v4",
                    "reference_sources": "PSA-OPENSTAT-2M4AFN08|DA-PRICE-MONITORING",
                    "geography_id": geography_id,
                    "geography_name": "Nueva Ecija",
                }
            ]
        return {
            "crop_id": crop_id,
            "geography_id": geography_id,
            "range": time_range,
            "start_date": start_date,
            "end_date": end_date,
            "currency": "PHP",
            "unit": "PHP/kg",
            "dataset_version": "demo-2026-09-v4",
            "data_kind": "synthetic_demo",
            "provenance": {"meaning": "Generated values are not PSA or DA observations."},
            "records": records[:limit],
        }

    def get_suitability(self, crop_id, geography_id):
        if crop_id != "tomato" or geography_id not in {"mun_0304903000", "mun_empty"}:
            raise ContextServiceError(
                "UNSUPPORTED_GEOGRAPHY", "This location is not supported.", 404
            )
        if geography_id == "mun_empty":
            return {
                "crop_id": crop_id,
                "geography_id": geography_id,
                "geography_name": "No Data Town",
                "suitability_class": "no_data",
                "dataset_version": "demo-2026-09-v4",
                "data_kind": None,
                "source_ids": [],
                "method_note": None,
            }
        return {
            "crop_id": crop_id,
            "geography_id": geography_id,
            "geography_name": "Cabanatuan City",
            "suitability_class": self.suitability_class,
            "dataset_version": "demo-2026-09-v4",
            "data_kind": "synthetic_demo",
            "source_ids": ["TANIM-SYNTH-SOIL-BASELINE-V1"],
            "reference_sources": "TANIM-SYNTH-SOIL-BASELINE-V1",
            "method_note": "Synthetic soil context only.",
        }

    def get_supply_map(self, crop_id, period):
        if crop_id != "tomato":
            return None
        return {
            "crop_id": crop_id,
            "period": {
                "period_start": period.period_start,
                "period_end": period.period_end,
                "period_kind": period.period_kind,
            },
            "available_periods": [
                {
                    "period_start": date(2026, 9, 1),
                    "period_end": date(2026, 9, 30),
                    "period_kind": "current_supply",
                }
            ],
            "geography_level": "region",
            "data_kind": "derived",
            "source_data_kind": "synthetic_demo",
            "dataset_version": "demo-2026-09-v4",
            "source_note": "These values are not registered farmer planting plans.",
            "items": [
                {
                    "geography_id": "region_0300000000",
                    "name": "Central Luzon",
                    "geography_level": "region",
                    "period_start": period.period_start,
                    "period_end": period.period_end,
                    "period_kind": period.period_kind,
                    "planned_context_area_ha": Decimal("180.00"),
                    "reference_context_area_ha": Decimal("200.00"),
                    "ratio": Decimal("0.900000"),
                    "level": "moderate",
                    "data_status": "available",
                    "data_kind": "derived",
                    "source_data_kind": "synthetic_demo",
                    "dataset_version": "demo-2026-09-v4",
                    "source_note": "These values are not registered farmer planting plans.",
                },
                {
                    "geography_id": "region_0500000000",
                    "name": "Bicol Region",
                    "geography_level": "region",
                    "period_start": period.period_start,
                    "period_end": period.period_end,
                    "period_kind": period.period_kind,
                    "planned_context_area_ha": None,
                    "reference_context_area_ha": None,
                    "ratio": None,
                    "level": "no_data",
                    "data_status": "no_data",
                    "data_kind": None,
                    "source_data_kind": None,
                    "dataset_version": "demo-2026-09-v4",
                    "source_note": "No snapshot is available.",
                },
            ],
        }


class FakeWeatherProvider:
    name = "Test Weather"

    def __init__(self):
        self.status_error = None
        self.forecast_error = None
        self.status_calls = 0
        self.forecast_calls = []

    def check_reachable(self):
        self.status_calls += 1
        if self.status_error:
            raise self.status_error

    def get_forecast(self, latitude, longitude):
        self.forecast_calls.append((latitude, longitude))
        if self.forecast_error:
            raise self.forecast_error
        return {
            "observed_at": "2026-09-24T10:00",
            "retrieved_at": "2026-09-24T02:00:00+00:00",
            "current": {
                "temperature_c": 29,
                "precipitation_mm": 0,
                "rain_mm": 0,
                "weather_code": 2,
                "condition": "Partly cloudy",
            },
            "forecast": [],
            "attribution": "Test provider attribution.",
        }


def request(method: str, path: str, **kwargs) -> httpx.Response:
    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=api_module.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send_request())


@pytest.fixture
def install_context_services():
    repository = InMemoryContextRepository()
    provider = FakeWeatherProvider()
    api_module.app.dependency_overrides[context_module.get_context_repository] = lambda: repository
    api_module.app.dependency_overrides[context_module.get_weather_provider] = lambda: provider
    yield repository, provider
    api_module.app.dependency_overrides.clear()


def test_crop_list_search_category_and_names(install_context_services):
    response = request("GET", "/crops?q=tomato&category=vegetable")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["canonical_name_en"] == "Tomato"
    assert body["items"][0]["canonical_name_tl"] == "Kamatis"
    assert body["dataset_version"] == "demo-2026-09-v4"


def test_crop_detail_exposes_profile_context_and_links(install_context_services):
    response = request("GET", "/crops/tomato")

    assert response.status_code == 200
    body = response.json()
    assert body["scientific_name"] == "Solanum lycopersicum"
    assert body["summary_tl"]
    assert body["links"]["prices"] == "/prices?crop_id=tomato"
    assert body["source_ids"] == ["TANIM-SYNTH-CROP-PROFILE-V1"]


def test_crop_detail_rejects_unsupported_crop(install_context_services):
    response = request("GET", "/crops/unsupported")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "UNSUPPORTED_CROP"


def test_prices_filter_location_period_unit_and_synthetic_provenance(install_context_services):
    repository, _ = install_context_services
    response = request(
        "GET",
        "/prices?crop_id=tomato&geography_id=province_0304900000&range=3m&start_date=2026-06-01",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["unit"] == "PHP/kg"
    assert body["records"][0]["price_php_per_kg"] == 42.5
    assert body["records"][0]["geography_id"] == "province_0304900000"
    assert body["records"][0]["data_kind"] == "synthetic_demo"
    assert repository.price_calls[0][2:5] == ("3m", date(2026, 6, 1), None)


def test_prices_allow_empty_results_with_provenance(install_context_services):
    response = request("GET", "/prices?crop_id=eggplant&range=all")

    assert response.status_code == 200
    assert response.json()["records"] == []
    assert response.json()["data_kind"] == "synthetic_demo"


@pytest.mark.parametrize(
    ("geography_id", "expected_class"),
    [("mun_0304903000", "suitable"), ("mun_empty", "no_data")],
)
def test_suitability_returns_class_and_is_not_supply_pressure(
    install_context_services, geography_id, expected_class
):
    response = request("GET", f"/suitability?crop_id=tomato&geography_id={geography_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["suitability_class"] == expected_class
    assert body["dataset_version"] == "demo-2026-09-v4"
    assert "risk" not in body
    assert "ratio" not in body


def test_supply_map_filters_period_and_marks_snapshot_context(install_context_services):
    response = request("GET", "/supply-map?crop_id=tomato&period=2026-09-01")

    assert response.status_code == 200
    body = response.json()
    assert body["period"]["period_start"] == "2026-09-01"
    assert body["items"][0]["geography_id"] == "region_0300000000"
    assert body["items"][1]["level"] == "no_data"
    assert "not registered farmer planting plans" in body["source_note"]
    assert "planting_plan_count" not in body
    assert body["dataset_version"] == "demo-2026-09-v4"


def test_supply_map_rejects_unsupported_period(install_context_services):
    response = request("GET", "/supply-map?crop_id=tomato&period=2035-01-01")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNSUPPORTED_PERIOD"


def test_local_map_geometry_has_luzon_regions(install_context_services):
    response = request("GET", "/map-geometry")

    assert response.status_code == 200
    body = response.json()
    assert len(body["features"]) == 8
    assert {feature["properties"]["geography_id"] for feature in body["features"]} >= {
        "region_0100000000",
        "region_1300000000",
    }


def test_weather_requires_consent_before_provider_requests(install_context_services):
    _, provider = install_context_services

    status = request("GET", "/weather/status")
    weather = request("GET", "/weather?geography_id=region_0100000000")

    assert status.status_code == 428
    assert weather.status_code == 428
    assert provider.status_calls == 0
    assert provider.forecast_calls == []


def test_weather_status_and_forecast_success(install_context_services):
    _, provider = install_context_services

    status = request("GET", "/weather/status?consent=true")
    weather = request("GET", "/weather?geography_id=region_0100000000&consent=true")

    assert status.status_code == 200
    assert status.json()["status"] == "available"
    assert weather.status_code == 200
    assert weather.json()["data_kind"] == "live_external"
    assert weather.json()["location"] == "Region I (Ilocos Region)"
    assert weather.json()["current"]["temperature_c"] == 29
    assert provider.status_calls == 1
    assert len(provider.forecast_calls) == 1


@pytest.mark.parametrize(
    ("code", "status_code"),
    [("WEATHER_UNAVAILABLE", 503), ("WEATHER_TIMEOUT", 504)],
)
def test_weather_provider_failure_is_retryable_and_clear(
    install_context_services, code, status_code
):
    _, provider = install_context_services
    provider.status_error = WeatherProviderError(code, status_code)

    response = request("GET", "/weather/status?consent=true")

    assert response.status_code == status_code
    assert response.json()["detail"]["code"] == code
    assert response.json()["detail"]["message"] == context_module.WEATHER_FAILURE_MESSAGE


def test_weather_does_not_affect_local_health(install_context_services):
    _, provider = install_context_services
    provider.status_error = WeatherProviderError("WEATHER_UNAVAILABLE")

    response = request("GET", "/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    assert provider.status_calls == 0
