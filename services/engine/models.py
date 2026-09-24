"""Small domain models shared by the pure engine and its data adapter."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

RiskLevel = Literal["low", "moderate", "high"]
RiskStatus = Literal["available", "unavailable"]


@dataclass(frozen=True)
class PlanningPeriod:
    """A configured future planning period."""

    start: date
    end: date
    kind: str = "future_planning"


@dataclass(frozen=True)
class PlanRecord:
    """The planting-plan fields needed by the pure aggregation function."""

    crop_id: str
    geography_id: str
    area_ha: Decimal
    harvest_start: date
    harvest_end: date
    status: str


@dataclass(frozen=True)
class PlanAggregate:
    existing_planned_area_ha: Decimal
    contributing_plan_count: int


@dataclass(frozen=True)
class CropRecord:
    crop_id: str
    canonical_name_en: str


@dataclass(frozen=True)
class GeographyRecord:
    geography_id: str
    database_id: int
    name: str


@dataclass(frozen=True)
class ReferenceRecord:
    reference_area_ha: Decimal
    period_kind: str
    dataset_version: str


@dataclass(frozen=True)
class ComparisonResult:
    crop_id: str
    existing_planned_area_ha: Decimal
    reference_area_ha: Decimal | None
    current_ratio: Decimal | None
    current_risk: RiskLevel | None
    projected_ratio_if_same_area: Decimal | None
    projected_risk_if_same_area: RiskLevel | None
    contributing_plan_count: int = 0


@dataclass(frozen=True)
class RiskCheckInput:
    crop_id: str
    geography_id: str
    proposed_area_ha: Decimal
    harvest_start: date
    harvest_end: date
    comparison_crop_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class RiskCheckResult:
    status: RiskStatus
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
    risk: RiskLevel | None
    contributing_plan_count: int
    assumption_version: str
    dataset_version: str
    explanation: str
    comparisons: tuple[ComparisonResult, ...]


@dataclass(frozen=True)
class RiskContextResult:
    """Current community pressure for one crop, place, and planning period."""

    status: RiskStatus
    crop_id: str
    geography_id: str
    planning_period_start: date
    planning_period_end: date
    planned_area_ha: Decimal
    reference_area_ha: Decimal | None
    ratio: Decimal | None
    risk: RiskLevel | None
    contributing_plan_count: int
    assumption_version: str
    dataset_version: str
    explanation: str
