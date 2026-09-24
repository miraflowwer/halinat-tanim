"""Small shared lookups needed by planting-plan forms."""

from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.api.platform_repository import PlatformRepositoryError, PostgresPlatformRepository
from services.api.routes.plans import PLATFORM_REPOSITORY
from services.engine.config import load_engine_config

router = APIRouter(tags=["lookups"])


class CropResponse(BaseModel):
    crop_id: str
    canonical_name_en: str
    canonical_name_tl: str | None
    scientific_name: str | None
    category: str


class GeographyResponse(BaseModel):
    geography_id: str
    name: str
    level: str
    parent_geography_id: str | None


class PlanningPeriodResponse(BaseModel):
    period_start: date
    period_end: date


def _unavailable() -> None:
    raise HTTPException(
        status_code=503,
        detail={
            "code": "DATABASE_UNAVAILABLE",
            "message": "TANIM cannot load the plan form right now. Check PostgreSQL and retry.",
        },
    ) from None


@router.get("/crops", response_model=list[CropResponse])
def list_crops(
    repository: PostgresPlatformRepository = PLATFORM_REPOSITORY,
) -> list[CropResponse]:
    try:
        return [CropResponse(**crop) for crop in repository.list_crops()]
    except PlatformRepositoryError:
        _unavailable()


@router.get("/geographies", response_model=list[GeographyResponse])
def list_geographies(
    repository: PostgresPlatformRepository = PLATFORM_REPOSITORY,
) -> list[GeographyResponse]:
    try:
        return [GeographyResponse(**geography) for geography in repository.list_geographies()]
    except PlatformRepositoryError:
        _unavailable()


@router.get("/planning-periods", response_model=list[PlanningPeriodResponse])
def list_planning_periods() -> list[PlanningPeriodResponse]:
    try:
        config = load_engine_config()
    except (OSError, KeyError, ValueError):
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATASET_NOT_READY",
                "message": "The configured planning periods are not ready.",
            },
        ) from None
    return [
        PlanningPeriodResponse(period_start=period.start, period_end=period.end)
        for period in config.future_periods
    ]
