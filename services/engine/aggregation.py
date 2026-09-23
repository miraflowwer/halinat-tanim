"""Pure aggregation of registered planting plans."""

from collections.abc import Iterable
from datetime import date
from decimal import Decimal

from .models import PlanAggregate, PlanRecord


def _overlaps(
    harvest_start: date,
    harvest_end: date,
    period_start: date,
    period_end: date,
) -> bool:
    return harvest_start <= period_end and harvest_end >= period_start


def aggregate_relevant_plans(
    plans: Iterable[PlanRecord],
    *,
    crop_id: str,
    geography_id: str,
    period_start: date,
    period_end: date,
) -> PlanAggregate:
    """Sum only active plans for the requested crop, place, and overlap."""
    relevant = [
        plan
        for plan in plans
        if plan.status == "active"
        and plan.crop_id == crop_id
        and plan.geography_id == geography_id
        and _overlaps(plan.harvest_start, plan.harvest_end, period_start, period_end)
    ]
    return PlanAggregate(
        existing_planned_area_ha=sum(
            (Decimal(str(plan.area_ha)) for plan in relevant),
            Decimal("0"),
        ),
        contributing_plan_count=len(relevant),
    )
