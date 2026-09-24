"""Small shared lookups needed by planting-plan forms."""

from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.engine.config import load_engine_config

router = APIRouter(tags=["lookups"])


class PlanningPeriodResponse(BaseModel):
    period_start: date
    period_end: date


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
