"""Application-free orchestration for one explainable risk check."""

from decimal import Decimal

from .aggregation import aggregate_relevant_plans
from .comparisons import calculate_comparison, sort_comparisons
from .config import EngineConfig
from .explanations import build_available_explanation, build_unavailable_explanation
from .models import ComparisonResult, RiskCheckInput, RiskCheckResult
from .periods import EngineInputError, resolve_supported_period
from .repository import DatasetNotReadyError, RiskDataRepository
from .risk import calculate_projected_area, calculate_risk

MAX_COMPARISON_CROPS = 5


def _usable_reference(reference_area_ha: Decimal | None) -> bool:
    return reference_area_ha is not None and reference_area_ha.is_finite() and reference_area_ha > 0


class RiskService:
    """Coordinate repository reads without putting SQL into formula functions."""

    def __init__(self, repository: RiskDataRepository, config: EngineConfig):
        self.repository = repository
        self.config = config

    def check(self, request: RiskCheckInput) -> RiskCheckResult:
        proposed_area = self._validate_request(request)
        requested_start, requested_end, period = resolve_supported_period(
            request.harvest_start,
            request.harvest_end,
            self.config,
        )

        if not self.repository.dataset_is_ready(self.config.dataset_version):
            raise DatasetNotReadyError(
                f"Configured dataset {self.config.dataset_version} is not seeded."
            )

        crop = self.repository.get_crop(request.crop_id)
        if crop is None:
            raise EngineInputError(
                "UNSUPPORTED_CROP",
                "The requested crop is not active or supported.",
            )

        geography = self.repository.get_geography(request.geography_id)
        if geography is None:
            raise EngineInputError(
                "UNSUPPORTED_GEOGRAPHY",
                "The requested geography is not an active supported municipality or city.",
            )

        primary_plans = self.repository.get_plans(
            request.crop_id,
            geography.geography_id,
            geography.database_id,
            period.start,
            period.end,
        )
        primary_aggregate = aggregate_relevant_plans(
            primary_plans,
            crop_id=request.crop_id,
            geography_id=geography.geography_id,
            period_start=period.start,
            period_end=period.end,
        )
        reference = self.repository.get_reference(
            request.crop_id,
            geography.database_id,
            period.start,
            period.end,
            self.config.dataset_version,
        )
        reference_area = reference.reference_area_ha if reference else None
        projected_area = calculate_projected_area(
            primary_aggregate.existing_planned_area_ha,
            proposed_area,
        )

        if _usable_reference(reference_area):
            calculation = calculate_risk(
                primary_aggregate.existing_planned_area_ha,
                proposed_area,
                reference_area,
                self.config.thresholds,
            )
            explanation = build_available_explanation(
                crop_name=crop.canonical_name_en,
                existing_planned_area_ha=primary_aggregate.existing_planned_area_ha,
                proposed_area_ha=proposed_area,
                projected_planned_area_ha=calculation.projected_planned_area_ha,
                reference_area_ha=reference_area,
                ratio=calculation.ratio,
                risk=calculation.risk,
            )
            status = "available"
            ratio = calculation.ratio
            risk = calculation.risk
            projected_area = calculation.projected_planned_area_ha
        else:
            explanation = build_unavailable_explanation(
                crop_name=crop.canonical_name_en,
                existing_planned_area_ha=primary_aggregate.existing_planned_area_ha,
                proposed_area_ha=proposed_area,
                projected_planned_area_ha=projected_area,
            )
            status = "unavailable"
            ratio = None
            risk = None

        comparisons = self._comparisons(
            request,
            geography.geography_id,
            geography.database_id,
            period.start,
            period.end,
            proposed_area,
        )
        return RiskCheckResult(
            status=status,
            crop_id=request.crop_id,
            geography_id=request.geography_id,
            requested_harvest_start=requested_start,
            requested_harvest_end=requested_end,
            planning_period_start=period.start,
            planning_period_end=period.end,
            existing_planned_area_ha=primary_aggregate.existing_planned_area_ha,
            proposed_area_ha=proposed_area,
            projected_planned_area_ha=projected_area,
            reference_area_ha=reference_area if _usable_reference(reference_area) else None,
            ratio=ratio,
            risk=risk,
            contributing_plan_count=primary_aggregate.contributing_plan_count,
            assumption_version=self.config.assumption_version,
            dataset_version=self.config.dataset_version,
            explanation=explanation,
            comparisons=sort_comparisons(comparisons),
        )

    @staticmethod
    def _validate_request(request: RiskCheckInput) -> Decimal:
        try:
            proposed = Decimal(str(request.proposed_area_ha))
        except (TypeError, ValueError):
            raise EngineInputError(
                "INVALID_AREA",
                "proposed_area_ha must be a finite number greater than zero.",
            ) from None
        if not proposed.is_finite() or proposed <= 0:
            raise EngineInputError(
                "INVALID_AREA",
                "proposed_area_ha must be a finite number greater than zero.",
            )
        comparisons = request.comparison_crop_ids
        if len(comparisons) > MAX_COMPARISON_CROPS:
            raise EngineInputError(
                "COMPARISON_LIMIT_EXCEEDED",
                f"comparison_crop_ids cannot contain more than {MAX_COMPARISON_CROPS} crops.",
            )
        if len(set(comparisons)) != len(comparisons):
            raise EngineInputError(
                "DUPLICATE_COMPARISON_CROP_IDS",
                "comparison_crop_ids cannot contain duplicate crop IDs.",
            )
        if request.crop_id in comparisons:
            raise EngineInputError(
                "PRIMARY_CROP_IN_COMPARISONS",
                "The primary crop cannot also be a comparison crop.",
            )
        return proposed

    def _comparisons(
        self,
        request: RiskCheckInput,
        geography_id: str,
        geography_database_id: int,
        period_start,
        period_end,
        proposed_area: Decimal,
    ) -> list[ComparisonResult]:
        result: list[ComparisonResult] = []
        for crop_id in request.comparison_crop_ids:
            crop = self.repository.get_crop(crop_id)
            if crop is None:
                raise EngineInputError(
                    "UNSUPPORTED_CROP",
                    f"Comparison crop {crop_id!r} is not active or supported.",
                )
            plans = self.repository.get_plans(
                crop_id,
                geography_id,
                geography_database_id,
                period_start,
                period_end,
            )
            aggregate = aggregate_relevant_plans(
                plans,
                crop_id=crop_id,
                geography_id=geography_id,
                period_start=period_start,
                period_end=period_end,
            )
            reference = self.repository.get_reference(
                crop_id,
                geography_database_id,
                period_start,
                period_end,
                self.config.dataset_version,
            )
            reference_area = reference.reference_area_ha if reference else None
            result.append(
                calculate_comparison(
                    crop_id,
                    aggregate.existing_planned_area_ha,
                    reference_area if _usable_reference(reference_area) else None,
                    proposed_area,
                    self.config.thresholds,
                )
            )
        return result
