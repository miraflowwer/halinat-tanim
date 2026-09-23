"""Configuration for the explainable Glut Risk engine."""

import json
from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from .models import PlanningPeriod

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET_CONFIG = ROOT / "data" / "dataset_config.json"

# These are engine assumptions, not the thresholds used to label Phase 2 map
# snapshots. They currently have the same values by design, but the engine
# keeps its own named version so the two concepts can change independently.
ENGINE_ASSUMPTION_VERSION = "grci-v1"


@dataclass(frozen=True)
class RiskThresholds:
    low_below: Decimal
    high_above: Decimal


ENGINE_THRESHOLDS = RiskThresholds(
    low_below=Decimal("0.90"),
    high_above=Decimal("1.10"),
)


def _configured_quarter_periods(data: dict[str, Any]) -> list[tuple[str, str]]:
    future = data["periods"]["future_planning"]
    horizon_start = date.fromisoformat(future["start"])
    horizon_end = date.fromisoformat(future["end"])
    starts = [date.fromisoformat(value) for value in future["quarter_starts"]]
    periods = []
    for start in starts:
        end_month = start.month + 2
        end = date(start.year, end_month, monthrange(start.year, end_month)[1])
        if start < horizon_start or end > horizon_end:
            raise ValueError("future planning quarter is outside its configured horizon")
        periods.append((start.isoformat(), end.isoformat()))
    if periods != sorted(periods) or len(periods) != len(set(periods)):
        raise ValueError("future planning quarter starts must be unique and chronological")

    expected: list[tuple[str, str]] = []
    cursor = horizon_start
    while cursor <= horizon_end:
        end_month = cursor.month + 2
        end = date(cursor.year, end_month, monthrange(cursor.year, end_month)[1])
        expected.append((cursor.isoformat(), end.isoformat()))
        cursor = date(
            cursor.year + (1 if cursor.month == 10 else 0),
            (cursor.month + 3 - 1) % 12 + 1,
            1,
        )
    if periods != expected:
        raise ValueError("future planning quarters must cover the configured horizon")
    return periods


@dataclass(frozen=True)
class EngineConfig:
    assumption_version: str
    dataset_version: str
    future_periods: tuple[PlanningPeriod, ...]
    thresholds: RiskThresholds


def load_engine_config(config_path: Path = DEFAULT_DATASET_CONFIG) -> EngineConfig:
    """Load the configured dataset version and future planning horizon."""
    with config_path.open(encoding="utf-8") as file:
        data: dict[str, Any] = json.load(file)

    dataset_version = str(data["dataset_version"]).strip()
    if not dataset_version:
        raise ValueError("dataset_config.json must define a dataset_version")

    periods = tuple(
        PlanningPeriod(
            start=date.fromisoformat(start),
            end=date.fromisoformat(end),
        )
        for start, end in _configured_quarter_periods(data)
    )
    return EngineConfig(
        assumption_version=ENGINE_ASSUMPTION_VERSION,
        dataset_version=dataset_version,
        future_periods=periods,
        thresholds=ENGINE_THRESHOLDS,
    )
