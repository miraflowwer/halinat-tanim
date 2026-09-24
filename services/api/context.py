"""Read-only crop, price, suitability, and supply context APIs."""

from __future__ import annotations

import json
import logging
import math
import os
from calendar import monthrange
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Protocol

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from psycopg.rows import dict_row
from pydantic import BaseModel, field_serializer

from services.api.weather_provider import (
    OpenMeteoProvider,
    WeatherProvider,
    WeatherProviderError,
)

logger = logging.getLogger(__name__)
router = APIRouter()
ROOT = Path(__file__).resolve().parents[2]
DATASET_CONFIG_PATH = ROOT / "data" / "dataset_config.json"
MAP_GEOMETRY_PATH = ROOT / "data" / "geometry" / "luzon-regions.geojson"
WEATHER_FAILURE_MESSAGE = (
    "TANIM cannot connect to the weather service. Check your internet connection and try again."
)


class ContextServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class MapPeriod:
    period_start: date
    period_end: date
    period_kind: Literal["current_supply", "future_planning"]


@dataclass(frozen=True)
class ContextConfiguration:
    dataset_version: str
    periods: tuple[MapPeriod, ...]
    low_below: Decimal
    high_above: Decimal


def load_context_configuration(path: Path = DATASET_CONFIG_PATH) -> ContextConfiguration:
    try:
        with path.open(encoding="utf-8") as file:
            data: dict[str, Any] = json.load(file)
        version = str(data["dataset_version"]).strip()
        current = data["periods"]["current_supply"]
        future = data["periods"]["future_planning"]
        low_below = Decimal(str(data["snapshot_thresholds"]["low_below"]))
        high_above = Decimal(str(data["snapshot_thresholds"]["high_above"]))
        periods = [
            MapPeriod(
                date.fromisoformat(current["start"]),
                date.fromisoformat(current["end"]),
                "current_supply",
            )
        ]
        for start_text in future["quarter_starts"]:
            start = date.fromisoformat(start_text)
            end_month = start.month + 2
            end = date(start.year, end_month, monthrange(start.year, end_month)[1])
            periods.append(MapPeriod(start, end, "future_planning"))
    except (KeyError, OSError, TypeError, ValueError) as error:
        raise ContextServiceError(
            "DATASET_NOT_READY", "The configured TANIM dataset is not ready."
        ) from error

    if not version or low_below < 0 or high_above <= low_below:
        raise ContextServiceError(
            "DATASET_NOT_READY", "The configured TANIM dataset is not ready."
        )
    return ContextConfiguration(version, tuple(periods), low_below, high_above)


class ContextRepository(Protocol):
    def list_crops(
        self, search: str | None, category: str | None, limit: int, offset: int
    ) -> dict[str, Any]: ...

    def get_crop(self, crop_id: str) -> dict[str, Any] | None: ...

    def list_geographies(
        self,
        level: str | None,
        search: str | None,
        for_prices: bool,
        crop_id: str | None,
        limit: int,
    ) -> dict[str, Any]: ...

    def get_prices(
        self,
        crop_id: str,
        geography_id: str | None,
        time_range: str,
        start_date: date | None,
        end_date: date | None,
        limit: int,
    ) -> dict[str, Any]: ...

    def get_suitability(self, crop_id: str, geography_id: str) -> dict[str, Any] | None: ...

    def get_supply_map(
        self, crop_id: str, period: MapPeriod
    ) -> dict[str, Any] | None: ...


class PostgresContextRepository:
    def __init__(
        self,
        database_url: str,
        configuration: ContextConfiguration,
        *,
        connection_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.database_url = database_url
        self.configuration = configuration
        self.connection_factory = connection_factory or psycopg.connect

    @classmethod
    def from_environment(cls) -> PostgresContextRepository:
        database_url = os.getenv("DATABASE_URL", "").strip()
        if not database_url:
            raise ContextServiceError(
                "DATABASE_UNAVAILABLE",
                "TANIM cannot read the local data service right now. Check PostgreSQL and retry.",
            )
        return cls(database_url, load_context_configuration())

    def _run(self, operation):
        try:
            with self.connection_factory(
                self.database_url, connect_timeout=3, row_factory=dict_row
            ) as connection:
                self._require_active_dataset(connection)
                return operation(connection)
        except ContextServiceError:
            raise
        except (psycopg.Error, ValueError) as error:
            logger.warning("Context data query failed (%s).", type(error).__name__)
            raise ContextServiceError(
                "DATABASE_UNAVAILABLE",
                "TANIM cannot read the local data service right now. Check PostgreSQL and retry.",
            ) from None

    def _require_active_dataset(self, connection) -> dict[str, Any]:
        row = connection.execute(
            """
            SELECT dataset_version, data_kind, metadata
            FROM dataset_metadata
            WHERE dataset_version = %s
            """,
            (self.configuration.dataset_version,),
        ).fetchone()
        if row is None:
            raise ContextServiceError(
                "DATASET_NOT_READY",
                "The configured TANIM dataset is not seeded. Run the data seed step and retry.",
            )
        return row

    @staticmethod
    def _split_sources(value: str | None) -> list[str]:
        if not value:
            return []
        return [source.strip() for source in value.split("|") if source.strip()]

    def _require_crop(self, connection, crop_id: str) -> None:
        row = connection.execute(
            "SELECT 1 FROM crops WHERE crop_id = %s AND active = TRUE", (crop_id,)
        ).fetchone()
        if row is None:
            raise ContextServiceError("UNSUPPORTED_CROP", "This crop is not supported.", 404)

    def _require_geography(self, connection, geography_id: str) -> None:
        row = connection.execute(
            """
            SELECT 1 FROM geographies
            WHERE geography_id = %s AND active = TRUE
              AND country = 'Philippines' AND island_group = 'Luzon'
            """,
            (geography_id,),
        ).fetchone()
        if row is None:
            raise ContextServiceError(
                "UNSUPPORTED_GEOGRAPHY", "This Luzon location is not supported.", 404
            )

    def list_crops(
        self, search: str | None, category: str | None, limit: int, offset: int
    ) -> dict[str, Any]:
        cleaned_search = search.strip().casefold() if search else None

        def operation(connection):
            filters = ["c.active = TRUE", "p.dataset_version = %s"]
            parameters: list[object] = [self.configuration.dataset_version]
            if category:
                filters.append("c.category = %s")
                parameters.append(category.strip())
            if cleaned_search:
                filters.append(
                    "position(%s in lower(concat_ws(' ', c.canonical_name_en, "
                    "c.canonical_name_tl, c.scientific_name, "
                    "array_to_string(c.aliases_en || c.aliases_tl, ' ')))) > 0"
                )
                parameters.append(cleaned_search)
            where_clause = " AND ".join(filters)
            total = connection.execute(
                f"""
                SELECT count(*) AS total
                FROM crops c
                JOIN crop_profiles p ON p.crop_id = c.crop_id
                WHERE {where_clause}
                """,
                parameters,
            ).fetchone()["total"]
            rows = connection.execute(
                f"""
                SELECT c.crop_id, c.canonical_name_en, c.canonical_name_tl,
                       c.scientific_name, c.category, c.aliases_en, c.aliases_tl,
                       p.data_kind, p.dataset_version
                FROM crops c
                JOIN crop_profiles p ON p.crop_id = c.crop_id
                WHERE {where_clause}
                ORDER BY c.canonical_name_en, c.crop_id
                LIMIT %s OFFSET %s
                """,
                (*parameters, limit, offset),
            ).fetchall()
            categories = connection.execute(
                "SELECT DISTINCT category FROM crops WHERE active = TRUE ORDER BY category"
            ).fetchall()
            return {
                "items": [dict(row) for row in rows],
                "total": total,
                "categories": [row["category"] for row in categories],
                "dataset_version": self.configuration.dataset_version,
            }

        return self._run(operation)

    def get_crop(self, crop_id: str) -> dict[str, Any] | None:
        def operation(connection):
            self._require_crop(connection, crop_id)
            row = connection.execute(
                """
                SELECT c.crop_id, c.canonical_name_en, c.canonical_name_tl,
                       c.scientific_name, c.category, c.aliases_en, c.aliases_tl,
                       p.summary_en, p.summary_tl,
                       p.growing_conditions_en, p.growing_conditions_tl,
                       p.soil_notes_en, p.soil_notes_tl, p.reference_sources,
                       p.method_note, p.data_kind, p.dataset_version,
                       d.metadata
                FROM crops c
                JOIN crop_profiles p ON p.crop_id = c.crop_id
                  AND p.dataset_version = %s
                JOIN dataset_metadata d ON d.dataset_version = p.dataset_version
                WHERE c.crop_id = %s AND c.active = TRUE
                """,
                (self.configuration.dataset_version, crop_id),
            ).fetchone()
            if row is None:
                raise ContextServiceError(
                    "DATASET_NOT_READY",
                    "This crop profile is not available in the configured dataset.",
                )
            metadata = row["metadata"] or {}
            return {
                **{key: value for key, value in row.items() if key != "metadata"},
                "source_ids": self._split_sources(row["reference_sources"]),
                "dataset_provenance": metadata.get("provenance", {}),
                "links": {
                    "prices": f"/prices?crop_id={crop_id}",
                    "supply": f"/supply-map?crop_id={crop_id}",
                    "suitability": f"/suitability?crop_id={crop_id}",
                },
            }

        return self._run(operation)

    def list_geographies(
        self,
        level: str | None,
        search: str | None,
        for_prices: bool,
        crop_id: str | None,
        limit: int,
    ) -> dict[str, Any]:
        cleaned_search = search.strip().casefold() if search else None

        def operation(connection):
            filters = [
                "g.active = TRUE",
                "g.country = 'Philippines'",
                "g.island_group = 'Luzon'",
            ]
            parameters: list[object] = []
            if level:
                filters.append("g.level = %s")
                parameters.append(level)
            if cleaned_search:
                filters.append("position(%s in lower(g.name)) > 0")
                parameters.append(cleaned_search)
            if for_prices:
                price_filter = (
                    " AND ph.crop_id = %s" if crop_id is not None else ""
                )
                filters.append(
                    "EXISTS (SELECT 1 FROM price_history ph "
                    "WHERE ph.geography_id = g.id AND ph.dataset_version = %s"
                    f"{price_filter})"
                )
                parameters.append(self.configuration.dataset_version)
                if crop_id is not None:
                    parameters.append(crop_id)
            rows = connection.execute(
                f"""
                SELECT DISTINCT g.geography_id, g.name, g.level, g.code,
                       parent.geography_id AS parent_geography_id,
                       parent.name AS parent_name
                FROM geographies g
                LEFT JOIN geographies parent ON parent.id = g.parent_id
                WHERE {' AND '.join(filters)}
                ORDER BY g.name
                LIMIT %s
                """,
                (*parameters, limit),
            ).fetchall()
            return {
                "items": [dict(row) for row in rows],
                "dataset_version": self.configuration.dataset_version,
            }

        return self._run(operation)

    @staticmethod
    def _subtract_months(value: date, months: int) -> date:
        month_index = value.year * 12 + value.month - 1 - months
        year, zero_based_month = divmod(month_index, 12)
        month = zero_based_month + 1
        return date(year, month, min(value.day, monthrange(year, month)[1]))

    def get_prices(
        self,
        crop_id: str,
        geography_id: str | None,
        time_range: str,
        start_date: date | None,
        end_date: date | None,
        limit: int,
    ) -> dict[str, Any]:
        if start_date and end_date and start_date > end_date:
            raise ContextServiceError(
                "INVALID_DATE_RANGE", "The start date must be before the end date.", 422
            )

        def operation(connection):
            self._require_crop(connection, crop_id)
            if geography_id:
                self._require_geography(connection, geography_id)
            parameters: list[object] = [crop_id, self.configuration.dataset_version]
            geography_filter = ""
            if geography_id:
                geography_filter = " AND g.geography_id = %s"
                parameters.append(geography_id)
            maximum = connection.execute(
                f"""
                SELECT max(ph.price_date) AS latest_date
                FROM price_history ph
                JOIN geographies g ON g.id = ph.geography_id
                WHERE ph.crop_id = %s AND ph.dataset_version = %s{geography_filter}
                """,
                parameters,
            ).fetchone()["latest_date"]
            range_months = {"1m": 1, "3m": 3, "1y": 12}.get(time_range)
            effective_start = start_date
            if effective_start is None and maximum is not None and range_months is not None:
                effective_start = self._subtract_months(maximum, range_months)
            effective_end = end_date or maximum
            if effective_start and effective_end and effective_start > effective_end:
                raise ContextServiceError(
                    "INVALID_DATE_RANGE",
                    "The start date must be before the end date.",
                    422,
                )

            filters = ["ph.crop_id = %s", "ph.dataset_version = %s"]
            query_parameters: list[object] = [crop_id, self.configuration.dataset_version]
            if geography_id:
                filters.append("g.geography_id = %s")
                query_parameters.append(geography_id)
            if effective_start:
                filters.append("ph.price_date >= %s")
                query_parameters.append(effective_start)
            if effective_end:
                filters.append("ph.price_date <= %s")
                query_parameters.append(effective_end)
            rows = connection.execute(
                f"""
                SELECT ph.price_date AS date, ph.price_php_per_kg,
                       ph.currency, ph.price_unit, ph.data_kind,
                       ph.dataset_version, ph.reference_sources,
                       g.geography_id, g.name AS geography_name
                FROM price_history ph
                JOIN geographies g ON g.id = ph.geography_id
                WHERE {' AND '.join(filters)}
                ORDER BY ph.price_date, g.name
                LIMIT %s
                """,
                (*query_parameters, limit),
            ).fetchall()
            records = [dict(row) for row in rows]
            if any(_price_number(row["price_php_per_kg"]) is None for row in records):
                raise ContextServiceError(
                    "DATASET_NOT_READY",
                    "The configured price data contains an invalid value.",
                )
            metadata = self._require_active_dataset(connection)
            provenance = (metadata["metadata"] or {}).get("provenance", {}).get(
                "price_history", {}
            )
            records = [dict(row) for row in rows]
            record_kinds = {row["data_kind"] for row in records}
            data_kind = (
                next(iter(record_kinds))
                if len(record_kinds) == 1
                else "mixed"
                if record_kinds
                else metadata["data_kind"]
            )
            return {
                "crop_id": crop_id,
                "geography_id": geography_id,
                "range": time_range,
                "start_date": effective_start,
                "end_date": effective_end,
                "currency": "PHP",
                "unit": "PHP/kg",
                "dataset_version": self.configuration.dataset_version,
                "data_kind": data_kind,
                "provenance": provenance,
                "records": records,
            }

        return self._run(operation)

    def get_suitability(self, crop_id: str, geography_id: str) -> dict[str, Any] | None:
        def operation(connection):
            self._require_crop(connection, crop_id)
            self._require_geography(connection, geography_id)
            row = connection.execute(
                """
                SELECT c.crop_id, g.geography_id, g.name AS geography_name,
                       s.suitability_class, s.dataset_version, s.data_kind,
                       s.reference_sources, s.method_note
                FROM crops c
                CROSS JOIN geographies g
                LEFT JOIN soil_suitability s ON s.crop_id = c.crop_id
                  AND s.geography_id = g.id
                  AND s.dataset_version = %s
                WHERE c.crop_id = %s AND g.geography_id = %s
                  AND c.active = TRUE AND g.active = TRUE
                """,
                (self.configuration.dataset_version, crop_id, geography_id),
            ).fetchone()
            if row is None:
                return None
            if row["suitability_class"] is None:
                return {
                    "crop_id": crop_id,
                    "geography_id": geography_id,
                    "geography_name": row["geography_name"],
                    "suitability_class": "no_data",
                    "dataset_version": self.configuration.dataset_version,
                    "data_kind": None,
                    "source_ids": [],
                    "method_note": None,
                }
            return {
                **dict(row),
                "source_ids": self._split_sources(row["reference_sources"]),
            }

        return self._run(operation)

    def get_supply_map(
        self, crop_id: str, period: MapPeriod
    ) -> dict[str, Any] | None:
        def operation(connection):
            self._require_crop(connection, crop_id)
            region_rows = connection.execute(
                """
                WITH locations AS (
                    SELECT geography.id AS geography_id,
                           CASE WHEN parent.level = 'region' THEN parent.id
                                ELSE parent.parent_id END AS region_database_id
                    FROM geographies geography
                    JOIN geographies parent ON parent.id = geography.parent_id
                    WHERE geography.level = 'municipality_city'
                      AND geography.active = TRUE
                      AND geography.country = 'Philippines'
                      AND geography.island_group = 'Luzon'
                )
                SELECT region.geography_id, region.name,
                       count(locations.geography_id) AS geography_count,
                       count(snapshot.id) AS snapshot_count,
                       count(snapshot.reference_area_ha) AS reference_count,
                       sum(snapshot.planned_area_ha) AS planned_context_area_ha,
                       sum(snapshot.reference_area_ha) AS reference_context_area_ha,
                       count(DISTINCT snapshot.data_kind) AS data_kind_count,
                       min(snapshot.data_kind) AS snapshot_data_kind
                FROM geographies region
                LEFT JOIN locations ON locations.region_database_id = region.id
                LEFT JOIN supply_snapshots snapshot
                  ON snapshot.geography_id = locations.geography_id
                 AND snapshot.crop_id = %s
                 AND snapshot.period_start = %s
                 AND snapshot.period_end = %s
                 AND snapshot.period_kind = %s
                 AND snapshot.dataset_version = %s
                WHERE region.level = 'region' AND region.active = TRUE
                  AND region.country = 'Philippines' AND region.island_group = 'Luzon'
                GROUP BY region.id, region.geography_id, region.name
                ORDER BY region.name
                """,
                (
                    crop_id,
                    period.period_start,
                    period.period_end,
                    period.period_kind,
                    self.configuration.dataset_version,
                ),
            ).fetchall()
            records = []
            for row in region_rows:
                is_complete = (
                    row["geography_count"] > 0
                    and row["snapshot_count"] == row["geography_count"]
                    and row["reference_count"] == row["geography_count"]
                    and row["data_kind_count"] == 1
                    and row["snapshot_data_kind"] == "synthetic_demo"
                    and row["reference_context_area_ha"] is not None
                    and row["reference_context_area_ha"] > 0
                )
                ratio = None
                level = "no_data"
                if is_complete:
                    ratio = (
                        row["planned_context_area_ha"] / row["reference_context_area_ha"]
                    ).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
                    if ratio < self.configuration.low_below:
                        level = "low"
                    elif ratio > self.configuration.high_above:
                        level = "high"
                    else:
                        level = "moderate"
                records.append(
                    {
                        "geography_id": row["geography_id"],
                        "name": row["name"],
                        "geography_level": "region",
                        "period_start": period.period_start,
                        "period_end": period.period_end,
                        "period_kind": period.period_kind,
                        "planned_context_area_ha": (
                            row["planned_context_area_ha"] if is_complete else None
                        ),
                        "reference_context_area_ha": (
                            row["reference_context_area_ha"] if is_complete else None
                        ),
                        "ratio": ratio,
                        "level": level,
                        "data_status": "available" if is_complete else "no_data",
                        "data_kind": "derived" if is_complete else None,
                        "source_data_kind": "synthetic_demo" if is_complete else None,
                        "dataset_version": self.configuration.dataset_version,
                        "source_note": (
                            "Regional totals from supply_snapshots context. "
                            "These values are not registered farmer planting plans."
                        ),
                    }
                )
            return {
                "crop_id": crop_id,
                "period": {
                    "period_start": period.period_start,
                    "period_end": period.period_end,
                    "period_kind": period.period_kind,
                },
                "available_periods": [
                    {
                        "period_start": item.period_start,
                        "period_end": item.period_end,
                        "period_kind": item.period_kind,
                    }
                    for item in self.configuration.periods
                ],
                "geography_level": "region",
                "data_kind": "derived",
                "source_data_kind": "synthetic_demo",
                "dataset_version": self.configuration.dataset_version,
                "source_note": (
                    "Regional totals from supply_snapshots context. "
                    "These values are not registered farmer planting plans."
                ),
                "items": records,
            }

        return self._run(operation)


def get_context_repository() -> ContextRepository:
    try:
        return PostgresContextRepository.from_environment()
    except ContextServiceError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail={"code": error.code, "message": error.message},
        ) from None


def get_weather_provider() -> WeatherProvider:
    return OpenMeteoProvider()


CONTEXT_REPOSITORY_DEPENDENCY = Depends(get_context_repository)
WEATHER_PROVIDER_DEPENDENCY = Depends(get_weather_provider)


def _service_error(error: ContextServiceError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    ) from None


def _price_number(value: Decimal | None) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (OverflowError, ValueError):
        return None
    return number if math.isfinite(number) else None


class PriceRecordResponse(BaseModel):
    date: date
    price_php_per_kg: Decimal
    currency: Literal["PHP"]
    price_unit: Literal["PHP/kg"]
    data_kind: str
    dataset_version: str
    reference_sources: str | None
    geography_id: str
    geography_name: str

    @field_serializer("price_php_per_kg", when_used="json")
    def decimal_as_number(self, value: Decimal) -> float | str:
        number = _price_number(value)
        if number is None:
            raise ValueError("Price must be a finite number.")
        return number


class PriceHistoryResponse(BaseModel):
    crop_id: str
    geography_id: str | None
    range: str
    start_date: date | None
    end_date: date | None
    currency: Literal["PHP"]
    unit: Literal["PHP/kg"]
    dataset_version: str
    data_kind: str
    provenance: dict[str, Any]
    records: list[PriceRecordResponse]


def _load_map_geometry() -> dict[str, Any]:
    try:
        with MAP_GEOMETRY_PATH.open(encoding="utf-8") as file:
            geometry = json.load(file)
    except (OSError, ValueError):
        raise HTTPException(
            status_code=503,
            detail={
                "code": "MAP_GEOMETRY_NOT_READY",
                "message": "The local Luzon map layer is not available.",
            },
        ) from None
    if geometry.get("type") != "FeatureCollection" or len(geometry.get("features", [])) != 8:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "MAP_GEOMETRY_NOT_READY",
                "message": "The local Luzon map layer is not available.",
            },
        )
    return geometry


@lru_cache(maxsize=1)
def _map_geometry() -> dict[str, Any]:
    return _load_map_geometry()


def _ring_centroid(ring: list[list[float]]) -> tuple[float, float, float]:
    cross_sum = 0.0
    longitude_sum = 0.0
    latitude_sum = 0.0
    for point, following in zip(ring, [*ring[1:], ring[0]], strict=True):
        cross = point[0] * following[1] - following[0] * point[1]
        cross_sum += cross
        longitude_sum += (point[0] + following[0]) * cross
        latitude_sum += (point[1] + following[1]) * cross
    if abs(cross_sum) < 1e-12:
        points = ring[:-1] if len(ring) > 1 and ring[0] == ring[-1] else ring
        return (
            sum(point[0] for point in points) / len(points),
            sum(point[1] for point in points) / len(points),
            0.0,
        )
    return longitude_sum / (3 * cross_sum), latitude_sum / (3 * cross_sum), abs(cross_sum) / 2


def _geometry_centroid(geometry: dict[str, Any]) -> tuple[float, float]:
    coordinates = geometry["coordinates"]
    polygons = [coordinates] if geometry["type"] == "Polygon" else coordinates
    centroids = [_ring_centroid(polygon[0]) for polygon in polygons if polygon]
    total_area = sum(item[2] for item in centroids)
    if total_area <= 0:
        raise ValueError("Map geometry has no usable area.")
    return (
        sum(longitude * area for longitude, _, area in centroids) / total_area,
        sum(latitude * area for _, latitude, area in centroids) / total_area,
    )


def _weather_location(geography_id: str) -> dict[str, Any]:
    for feature in _map_geometry()["features"]:
        properties = feature["properties"]
        if properties.get("geography_id") == geography_id:
            try:
                longitude, latitude = _geometry_centroid(feature["geometry"])
            except (KeyError, TypeError, ValueError):
                break
            return {
                "geography_id": geography_id,
                "name": properties["name"],
                "latitude": latitude,
                "longitude": longitude,
            }
    raise HTTPException(
        status_code=404,
        detail={"code": "UNSUPPORTED_WEATHER_LOCATION", "message": "Choose a Luzon region."},
    )


def _require_weather_consent(consent: bool) -> None:
    if not consent:
        raise HTTPException(
            status_code=428,
            detail={
                "code": "WEATHER_CONSENT_REQUIRED",
                "message": "Choose Continue before TANIM connects to live weather.",
            },
        )


@router.get("/crops")
def list_crops(
    q: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=5000),
    repository: ContextRepository = CONTEXT_REPOSITORY_DEPENDENCY,
) -> dict[str, Any]:
    try:
        return repository.list_crops(q, category, limit, offset)
    except ContextServiceError as error:
        _service_error(error)


@router.get("/crops/{crop_id}")
def get_crop(
    crop_id: str,
    repository: ContextRepository = CONTEXT_REPOSITORY_DEPENDENCY,
) -> dict[str, Any]:
    try:
        crop = repository.get_crop(crop_id)
    except ContextServiceError as error:
        _service_error(error)
    if crop is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "UNSUPPORTED_CROP", "message": "This crop is not supported."},
        )
    return crop


@router.get("/geographies")
def list_geographies(
    level: Literal["region", "province", "municipality_city"] | None = None,
    q: str | None = Query(default=None, max_length=120),
    for_prices: bool = False,
    crop_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    repository: ContextRepository = CONTEXT_REPOSITORY_DEPENDENCY,
) -> dict[str, Any]:
    try:
        return repository.list_geographies(level, q, for_prices, crop_id, limit)
    except ContextServiceError as error:
        _service_error(error)


@router.get("/prices", response_model=PriceHistoryResponse)
def get_prices(
    crop_id: str = Query(min_length=1, max_length=80),
    geography_id: str | None = Query(default=None, max_length=80),
    time_range: Literal["1m", "3m", "1y", "all"] = Query(default="1y", alias="range"),
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(default=500, ge=1, le=1000),
    repository: ContextRepository = CONTEXT_REPOSITORY_DEPENDENCY,
) -> dict[str, Any]:
    try:
        return repository.get_prices(
            crop_id, geography_id, time_range, start_date, end_date, limit
        )
    except ContextServiceError as error:
        _service_error(error)


@router.get("/suitability")
def get_suitability(
    crop_id: str = Query(min_length=1, max_length=80),
    geography_id: str = Query(min_length=1, max_length=80),
    repository: ContextRepository = CONTEXT_REPOSITORY_DEPENDENCY,
) -> dict[str, Any]:
    try:
        result = repository.get_suitability(crop_id, geography_id)
    except ContextServiceError as error:
        _service_error(error)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "UNSUPPORTED_GEOGRAPHY", "message": "This location is not supported."},
        )
    return result


@router.get("/supply-map")
def get_supply_map(
    crop_id: str = Query(min_length=1, max_length=80),
    period: str = Query(default="current", max_length=10),
    repository: ContextRepository = CONTEXT_REPOSITORY_DEPENDENCY,
) -> dict[str, Any]:
    try:
        configuration = load_context_configuration()
        if period == "current":
            selected = next(
                item for item in configuration.periods if item.period_kind == "current_supply"
            )
        else:
            try:
                requested_start = date.fromisoformat(period)
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail={"code": "INVALID_PERIOD", "message": "Choose a supported map period."},
                ) from None
            selected = next(
                (item for item in configuration.periods if item.period_start == requested_start),
                None,
            )
            if selected is None:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "UNSUPPORTED_PERIOD",
                        "message": "Choose a supported map period.",
                    },
                )
        result = repository.get_supply_map(crop_id, selected)
    except ContextServiceError as error:
        _service_error(error)
    except StopIteration:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATASET_NOT_READY",
                "message": "The configured dataset has no current map period.",
            },
        ) from None
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "UNSUPPORTED_CROP", "message": "This crop is not supported."},
        )
    return result


@router.get("/map-geometry")
def get_map_geometry() -> JSONResponse:
    return JSONResponse(content=_map_geometry())


@router.get("/weather/status")
def weather_status(
    consent: bool = False,
    provider: WeatherProvider = WEATHER_PROVIDER_DEPENDENCY,
) -> dict[str, Any]:
    _require_weather_consent(consent)
    try:
        provider.check_reachable()
    except WeatherProviderError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail={"code": error.code, "message": WEATHER_FAILURE_MESSAGE},
        ) from None
    return {"status": "available", "provider": provider.name}


@router.get("/weather")
def get_weather(
    geography_id: str = Query(min_length=1, max_length=80),
    consent: bool = False,
    provider: WeatherProvider = WEATHER_PROVIDER_DEPENDENCY,
) -> dict[str, Any]:
    _require_weather_consent(consent)
    location = _weather_location(geography_id)
    try:
        report = provider.get_forecast(location["latitude"], location["longitude"])
    except WeatherProviderError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail={"code": error.code, "message": WEATHER_FAILURE_MESSAGE},
        ) from None
    return {
        "status": "available",
        "provider": provider.name,
        "data_kind": "live_external",
        "geography_id": location["geography_id"],
        "location": location["name"],
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        **report,
    }
