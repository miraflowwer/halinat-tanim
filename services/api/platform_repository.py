"""PostgreSQL access for planting plans, lookups, and cooperative totals."""

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

import psycopg

logger = logging.getLogger(__name__)


class PlatformRepositoryError(RuntimeError):
    """A safe failure from the platform data store."""


class OrganizationMembershipRequired(PlatformRepositoryError):
    """A Cooperative account is missing its organization link."""


@dataclass(frozen=True)
class PlanRecord:
    plan_id: int
    crop_id: str
    crop_name_en: str
    crop_name_tl: str | None
    geography_id: str
    geography_name: str
    area_ha: Decimal
    planting_date: date
    harvest_start: date
    harvest_end: date
    status: str


@dataclass(frozen=True)
class CooperativePlanRecord:
    crop_id: str
    crop_name_en: str
    crop_name_tl: str | None
    geography_id: str
    geography_name: str
    area_ha: Decimal
    harvest_start: date
    harvest_end: date


@dataclass(frozen=True)
class OrganizationRecord:
    organization_id: int
    name: str


_PLAN_SELECT = """
    SELECT pp.id, pp.crop_id, c.canonical_name_en, c.canonical_name_tl,
           g.geography_id,
           concat_ws(', ', g.name, province.name, region.name),
           pp.area_ha, pp.planting_date, pp.harvest_start, pp.harvest_end, pp.status
    FROM planting_plans AS pp
    JOIN crops AS c ON c.crop_id = pp.crop_id
    JOIN geographies AS g ON g.id = pp.geography_id
    LEFT JOIN geographies AS province ON province.id = g.parent_id
    LEFT JOIN geographies AS region ON region.id = province.parent_id
"""


def _plan_from_row(row: tuple[Any, ...]) -> PlanRecord:
    return PlanRecord(
        plan_id=row[0],
        crop_id=row[1],
        crop_name_en=row[2],
        crop_name_tl=row[3],
        geography_id=row[4],
        geography_name=row[5],
        area_ha=Decimal(str(row[6])),
        planting_date=row[7],
        harvest_start=row[8],
        harvest_end=row[9],
        status=row[10],
    )


class PostgresPlatformRepository:
    """Keep platform SQL and user ownership filters in one small adapter."""

    def __init__(
        self,
        database_url: str,
        *,
        connection_factory: Callable[..., Any] | None = None,
    ):
        self.database_url = database_url.strip()
        self.connection_factory = connection_factory or psycopg.connect

    @classmethod
    def from_environment(cls) -> "PostgresPlatformRepository":
        return cls(os.getenv("DATABASE_URL", ""))

    def _run(self, operation: Callable[[Any], Any]) -> Any:
        if not self.database_url:
            raise PlatformRepositoryError("PostgreSQL is not configured.")
        try:
            with self.connection_factory(self.database_url, connect_timeout=5) as connection:
                with connection:
                    return operation(connection)
        except PlatformRepositoryError:
            raise
        except (psycopg.Error, ValueError) as error:
            logger.warning("Platform repository operation failed (%s).", type(error).__name__)
            raise PlatformRepositoryError(
                "PostgreSQL is not reachable or the platform data is not ready."
            ) from None

    def list_crops(self) -> list[dict[str, Any]]:
        return self._run(
            lambda connection: [
                {
                    "crop_id": row[0],
                    "canonical_name_en": row[1],
                    "canonical_name_tl": row[2],
                    "scientific_name": row[3],
                    "category": row[4],
                }
                for row in connection.execute(
                    """
                    SELECT crop_id, canonical_name_en, canonical_name_tl,
                           scientific_name, category
                    FROM crops
                    WHERE active = TRUE
                    ORDER BY canonical_name_en, crop_id
                    """
                ).fetchall()
            ]
        )

    def list_geographies(self) -> list[dict[str, Any]]:
        return self._run(
            lambda connection: [
                {
                    "geography_id": row[0],
                    "name": row[1],
                    "level": row[2],
                    "parent_geography_id": row[3],
                }
                for row in connection.execute(
                    """
                    SELECT child.geography_id, child.name, child.level, parent.geography_id
                    FROM geographies AS child
                    LEFT JOIN geographies AS parent ON parent.id = child.parent_id
                    WHERE child.active = TRUE
                      AND child.country = 'Philippines'
                      AND child.island_group = 'Luzon'
                      AND child.level IN ('region', 'province', 'municipality_city')
                    ORDER BY
                      CASE child.level
                        WHEN 'region' THEN 1
                        WHEN 'province' THEN 2
                        ELSE 3
                      END,
                      child.name
                    """
                ).fetchall()
            ]
        )

    def is_active_crop(self, crop_id: str) -> bool:
        return self._run(
            lambda connection: connection.execute(
                "SELECT 1 FROM crops WHERE crop_id = %s AND active = TRUE",
                (crop_id,),
            ).fetchone()
            is not None
        )

    def is_supported_geography(self, geography_id: str) -> bool:
        return self._run(
            lambda connection: connection.execute(
                """
                SELECT 1 FROM geographies
                WHERE geography_id = %s
                  AND level = 'municipality_city'
                  AND country = 'Philippines'
                  AND island_group = 'Luzon'
                  AND active = TRUE
                """,
                (geography_id,),
            ).fetchone()
            is not None
        )

    def list_plans(self, user_id: int) -> list[PlanRecord]:
        return self._run(
            lambda connection: [
                _plan_from_row(row)
                for row in connection.execute(
                    _PLAN_SELECT
                    + " WHERE pp.user_id = %s ORDER BY pp.harvest_start, pp.id DESC",
                    (user_id,),
                ).fetchall()
            ]
        )

    def get_plan(self, user_id: int, plan_id: int) -> PlanRecord | None:
        row = self._run(
            lambda connection: connection.execute(
                _PLAN_SELECT + " WHERE pp.user_id = %s AND pp.id = %s",
                (user_id, plan_id),
            ).fetchone()
        )
        return _plan_from_row(row) if row else None

    def create_plan(
        self,
        *,
        user_id: int,
        role: str,
        crop_id: str,
        geography_id: str,
        area_ha: Decimal,
        planting_date: date,
        harvest_start: date,
        harvest_end: date,
    ) -> PlanRecord:
        def operation(connection: Any) -> PlanRecord:
            crop = connection.execute(
                "SELECT 1 FROM crops WHERE crop_id = %s AND active = TRUE",
                (crop_id,),
            ).fetchone()
            if crop is None:
                raise PlatformRepositoryError("The selected crop is no longer supported.")

            geography = connection.execute(
                """
                SELECT id FROM geographies
                WHERE geography_id = %s
                  AND level = 'municipality_city'
                  AND country = 'Philippines'
                  AND island_group = 'Luzon'
                  AND active = TRUE
                """,
                (geography_id,),
            ).fetchone()
            if geography is None:
                raise PlatformRepositoryError("The selected location is no longer supported.")

            organization_id = None
            if role == "cooperative":
                membership = connection.execute(
                    """
                    SELECT organization_id
                    FROM organization_members
                    WHERE user_id = %s
                    ORDER BY created_at, organization_id
                    LIMIT 1
                    """,
                    (user_id,),
                ).fetchone()
                if membership is None:
                    raise OrganizationMembershipRequired(
                        "This Cooperative account has no organization membership."
                    )
                organization_id = membership[0]

            inserted = connection.execute(
                """
                INSERT INTO planting_plans (
                    user_id, organization_id, crop_id, geography_id, area_ha,
                    planting_date, harvest_start, harvest_end, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active')
                RETURNING id
                """,
                (
                    user_id,
                    organization_id,
                    crop_id,
                    geography[0],
                    area_ha,
                    planting_date,
                    harvest_start,
                    harvest_end,
                ),
            ).fetchone()
            row = connection.execute(
                _PLAN_SELECT + " WHERE pp.user_id = %s AND pp.id = %s",
                (user_id, inserted[0]),
            ).fetchone()
            if row is None:
                raise PlatformRepositoryError("The plan could not be loaded after saving.")
            return _plan_from_row(row)

        return self._run(operation)

    def update_plan(
        self,
        *,
        user_id: int,
        plan_id: int,
        crop_id: str,
        geography_id: str,
        area_ha: Decimal,
        planting_date: date,
        harvest_start: date,
        harvest_end: date,
    ) -> PlanRecord | None:
        def operation(connection: Any) -> PlanRecord | None:
            crop = connection.execute(
                "SELECT 1 FROM crops WHERE crop_id = %s AND active = TRUE",
                (crop_id,),
            ).fetchone()
            if crop is None:
                raise PlatformRepositoryError("The selected crop is no longer supported.")

            geography = connection.execute(
                """
                SELECT id FROM geographies
                WHERE geography_id = %s
                  AND level = 'municipality_city'
                  AND country = 'Philippines'
                  AND island_group = 'Luzon'
                  AND active = TRUE
                """,
                (geography_id,),
            ).fetchone()
            if geography is None:
                raise PlatformRepositoryError("The selected location is no longer supported.")

            changed = connection.execute(
                """
                UPDATE planting_plans
                SET crop_id = %s, geography_id = %s, area_ha = %s,
                    planting_date = %s, harvest_start = %s, harvest_end = %s,
                    updated_at = NOW()
                WHERE id = %s AND user_id = %s AND status = 'active'
                RETURNING id
                """,
                (
                    crop_id,
                    geography[0],
                    area_ha,
                    planting_date,
                    harvest_start,
                    harvest_end,
                    plan_id,
                    user_id,
                ),
            ).fetchone()
            if changed is None:
                return None
            row = connection.execute(
                _PLAN_SELECT + " WHERE pp.user_id = %s AND pp.id = %s",
                (user_id, plan_id),
            ).fetchone()
            return _plan_from_row(row) if row else None

        return self._run(operation)

    def cancel_plan(self, user_id: int, plan_id: int) -> PlanRecord | None:
        def operation(connection: Any) -> PlanRecord | None:
            connection.execute(
                """
                UPDATE planting_plans
                SET status = 'cancelled', updated_at = NOW()
                WHERE id = %s AND user_id = %s AND status = 'active'
                """,
                (plan_id, user_id),
            )
            row = connection.execute(
                _PLAN_SELECT + " WHERE pp.user_id = %s AND pp.id = %s",
                (user_id, plan_id),
            ).fetchone()
            return _plan_from_row(row) if row else None

        return self._run(operation)

    def cooperative_plans(
        self, user_id: int
    ) -> tuple[OrganizationRecord, list[CooperativePlanRecord]] | None:
        def operation(
            connection: Any,
        ) -> tuple[OrganizationRecord, list[CooperativePlanRecord]] | None:
            membership = connection.execute(
                """
                SELECT o.id, o.name
                FROM organization_members AS om
                JOIN organizations AS o ON o.id = om.organization_id
                WHERE om.user_id = %s
                ORDER BY om.created_at, o.id
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            if membership is None:
                return None

            rows = connection.execute(
                """
                SELECT pp.crop_id, c.canonical_name_en, c.canonical_name_tl,
                       g.geography_id,
                       concat_ws(', ', g.name, province.name, region.name),
                       pp.area_ha, pp.harvest_start, pp.harvest_end
                FROM planting_plans AS pp
                JOIN crops AS c ON c.crop_id = pp.crop_id
                JOIN geographies AS g ON g.id = pp.geography_id
                LEFT JOIN geographies AS province ON province.id = g.parent_id
                LEFT JOIN geographies AS region ON region.id = province.parent_id
                WHERE pp.organization_id = %s AND pp.status = 'active'
                ORDER BY c.canonical_name_en, pp.harvest_start, g.name
                """,
                (membership[0],),
            ).fetchall()
            plans = [
                CooperativePlanRecord(
                    crop_id=row[0],
                    crop_name_en=row[1],
                    crop_name_tl=row[2],
                    geography_id=row[3],
                    geography_name=row[4],
                    area_ha=Decimal(str(row[5])),
                    harvest_start=row[6],
                    harvest_end=row[7],
                )
                for row in rows
            ]
            return OrganizationRecord(membership[0], membership[1]), plans

        return self._run(operation)

    def has_organization_membership(self, user_id: int) -> bool:
        return self._run(
            lambda connection: connection.execute(
                "SELECT 1 FROM organization_members WHERE user_id = %s LIMIT 1",
                (user_id,),
            ).fetchone()
            is not None
        )
