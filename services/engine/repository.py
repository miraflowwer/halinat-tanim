"""Small psycopg data-access layer for the risk service."""

import logging
import os
from collections.abc import Callable
from datetime import date
from decimal import Decimal
from typing import Any, Protocol

import psycopg

from .models import CropRecord, GeographyRecord, PlanRecord, ReferenceRecord

logger = logging.getLogger(__name__)


class RepositoryError(RuntimeError):
    """A safe repository failure that must not expose SQL or credentials."""


class DatasetNotReadyError(RepositoryError):
    """The configured dataset is not registered in PostgreSQL."""


class RiskDataRepository(Protocol):
    def dataset_is_ready(self, dataset_version: str) -> bool: ...

    def get_crop(self, crop_id: str) -> CropRecord | None: ...

    def get_geography(self, geography_id: str) -> GeographyRecord | None: ...

    def get_plans(
        self,
        crop_id: str,
        geography_id: str,
        geography_database_id: int,
        period_start: date,
        period_end: date,
    ) -> list[PlanRecord]: ...

    def get_reference(
        self,
        crop_id: str,
        geography_database_id: int,
        period_start: date,
        period_end: date,
        dataset_version: str,
    ) -> ReferenceRecord | None: ...


class PostgresRiskRepository:
    """Read only the rows needed by one risk-check request."""

    def __init__(
        self,
        database_url: str,
        *,
        connection_factory: Callable[..., Any] | None = None,
    ):
        self.database_url = database_url.strip()
        self.connection_factory = connection_factory or psycopg.connect

    @classmethod
    def from_environment(cls) -> "PostgresRiskRepository":
        return cls(os.getenv("DATABASE_URL", ""))

    def _run(self, operation: Callable[[Any], Any]) -> Any:
        if not self.database_url:
            raise RepositoryError("PostgreSQL is not configured.")
        try:
            with self.connection_factory(self.database_url, connect_timeout=5) as connection:
                return operation(connection)
        except (psycopg.Error, ValueError) as error:
            logger.warning("Risk repository operation failed (%s).", type(error).__name__)
            raise RepositoryError(
                "PostgreSQL is not reachable or the database is not ready."
            ) from None

    def dataset_is_ready(self, dataset_version: str) -> bool:
        def operation(connection: Any) -> bool:
            row = connection.execute(
                """
                SELECT 1
                FROM dataset_metadata
                WHERE dataset_version = %s AND data_kind = 'synthetic_demo'
                LIMIT 1
                """,
                (dataset_version,),
            ).fetchone()
            return row is not None

        return self._run(operation)

    def get_crop(self, crop_id: str) -> CropRecord | None:
        def operation(connection: Any) -> CropRecord | None:
            row = connection.execute(
                """
                SELECT crop_id, canonical_name_en
                FROM crops
                WHERE crop_id = %s AND active = TRUE
                """,
                (crop_id,),
            ).fetchone()
            return CropRecord(crop_id=row[0], canonical_name_en=row[1]) if row else None

        return self._run(operation)

    def get_geography(self, geography_id: str) -> GeographyRecord | None:
        def operation(connection: Any) -> GeographyRecord | None:
            row = connection.execute(
                """
                SELECT id, geography_id, name
                FROM geographies
                WHERE geography_id = %s
                  AND level = 'municipality_city'
                  AND country = 'Philippines'
                  AND island_group = 'Luzon'
                  AND active = TRUE
                """,
                (geography_id,),
            ).fetchone()
            return (
                GeographyRecord(
                    geography_id=row[1],
                    database_id=row[0],
                    name=row[2],
                )
                if row
                else None
            )

        return self._run(operation)

    def get_plans(
        self,
        crop_id: str,
        geography_id: str,
        geography_database_id: int,
        period_start: date,
        period_end: date,
    ) -> list[PlanRecord]:
        def operation(connection: Any) -> list[PlanRecord]:
            rows = connection.execute(
                """
                SELECT crop_id, area_ha, harvest_start, harvest_end, status
                FROM planting_plans
                WHERE status = 'active'
                  AND crop_id = %s
                  AND geography_id = %s
                  AND harvest_start <= %s
                  AND harvest_end >= %s
                ORDER BY id
                """,
                (crop_id, geography_database_id, period_end, period_start),
            ).fetchall()
            return [
                PlanRecord(
                    crop_id=row[0],
                    geography_id=geography_id,
                    area_ha=Decimal(str(row[1])),
                    harvest_start=row[2],
                    harvest_end=row[3],
                    status=row[4],
                )
                for row in rows
            ]

        return self._run(operation)

    def get_reference(
        self,
        crop_id: str,
        geography_database_id: int,
        period_start: date,
        period_end: date,
        dataset_version: str,
    ) -> ReferenceRecord | None:
        def operation(connection: Any) -> ReferenceRecord | None:
            rows = connection.execute(
                """
                SELECT reference_area_ha, period_kind, dataset_version
                FROM crop_references
                WHERE crop_id = %s
                  AND geography_id = %s
                  AND period_start = %s
                  AND period_end = %s
                  AND period_kind = 'future_planning'
                  AND dataset_version = %s
                ORDER BY id
                """,
                (
                    crop_id,
                    geography_database_id,
                    period_start,
                    period_end,
                    dataset_version,
                ),
            ).fetchall()
            if len(rows) > 1:
                raise RepositoryError("Reference data is not unique for this planning period.")
            if not rows:
                return None
            return ReferenceRecord(
                reference_area_ha=Decimal(str(rows[0][0])),
                period_kind=rows[0][1],
                dataset_version=rows[0][2],
            )

        return self._run(operation)
