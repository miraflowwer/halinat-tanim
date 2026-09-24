"""Smoke-test the Phase 6 read APIs against the running local TANIM API."""

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

BASE_URL = os.getenv("TANIM_API_URL", "http://127.0.0.1:8000").rstrip("/")


def get_json(path: str) -> tuple[int, dict[str, object]]:
    try:
        with urlopen(f"{BASE_URL}{path}", timeout=5) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    try:
        status, crop_page = get_json("/crops?limit=1")
        require(status == 200, f"GET /crops returned HTTP {status}.")
        crops = crop_page.get("items")
        require(isinstance(crops, list) and bool(crops), "GET /crops returned no active crop.")
        crop = crops[0]
        require(isinstance(crop, dict), "GET /crops returned an invalid crop record.")
        crop_id = str(crop.get("crop_id", ""))
        dataset_version = str(crop_page.get("dataset_version", ""))

        status, detail = get_json(f"/crops/{crop_id}")
        require(status == 200, f"GET /crops/{{crop_id}} returned HTTP {status}.")
        require(
            detail.get("dataset_version") == dataset_version,
            "Crop detail changed dataset version.",
        )
        require(bool(detail.get("canonical_name_tl")), "Crop detail has no Tagalog name.")

        query = urlencode({"for_prices": "true", "crop_id": crop_id, "limit": 1000})
        status, locations = get_json(f"/geographies?{query}")
        require(status == 200, f"GET /geographies for prices returned HTTP {status}.")
        price_locations = locations.get("items")
        require(
            isinstance(price_locations, list) and bool(price_locations),
            "No price locations were returned.",
        )
        price_location = price_locations[0]
        require(isinstance(price_location, dict), "Price location record is invalid.")
        price_query = urlencode(
            {
                "crop_id": crop_id,
                "geography_id": price_location.get("geography_id", ""),
                "range": "3m",
            }
        )
        status, prices = get_json(f"/prices?{price_query}")
        require(status == 200, f"GET /prices returned HTTP {status}.")
        require(prices.get("unit") == "PHP/kg", "Prices did not report PHP/kg.")
        require(prices.get("dataset_version") == dataset_version, "Prices changed dataset version.")

        map_query = urlencode({"crop_id": crop_id, "period": "current"})
        status, map_body = get_json(f"/supply-map?{map_query}")
        require(status == 200, f"GET /supply-map returned HTTP {status}.")
        require(
            map_body.get("dataset_version") == dataset_version,
            "Supply map changed dataset version.",
        )
        require(map_body.get("geography_level") == "region", "Supply map is not region-compatible.")
        require("not registered farmer planting plans" in str(map_body.get("source_note", "")),
                "Supply map did not identify snapshots as context.")

        status, geometry = get_json("/map-geometry")
        require(status == 200, f"GET /map-geometry returned HTTP {status}.")
        features = geometry.get("features")
        require(
            isinstance(features, list) and len(features) == 8,
            "Local map has the wrong Luzon region count.",
        )

        status, geographies = get_json("/geographies?level=municipality_city&limit=1")
        require(status == 200, f"GET /geographies returned HTTP {status}.")
        places = geographies.get("items")
        require(isinstance(places, list) and bool(places), "No municipality or city was returned.")
        place = places[0]
        require(isinstance(place, dict), "Municipality or city record is invalid.")
        suitability_query = urlencode(
            {"crop_id": crop_id, "geography_id": place.get("geography_id", "")}
        )
        suitability_status, suitability = get_json(f"/suitability?{suitability_query}")
        require(suitability_status == 200, f"GET /suitability returned HTTP {suitability_status}.")
        require("suitability_class" in suitability, "Suitability has no class.")
        require(
            suitability.get("dataset_version") == dataset_version,
            "Suitability changed dataset version.",
        )

        consent_status, consent_body = get_json("/weather/status")
        consent_detail = consent_body.get("detail", {})
        require(consent_status == 428, "Weather status did not require user consent.")
        require(
            isinstance(consent_detail, dict)
            and consent_detail.get("code") == "WEATHER_CONSENT_REQUIRED",
            "Weather status returned an unexpected consent response.",
        )
    except (OSError, URLError, RuntimeError, ValueError) as error:
        print(f"Context API smoke failed: {error}")
        return 1

    print(
        "Context API smoke passed: crops, prices, suitability, supply map, local geometry, "
        "and weather consent are available."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
