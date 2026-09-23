"""Pure Decimal calculations for the explainable Glut Risk result."""

from dataclasses import dataclass
from decimal import Decimal

from .config import ENGINE_THRESHOLDS, RiskThresholds
from .models import RiskLevel


def _decimal(value: Decimal | int | str, field_name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as error:
        raise ValueError(f"{field_name} must be a valid decimal number") from error
    if not result.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return result


def calculate_projected_area(
    existing_planned_area_ha: Decimal | int | str,
    proposed_area_ha: Decimal | int | str,
) -> Decimal:
    existing = _decimal(existing_planned_area_ha, "existing_planned_area_ha")
    proposed = _decimal(proposed_area_ha, "proposed_area_ha")
    if existing < 0:
        raise ValueError("existing_planned_area_ha cannot be negative")
    if proposed < 0:
        raise ValueError("proposed_area_ha cannot be negative")
    return existing + proposed


def calculate_ratio(
    projected_planned_area_ha: Decimal | int | str,
    reference_area_ha: Decimal | int | str,
) -> Decimal:
    projected = _decimal(projected_planned_area_ha, "projected_planned_area_ha")
    reference = _decimal(reference_area_ha, "reference_area_ha")
    if projected < 0:
        raise ValueError("projected_planned_area_ha cannot be negative")
    if reference <= 0:
        raise ValueError("reference_area_ha must be greater than zero")
    return projected / reference


def classify_risk(
    ratio: Decimal | int | str,
    thresholds: RiskThresholds = ENGINE_THRESHOLDS,
) -> RiskLevel:
    value = _decimal(ratio, "ratio")
    if value < 0:
        raise ValueError("ratio cannot be negative")
    if thresholds.low_below >= thresholds.high_above:
        raise ValueError("risk thresholds must be ordered")
    if value < thresholds.low_below:
        return "low"
    if value <= thresholds.high_above:
        return "moderate"
    return "high"


@dataclass(frozen=True)
class RiskCalculation:
    projected_planned_area_ha: Decimal
    ratio: Decimal
    risk: RiskLevel


def calculate_risk(
    existing_planned_area_ha: Decimal | int | str,
    proposed_area_ha: Decimal | int | str,
    reference_area_ha: Decimal | int | str,
    thresholds: RiskThresholds = ENGINE_THRESHOLDS,
) -> RiskCalculation:
    projected = calculate_projected_area(existing_planned_area_ha, proposed_area_ha)
    ratio = calculate_ratio(projected, reference_area_ha)
    return RiskCalculation(
        projected_planned_area_ha=projected,
        ratio=ratio,
        risk=classify_risk(ratio, thresholds),
    )
