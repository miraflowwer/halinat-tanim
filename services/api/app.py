import logging
import math
import os
from datetime import date
from decimal import Decimal
from typing import Literal

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from services.engine.config import load_engine_config
from services.engine.models import RiskCheckInput, RiskCheckResult
from services.engine.periods import EngineInputError
from services.engine.repository import (
    DatasetNotReadyError,
    PostgresRiskRepository,
    RepositoryError,
)
from services.engine.service import RiskService

logger = logging.getLogger(__name__)
app = FastAPI(title="TANIM API", version="0.1.0")


def _decimal_as_json_number(value: Decimal | None) -> float | str | None:
    if value is None:
        return None
    numeric = float(value)
    if math.isfinite(numeric):
        return numeric
    return format(value, "f")


class RiskCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    crop_id: str = Field(min_length=1)
    geography_id: str = Field(min_length=1)
    proposed_area_ha: Decimal
    harvest_start: str = Field(min_length=1)
    harvest_end: str = Field(min_length=1)
    comparison_crop_ids: list[str] = Field(default_factory=list)

    @field_validator("crop_id", "geography_id", "harvest_start", "harvest_end")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be blank")
        return cleaned

    @field_validator("proposed_area_ha")
    @classmethod
    def area_must_be_positive_and_finite(cls, value: Decimal) -> Decimal:
        if not value.is_finite() or value <= 0:
            raise ValueError("proposed_area_ha must be a finite number greater than zero")
        return value

    @field_validator("comparison_crop_ids")
    @classmethod
    def comparison_ids_must_not_be_blank(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("comparison crop IDs must not be blank")
        return cleaned


class ComparisonResponse(BaseModel):
    crop_id: str
    existing_planned_area_ha: Decimal
    reference_area_ha: Decimal | None
    current_ratio: Decimal | None
    current_risk: Literal["low", "moderate", "high"] | None
    projected_ratio_if_same_area: Decimal | None
    projected_risk_if_same_area: Literal["low", "moderate", "high"] | None

    @field_serializer(
        "existing_planned_area_ha",
        "reference_area_ha",
        "current_ratio",
        "projected_ratio_if_same_area",
        when_used="json",
    )
    def decimal_as_number(self, value: Decimal | None) -> float | str | None:
        return _decimal_as_json_number(value)


class RiskCheckResponse(BaseModel):
    status: Literal["available", "unavailable"]
    crop_id: str
    geography_id: str
    requested_harvest_start: date
    requested_harvest_end: date
    planning_period_start: date
    planning_period_end: date
    existing_planned_area_ha: Decimal
    proposed_area_ha: Decimal
    projected_planned_area_ha: Decimal
    reference_area_ha: Decimal | None
    ratio: Decimal | None
    risk: Literal["low", "moderate", "high"] | None
    contributing_plan_count: int
    assumption_version: str
    dataset_version: str
    explanation: str
    comparisons: list[ComparisonResponse]

    @field_serializer(
        "existing_planned_area_ha",
        "proposed_area_ha",
        "projected_planned_area_ha",
        "reference_area_ha",
        "ratio",
        when_used="json",
    )
    def decimal_as_number(self, value: Decimal | None) -> float | str | None:
        return _decimal_as_json_number(value)


def build_risk_service() -> RiskService:
    return RiskService(
        PostgresRiskRepository.from_environment(),
        load_engine_config(),
    )


def _risk_response(result: RiskCheckResult) -> RiskCheckResponse:
    return RiskCheckResponse(
        status=result.status,
        crop_id=result.crop_id,
        geography_id=result.geography_id,
        requested_harvest_start=result.requested_harvest_start,
        requested_harvest_end=result.requested_harvest_end,
        planning_period_start=result.planning_period_start,
        planning_period_end=result.planning_period_end,
        existing_planned_area_ha=result.existing_planned_area_ha,
        proposed_area_ha=result.proposed_area_ha,
        projected_planned_area_ha=result.projected_planned_area_ha,
        reference_area_ha=result.reference_area_ha,
        ratio=result.ratio,
        risk=result.risk,
        contributing_plan_count=result.contributing_plan_count,
        assumption_version=result.assumption_version,
        dataset_version=result.dataset_version,
        explanation=result.explanation,
        comparisons=[
            ComparisonResponse(**comparison.__dict__) for comparison in result.comparisons
        ],
    )


def _validation_code(errors: list[dict[str, object]]) -> str:
    locations = {str(part) for error in errors for part in error.get("loc", ())}
    if "proposed_area_ha" in locations:
        return "INVALID_AREA"
    if "harvest_start" in locations or "harvest_end" in locations:
        return "INVALID_DATE"
    return "INVALID_REQUEST"


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(_request, exception: RequestValidationError):
    errors = exception.errors()
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "code": _validation_code(errors),
                "message": "The risk-check request is not valid.",
            }
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the API process can serve requests."""
    return {"status": "healthy"}


@app.get("/health/db")
def database_health() -> dict[str, str]:
    """Check PostgreSQL without returning connection details to the caller."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "unavailable",
                "message": "DATABASE_URL is not configured.",
            },
        )

    try:
        with psycopg.connect(database_url, connect_timeout=3) as connection:
            connection.execute("SELECT 1")
    except (psycopg.Error, ValueError) as error:
        logger.warning("Database health check failed (%s).", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "unavailable",
                "message": "PostgreSQL is not reachable. Check DATABASE_URL and the local server.",
            },
        ) from None

    return {"status": "healthy", "database": "reachable"}


@app.post("/risk/check", response_model=RiskCheckResponse)
def risk_check(request: RiskCheckRequest) -> RiskCheckResponse:
    try:
        result = build_risk_service().check(
            RiskCheckInput(
                crop_id=request.crop_id,
                geography_id=request.geography_id,
                proposed_area_ha=request.proposed_area_ha,
                harvest_start=request.harvest_start,
                harvest_end=request.harvest_end,
                comparison_crop_ids=tuple(request.comparison_crop_ids),
            )
        )
    except EngineInputError as error:
        raise HTTPException(
            status_code=400,
            detail={"code": error.code, "message": error.message},
        ) from None
    except DatasetNotReadyError:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATASET_NOT_READY",
                "message": (
                    "The configured TANIM dataset is not seeded. "
                    "Run the data seed step and retry."
                ),
            },
        ) from None
    except RepositoryError:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATABASE_UNAVAILABLE",
                "message": (
                    "TANIM cannot read the local data service right now. "
                    "Check PostgreSQL and retry."
                ),
            },
        ) from None
    except (OSError, KeyError, ValueError) as error:
        logger.warning("Risk configuration could not be loaded (%s).", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATASET_NOT_READY",
                "message": "The configured TANIM dataset is not ready.",
            },
        ) from None
    return _risk_response(result)
