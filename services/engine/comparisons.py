"""Informational crop comparison calculations."""

from decimal import Decimal

from .config import ENGINE_THRESHOLDS, RiskThresholds
from .models import ComparisonResult
from .risk import calculate_ratio, calculate_risk, classify_risk


def calculate_comparison(
    crop_id: str,
    existing_planned_area_ha: Decimal,
    reference_area_ha: Decimal | None,
    proposed_area_ha: Decimal,
    thresholds: RiskThresholds = ENGINE_THRESHOLDS,
) -> ComparisonResult:
    """Calculate current and hypothetical same-area pressure for one crop."""
    if reference_area_ha is None or reference_area_ha <= 0:
        return ComparisonResult(
            crop_id=crop_id,
            existing_planned_area_ha=existing_planned_area_ha,
            reference_area_ha=None,
            current_ratio=None,
            current_risk=None,
            projected_ratio_if_same_area=None,
            projected_risk_if_same_area=None,
        )

    current_ratio = calculate_ratio(existing_planned_area_ha, reference_area_ha)
    projected = calculate_risk(
        existing_planned_area_ha,
        proposed_area_ha,
        reference_area_ha,
        thresholds,
    )
    return ComparisonResult(
        crop_id=crop_id,
        existing_planned_area_ha=existing_planned_area_ha,
        reference_area_ha=reference_area_ha,
        current_ratio=current_ratio,
        current_risk=classify_risk(current_ratio, thresholds),
        projected_ratio_if_same_area=projected.ratio,
        projected_risk_if_same_area=projected.risk,
    )


def sort_comparisons(comparisons: list[ComparisonResult]) -> tuple[ComparisonResult, ...]:
    """Sort available projected ratios first, with a stable crop-id tie-breaker."""
    return tuple(
        sorted(
            comparisons,
            key=lambda item: (
                item.projected_ratio_if_same_area is None,
                item.projected_ratio_if_same_area or Decimal("0"),
                item.crop_id,
            ),
        )
    )
