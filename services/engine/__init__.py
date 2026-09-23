"""Pure and database-backed TANIM risk engine components."""

from .aggregation import aggregate_relevant_plans
from .config import ENGINE_ASSUMPTION_VERSION, ENGINE_THRESHOLDS, EngineConfig
from .periods import EngineInputError, resolve_supported_period
from .risk import calculate_projected_area, calculate_ratio, calculate_risk, classify_risk

__all__ = [
    "ENGINE_ASSUMPTION_VERSION",
    "ENGINE_THRESHOLDS",
    "EngineConfig",
    "EngineInputError",
    "aggregate_relevant_plans",
    "calculate_projected_area",
    "calculate_ratio",
    "calculate_risk",
    "classify_risk",
    "resolve_supported_period",
]
