"""Canonical planning-area limits shared by preview and persistence."""

from decimal import Decimal

from .periods import EngineInputError

MAX_PLANNING_AREA_HA = Decimal("99999999.9999")
MAX_PLANNING_AREA_DECIMAL_PLACES = 4


def validate_planning_area(value: Decimal, field_name: str) -> Decimal:
    if not value.is_finite() or value <= 0 or value > MAX_PLANNING_AREA_HA:
        raise ValueError(
            f"{field_name} must be a finite value greater than zero and no more than "
            f"{MAX_PLANNING_AREA_HA}."
        )
    if value.as_tuple().exponent < -MAX_PLANNING_AREA_DECIMAL_PLACES:
        raise ValueError(
            f"{field_name} can have up to {MAX_PLANNING_AREA_DECIMAL_PLACES} decimal places."
        )
    return value


def validate_engine_planning_area(value: Decimal) -> Decimal:
    try:
        return validate_planning_area(value, "proposed_area_ha")
    except ValueError as error:
        raise EngineInputError("INVALID_AREA", str(error)) from None
