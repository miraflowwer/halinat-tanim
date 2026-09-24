"""Isolated first-time demo data backed by the canonical seeded fixture."""

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Protocol

import psycopg

from services.engine.comparisons import calculate_comparison
from services.engine.config import EngineConfig
from services.engine.explanations import build_available_explanation
from services.engine.risk import calculate_risk

logger = logging.getLogger(__name__)

PRIMARY_SCENARIO_ID = "tomato_cabanatuan_2027_q1"
COMPARISON_SCENARIO_ID = "eggplant_cabanatuan_lower_pressure_2027_q1"


class DemoNotReadyError(RuntimeError):
    """The configured canonical demo fixture is not available."""


@dataclass(frozen=True)
class DemoScenarioRecord:
    scenario_id: str
    crop_id: str
    crop_name_en: str
    crop_name_tl: str | None
    geography_id: str
    geography_name: str
    period_start: date
    period_end: date
    existing_planned_area_ha: Decimal
    proposed_future_plan_area_ha: Decimal
    reference_area_ha: Decimal
    data_kind: str
    dataset_version: str


class DemoRepository(Protocol):
    def get_scenarios(self, dataset_version: str) -> list[DemoScenarioRecord]: ...


class PostgresDemoRepository:
    def __init__(
        self,
        database_url: str,
        *,
        connection_factory: Callable[..., Any] | None = None,
    ):
        self.database_url = database_url.strip()
        self.connection_factory = connection_factory or psycopg.connect

    @classmethod
    def from_environment(cls) -> "PostgresDemoRepository":
        return cls(os.getenv("DATABASE_URL", ""))

    def get_scenarios(self, dataset_version: str) -> list[DemoScenarioRecord]:
        if not self.database_url:
            raise DemoNotReadyError("PostgreSQL is not configured.")
        try:
            with self.connection_factory(self.database_url, connect_timeout=5) as connection:
                rows = connection.execute(
                    """
                    SELECT ds.scenario_id, ds.crop_id, c.canonical_name_en, c.canonical_name_tl,
                           g.geography_id, g.name, ds.period_start, ds.period_end,
                           ds.existing_planned_area_ha, ds.proposed_future_plan_area_ha,
                           ds.reference_area_ha, ds.data_kind, ds.dataset_version
                    FROM demo_scenarios AS ds
                    JOIN crops AS c ON c.crop_id = ds.crop_id
                    JOIN geographies AS g ON g.id = ds.geography_id
                    WHERE ds.dataset_version = %s
                      AND ds.data_kind = 'synthetic_demo'
                    ORDER BY ds.scenario_id
                    """,
                    (dataset_version,),
                ).fetchall()
            return [
                DemoScenarioRecord(
                    scenario_id=row[0],
                    crop_id=row[1],
                    crop_name_en=row[2],
                    crop_name_tl=row[3],
                    geography_id=row[4],
                    geography_name=row[5],
                    period_start=row[6],
                    period_end=row[7],
                    existing_planned_area_ha=Decimal(str(row[8])),
                    proposed_future_plan_area_ha=Decimal(str(row[9])),
                    reference_area_ha=Decimal(str(row[10])),
                    data_kind=row[11],
                    dataset_version=row[12],
                )
                for row in rows
            ]
        except (psycopg.Error, ValueError) as error:
            logger.warning("Demo repository operation failed (%s).", type(error).__name__)
            raise DemoNotReadyError("The canonical demo dataset is not ready.") from None


@dataclass(frozen=True)
class DemoScenarioResult:
    primary: DemoScenarioRecord
    projected_area_ha: Decimal
    ratio: Decimal
    risk: str
    explanation: str
    comparison: DemoScenarioRecord
    comparison_current_ratio: Decimal
    comparison_current_risk: str
    comparison_projected_ratio: Decimal
    comparison_projected_risk: str


class DemoService:
    def __init__(self, repository: DemoRepository, config: EngineConfig):
        self.repository = repository
        self.config = config

    def get_scenario(self) -> DemoScenarioResult:
        records = {
            record.scenario_id: record
            for record in self.repository.get_scenarios(self.config.dataset_version)
        }
        primary = records.get(PRIMARY_SCENARIO_ID)
        comparison = records.get(COMPARISON_SCENARIO_ID)
        if primary is None or comparison is None:
            raise DemoNotReadyError(
                "The configured dataset does not contain the canonical Tomato and Eggplant "
                "demo scenarios."
            )
        calculation = calculate_risk(
            primary.existing_planned_area_ha,
            primary.proposed_future_plan_area_ha,
            primary.reference_area_ha,
            self.config.thresholds,
        )
        comparison_result = calculate_comparison(
            comparison.crop_id,
            comparison.existing_planned_area_ha,
            comparison.reference_area_ha,
            primary.proposed_future_plan_area_ha,
            self.config.thresholds,
        )
        if (
            comparison_result.current_ratio is None
            or comparison_result.current_risk is None
            or comparison_result.projected_ratio_if_same_area is None
            or comparison_result.projected_risk_if_same_area is None
        ):
            raise DemoNotReadyError(
                "The canonical comparison scenario has no usable reference value."
            )
        return DemoScenarioResult(
            primary=primary,
            projected_area_ha=calculation.projected_planned_area_ha,
            ratio=calculation.ratio,
            risk=calculation.risk,
            explanation=build_available_explanation(
                crop_name=primary.crop_name_en,
                existing_planned_area_ha=primary.existing_planned_area_ha,
                proposed_area_ha=primary.proposed_future_plan_area_ha,
                projected_planned_area_ha=calculation.projected_planned_area_ha,
                reference_area_ha=primary.reference_area_ha,
                ratio=calculation.ratio,
                risk=calculation.risk,
            ),
            comparison=comparison,
            comparison_current_ratio=comparison_result.current_ratio,
            comparison_current_risk=comparison_result.current_risk,
            comparison_projected_ratio=comparison_result.projected_ratio_if_same_area,
            comparison_projected_risk=comparison_result.projected_risk_if_same_area,
        )
