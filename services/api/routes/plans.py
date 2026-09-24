"""Authenticated planting-plan API routes."""

from datetime import date
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from services.api.auth import AuthenticatedSession
from services.api.dependencies import AUTHENTICATED_SESSION, CSRF_PROTECTED_SESSION
from services.api.platform_repository import (
    OrganizationMembershipRequired,
    PlanRecord,
    PlatformRepositoryError,
    PostgresPlatformRepository,
)
from services.api.validation import validate_planning_area
from services.engine.config import load_engine_config
from services.engine.periods import EngineInputError, resolve_supported_period

router = APIRouter(tags=["plans"])
class PlanInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    crop_id: str = Field(min_length=1, max_length=100)
    geography_id: str = Field(min_length=1, max_length=120)
    area_ha: Decimal
    planting_date: date
    harvest_start: date
    harvest_end: date

    @field_validator("crop_id", "geography_id")
    @classmethod
    def clean_identifiers(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("identifier must not be blank")
        return cleaned

    @field_validator("area_ha")
    @classmethod
    def validate_area(cls, value: Decimal) -> Decimal:
        return validate_planning_area(value, "area_ha")

    @model_validator(mode="after")
    def validate_dates(self):
        if self.harvest_end < self.harvest_start:
            raise ValueError("harvest_end cannot be before harvest_start")
        if self.planting_date > self.harvest_start:
            raise ValueError("planting_date cannot be after harvest_start")
        return self


class PlanCreateRequest(PlanInput):
    pass


class PlanUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    crop_id: str | None = Field(default=None, min_length=1, max_length=100)
    geography_id: str | None = Field(default=None, min_length=1, max_length=120)
    area_ha: Decimal | None = None
    planting_date: date | None = None
    harvest_start: date | None = None
    harvest_end: date | None = None

    @model_validator(mode="after")
    def require_a_non_null_change(self):
        if not self.model_fields_set:
            raise ValueError("at least one plan field is required")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("plan fields cannot be null")
        return self

    @field_validator("crop_id", "geography_id")
    @classmethod
    def clean_identifiers(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("identifier must not be blank")
        return cleaned

    @field_validator("area_ha")
    @classmethod
    def validate_area(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return validate_planning_area(value, "area_ha")


class PlanResponse(BaseModel):
    plan_id: int
    crop_id: str
    crop_name_en: str
    crop_name_tl: str | None
    geography_id: str
    geography_name: str
    area_ha: Decimal
    planting_date: date
    harvest_start: date
    harvest_end: date
    status: Literal["active", "cancelled", "completed"]

    @field_serializer("area_ha", when_used="json")
    def area_as_number(self, value: Decimal) -> float:
        return float(value)


def get_platform_repository(request: Request) -> PostgresPlatformRepository:
    factory = getattr(request.app.state, "platform_repository_factory", None)
    return factory() if callable(factory) else PostgresPlatformRepository.from_environment()


PLATFORM_REPOSITORY = Depends(get_platform_repository)


def _as_response(plan: PlanRecord) -> PlanResponse:
    return PlanResponse(
        plan_id=plan.plan_id,
        crop_id=plan.crop_id,
        crop_name_en=plan.crop_name_en,
        crop_name_tl=plan.crop_name_tl,
        geography_id=plan.geography_id,
        geography_name=plan.geography_name,
        area_ha=plan.area_ha,
        planting_date=plan.planting_date,
        harvest_start=plan.harvest_start,
        harvest_end=plan.harvest_end,
        status=plan.status,  # type: ignore[arg-type]
    )


def _repository_failure(error: PlatformRepositoryError) -> None:
    if isinstance(error, OrganizationMembershipRequired):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "ORGANIZATION_REQUIRED",
                "message": "This Cooperative account has no organization membership.",
            },
        ) from None
    raise HTTPException(
        status_code=503,
        detail={
            "code": "DATABASE_UNAVAILABLE",
            "message": "TANIM cannot save or read plans right now. Check PostgreSQL and retry.",
        },
    ) from None


def _validate_plan_values(plan: PlanInput | dict[str, object]) -> None:
    try:
        resolve_supported_period(
            plan.harvest_start,
            plan.harvest_end,
            load_engine_config(),
        )
    except EngineInputError as error:
        raise HTTPException(
            status_code=400,
            detail={"code": error.code, "message": error.message},
        ) from None
    except (OSError, KeyError, ValueError):
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATASET_NOT_READY",
                "message": "The configured planning periods are not ready.",
            },
        ) from None


def _validate_supported_crop_and_geography(
    repository: PostgresPlatformRepository,
    crop_id: str,
    geography_id: str,
) -> None:
    try:
        crop_is_active = repository.is_active_crop(crop_id)
        geography_is_supported = repository.is_supported_geography(geography_id)
    except PlatformRepositoryError as error:
        _repository_failure(error)
    if not crop_is_active:
        raise HTTPException(
            status_code=400,
            detail={"code": "UNSUPPORTED_CROP", "message": "Choose an active TANIM crop."},
        )
    if not geography_is_supported:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "UNSUPPORTED_GEOGRAPHY",
                "message": "Choose an active Luzon municipality or city.",
            },
        )


def _plan_values(plan: PlanRecord) -> dict[str, object]:
    return {
        "crop_id": plan.crop_id,
        "geography_id": plan.geography_id,
        "area_ha": plan.area_ha,
        "planting_date": plan.planting_date,
        "harvest_start": plan.harvest_start,
        "harvest_end": plan.harvest_end,
    }


@router.get("/plans", response_model=list[PlanResponse])
def list_plans(
    session: AuthenticatedSession = AUTHENTICATED_SESSION,
    repository: PostgresPlatformRepository = PLATFORM_REPOSITORY,
) -> list[PlanResponse]:
    try:
        plans = repository.list_plans(session.user.user_id)
    except PlatformRepositoryError as error:
        _repository_failure(error)
    return [_as_response(plan) for plan in plans]


@router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    request: PlanCreateRequest,
    session: AuthenticatedSession = CSRF_PROTECTED_SESSION,
    repository: PostgresPlatformRepository = PLATFORM_REPOSITORY,
) -> PlanResponse:
    _validate_plan_values(request)
    _validate_supported_crop_and_geography(
        repository,
        request.crop_id,
        request.geography_id,
    )
    try:
        plan = repository.create_plan(
            user_id=session.user.user_id,
            role=session.user.role,
            crop_id=request.crop_id,
            geography_id=request.geography_id,
            area_ha=request.area_ha,
            planting_date=request.planting_date,
            harvest_start=request.harvest_start,
            harvest_end=request.harvest_end,
        )
    except PlatformRepositoryError as error:
        _repository_failure(error)
    return _as_response(plan)


@router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: int = Path(ge=1),
    session: AuthenticatedSession = AUTHENTICATED_SESSION,
    repository: PostgresPlatformRepository = PLATFORM_REPOSITORY,
) -> PlanResponse:
    try:
        plan = repository.get_plan(session.user.user_id, plan_id)
    except PlatformRepositoryError as error:
        _repository_failure(error)
    if plan is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "PLAN_NOT_FOUND", "message": "This plan was not found."},
        )
    return _as_response(plan)


@router.patch("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(
    request: PlanUpdateRequest,
    plan_id: int = Path(ge=1),
    session: AuthenticatedSession = CSRF_PROTECTED_SESSION,
    repository: PostgresPlatformRepository = PLATFORM_REPOSITORY,
) -> PlanResponse:
    try:
        current = repository.get_plan(session.user.user_id, plan_id)
    except PlatformRepositoryError as error:
        _repository_failure(error)
    if current is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "PLAN_NOT_FOUND", "message": "This plan was not found."},
        )
    if current.status != "active":
        raise HTTPException(
            status_code=409,
            detail={"code": "PLAN_NOT_ACTIVE", "message": "Only active plans can be changed."},
        )

    values = _plan_values(current)
    values.update(request.model_dump(exclude_unset=True))
    try:
        validated = PlanInput.model_validate(values)
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_REQUEST", "message": str(error)},
        ) from None
    _validate_plan_values(validated)
    _validate_supported_crop_and_geography(
        repository,
        validated.crop_id,
        validated.geography_id,
    )
    try:
        updated = repository.update_plan(
            user_id=session.user.user_id,
            plan_id=plan_id,
            crop_id=validated.crop_id,
            geography_id=validated.geography_id,
            area_ha=validated.area_ha,
            planting_date=validated.planting_date,
            harvest_start=validated.harvest_start,
            harvest_end=validated.harvest_end,
        )
    except PlatformRepositoryError as error:
        _repository_failure(error)
    if updated is None:
        raise HTTPException(
            status_code=409,
            detail={"code": "PLAN_NOT_ACTIVE", "message": "Only active plans can be changed."},
        )
    return _as_response(updated)


@router.delete("/plans/{plan_id}", response_model=PlanResponse)
def cancel_plan(
    plan_id: int = Path(ge=1),
    session: AuthenticatedSession = CSRF_PROTECTED_SESSION,
    repository: PostgresPlatformRepository = PLATFORM_REPOSITORY,
) -> PlanResponse:
    try:
        current = repository.get_plan(session.user.user_id, plan_id)
    except PlatformRepositoryError as error:
        _repository_failure(error)
    if current is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "PLAN_NOT_FOUND", "message": "This plan was not found."},
        )
    if current.status == "completed":
        raise HTTPException(
            status_code=409,
            detail={"code": "PLAN_NOT_ACTIVE", "message": "A completed plan cannot be cancelled."},
        )
    try:
        cancelled = repository.cancel_plan(session.user.user_id, plan_id)
    except PlatformRepositoryError as error:
        _repository_failure(error)
    if cancelled is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "PLAN_NOT_FOUND", "message": "This plan was not found."},
        )
    return _as_response(cancelled)
