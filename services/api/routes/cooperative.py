"""Organization-scoped aggregate overview for Cooperative accounts."""

from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, field_serializer

from services.api.auth import AuthenticatedSession
from services.api.dependencies import AUTHENTICATED_SESSION
from services.api.platform_repository import (
    PlatformRepositoryError,
    PostgresPlatformRepository,
)
from services.api.routes.plans import PLATFORM_REPOSITORY
from services.engine.config import load_engine_config
from services.engine.periods import EngineInputError, resolve_supported_period
from services.engine.repository import DatasetNotReadyError, RepositoryError
from services.engine.service import RiskService

router = APIRouter(tags=["cooperative"])


class RiskContextResponse(BaseModel):
    status: Literal["available", "unavailable"]
    risk: Literal["low", "moderate", "high"] | None
    planned_area_ha: Decimal | None
    reference_area_ha: Decimal | None
    ratio: Decimal | None
    contributing_plan_count: int
    assumption_version: str
    dataset_version: str
    explanation: str
    community_detail_status: Literal["available", "limited_for_privacy"]

    @field_serializer(
        "planned_area_ha",
        "reference_area_ha",
        "ratio",
        when_used="json",
    )
    def decimal_as_number(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None


class CooperativeAggregateResponse(BaseModel):
    crop_id: str
    crop_name_en: str
    crop_name_tl: str | None
    geography_id: str
    geography_name: str
    period_start: str
    period_end: str
    plan_count: int
    planned_area_ha: Decimal
    community_risk: RiskContextResponse

    @field_serializer("planned_area_ha", when_used="json")
    def decimal_as_number(self, value: Decimal) -> float:
        return float(value)


class CooperativeOverviewResponse(BaseModel):
    organization_name: str
    organization_join_code: str | None = None
    total_active_plan_count: int
    total_planned_area_ha: Decimal
    aggregates: list[CooperativeAggregateResponse]

    @field_serializer("total_planned_area_ha", when_used="json")
    def decimal_as_number(self, value: Decimal) -> float:
        return float(value)


def _platform_failure() -> None:
    raise HTTPException(
        status_code=503,
        detail={
            "code": "DATABASE_UNAVAILABLE",
            "message": "TANIM cannot load Cooperative plans right now. Check PostgreSQL and retry.",
        },
    ) from None


def _risk_service(request: Request) -> RiskService:
    factory = getattr(request.app.state, "risk_service_factory", None)
    if callable(factory):
        return factory()
    from services.engine.repository import PostgresRiskRepository

    return RiskService(PostgresRiskRepository.from_environment(), load_engine_config())


def _risk_failure() -> None:
    raise HTTPException(
        status_code=503,
        detail={
            "code": "RISK_CONTEXT_UNAVAILABLE",
            "message": "TANIM cannot load community risk context right now. Retry later.",
        },
    ) from None


@router.get("/cooperative/overview", response_model=CooperativeOverviewResponse)
def cooperative_overview(
    request: Request,
    session: AuthenticatedSession = AUTHENTICATED_SESSION,
    repository: PostgresPlatformRepository = PLATFORM_REPOSITORY,
) -> CooperativeOverviewResponse:
    if session.user.role != "cooperative":
        raise HTTPException(
            status_code=403,
            detail={
                "code": "COOPERATIVE_ROLE_REQUIRED",
                "message": "This view is for Cooperative accounts.",
            },
        )
    try:
        result = repository.cooperative_plans(session.user.user_id)
    except PlatformRepositoryError:
        _platform_failure()
    if result is None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "ORGANIZATION_REQUIRED",
                "message": "This Cooperative account has no organization membership.",
            },
        )
    organization, plans = result

    try:
        config = load_engine_config()
        risk_service = _risk_service(request)
        grouped: dict[tuple[str, str, str, str, str, str | None, str], dict[str, object]] = {}
        for plan in plans:
            _, _, period = resolve_supported_period(
                plan.harvest_start,
                plan.harvest_end,
                config,
            )
            key = (
                plan.crop_id,
                plan.geography_id,
                period.start.isoformat(),
                period.end.isoformat(),
                plan.crop_name_en,
                plan.crop_name_tl,
                plan.geography_name,
            )
            group = grouped.setdefault(
                key,
                {
                    "plan_count": 0,
                    "planned_area_ha": Decimal("0"),
                },
            )
            group["plan_count"] = int(group["plan_count"]) + 1
            group["planned_area_ha"] = Decimal(group["planned_area_ha"]) + plan.area_ha

        aggregates: list[CooperativeAggregateResponse] = []
        for key, group in grouped.items():
            (
                crop_id,
                geography_id,
                period_start,
                period_end,
                crop_name_en,
                crop_name_tl,
                geography_name,
            ) = key
            context = risk_service.current_context(
                crop_id=crop_id,
                geography_id=geography_id,
                harvest_start=period_start,
                harvest_end=period_end,
            )
            aggregates.append(
                CooperativeAggregateResponse(
                    crop_id=crop_id,
                    crop_name_en=crop_name_en,
                    crop_name_tl=crop_name_tl,
                    geography_id=geography_id,
                    geography_name=geography_name,
                    period_start=period_start,
                    period_end=period_end,
                    plan_count=int(group["plan_count"]),
                    planned_area_ha=Decimal(group["planned_area_ha"]),
                    community_risk=RiskContextResponse(
                        status=context.status,
                        risk=context.risk,
                        planned_area_ha=(
                            None
                            if context.contributing_plan_count < 2
                            else context.planned_area_ha
                        ),
                        reference_area_ha=context.reference_area_ha,
                        ratio=(
                            None
                            if context.contributing_plan_count < 2
                            else context.ratio
                        ),
                        contributing_plan_count=context.contributing_plan_count,
                        assumption_version=context.assumption_version,
                        dataset_version=context.dataset_version,
                        explanation=(
                            f"{context.explanation} Community detail is limited because "
                            "fewer than two registered plans contribute to this context."
                            if context.contributing_plan_count < 2
                            else context.explanation
                        ),
                        community_detail_status=(
                            "limited_for_privacy"
                            if context.contributing_plan_count < 2
                            else "available"
                        ),
                    ),
                )
            )
    except (OSError, KeyError, ValueError, EngineInputError, DatasetNotReadyError, RepositoryError):
        _risk_failure()

    aggregates.sort(
        key=lambda item: (
            item.period_start,
            item.crop_name_en.casefold(),
            item.geography_name.casefold(),
        )
    )
    return CooperativeOverviewResponse(
        organization_name=organization.name,
        organization_join_code=organization.join_code,
        total_active_plan_count=sum(item.plan_count for item in aggregates),
        total_planned_area_ha=sum(
            (item.planned_area_ha for item in aggregates),
            start=Decimal("0"),
        ),
        aggregates=aggregates,
    )
