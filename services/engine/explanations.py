"""Deterministic, value-based explanation templates."""

from decimal import ROUND_HALF_UP, Decimal

from .models import RiskLevel


def _area_text(value: Decimal) -> str:
    normalized = value.normalize()
    return format(normalized, "f")


def _ratio_text(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return format(rounded, "f")


def build_available_explanation(
    *,
    crop_name: str,
    existing_planned_area_ha: Decimal,
    proposed_area_ha: Decimal,
    projected_planned_area_ha: Decimal,
    reference_area_ha: Decimal,
    ratio: Decimal,
    risk: RiskLevel,
) -> str:
    risk_label = risk.capitalize()
    return (
        f"Registered {crop_name} plans for this planning period total "
        f"{_area_text(existing_planned_area_ha)} ha. Adding "
        f"{_area_text(proposed_area_ha)} ha gives "
        f"{_area_text(projected_planned_area_ha)} ha against a "
        f"{_area_text(reference_area_ha)} ha reference. The supply pressure ratio is "
        f"{_ratio_text(ratio)}, which is {risk_label} under the current TANIM "
        "prototype thresholds."
    )


def build_unavailable_explanation(
    *,
    crop_name: str,
    existing_planned_area_ha: Decimal,
    proposed_area_ha: Decimal,
    projected_planned_area_ha: Decimal,
) -> str:
    return (
        f"Registered {crop_name} plans for this planning period total "
        f"{_area_text(existing_planned_area_ha)} ha. Adding "
        f"{_area_text(proposed_area_ha)} ha gives "
        f"{_area_text(projected_planned_area_ha)} ha, but no usable reference area "
        "is available for this planning period. TANIM cannot calculate a supply "
        "pressure ratio or risk level."
    )
