import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from services.engine.aggregation import aggregate_relevant_plans
from services.engine.comparisons import calculate_comparison, sort_comparisons
from services.engine.config import load_engine_config
from services.engine.explanations import build_available_explanation
from services.engine.models import (
    CropRecord,
    GeographyRecord,
    PlanRecord,
    ReferenceRecord,
)
from services.engine.periods import EngineInputError, resolve_supported_period
from services.engine.risk import (
    calculate_projected_area,
    calculate_ratio,
    calculate_risk,
    classify_risk,
)
from services.engine.service import RiskService

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_tomato_fixture_calculates_high_risk():
    fixture = json.loads((ROOT / "data/seeds/demo_scenarios.json").read_text(encoding="utf-8"))
    scenario = next(item for item in fixture["scenarios"] if item["crop_id"] == "tomato")

    result = calculate_risk(
        Decimal(str(scenario["existing_planned_area_ha"])),
        Decimal(str(scenario["proposed_future_plan_area_ha"])),
        Decimal(str(scenario["reference_area_ha"])),
    )

    assert result.projected_planned_area_ha == Decimal("40")
    assert result.ratio == Decimal("1.6")
    assert result.risk == "high"


def test_current_risk_context_uses_active_plans_without_a_proposed_area():
    class Repository:
        def dataset_is_ready(self, dataset_version):
            return True

        def get_crop(self, crop_id):
            return CropRecord(crop_id, "Tomato")

        def get_geography(self, geography_id):
            return GeographyRecord(geography_id, 1, "Cabanatuan City")

        def get_plans(self, *_args):
            return [
                PlanRecord(
                    "tomato",
                    "mun_0304903000",
                    Decimal("20"),
                    date(2027, 1, 1),
                    date(2027, 3, 31),
                    "active",
                ),
                PlanRecord(
                    "tomato",
                    "mun_0304903000",
                    Decimal("99"),
                    date(2027, 1, 1),
                    date(2027, 3, 31),
                    "cancelled",
                ),
            ]

        def get_reference(self, *_args):
            return ReferenceRecord(Decimal("25"), "future_planning", config.dataset_version)

    config = load_engine_config()
    context = RiskService(Repository(), config).current_context(
        crop_id="tomato",
        geography_id="mun_0304903000",
        harvest_start=date(2027, 1, 1),
        harvest_end=date(2027, 3, 31),
    )

    assert context.status == "available"
    assert context.planned_area_ha == Decimal("20")
    assert context.reference_area_ha == Decimal("25")
    assert context.ratio == Decimal("0.8")
    assert context.risk == "low"
    assert "20 ha" in context.explanation
    assert "25 ha reference" in context.explanation


def test_eggplant_fixture_calculates_lower_pressure_context():
    fixture = json.loads((ROOT / "data/seeds/demo_scenarios.json").read_text(encoding="utf-8"))
    scenario = next(item for item in fixture["scenarios"] if item["crop_id"] == "eggplant")

    result = calculate_risk(
        Decimal(str(scenario["existing_planned_area_ha"])),
        Decimal(str(scenario["proposed_future_plan_area_ha"])),
        Decimal(str(scenario["reference_area_ha"])),
    )

    assert result.ratio.quantize(Decimal("0.000001")) == Decimal("0.666667")
    assert result.risk == "low"


def test_risk_threshold_boundaries_are_exact():
    assert classify_risk(Decimal("0.899999")) == "low"
    assert classify_risk(Decimal("0.90")) == "moderate"
    assert classify_risk(Decimal("1.00")) == "moderate"
    assert classify_risk(Decimal("1.10")) == "moderate"
    assert classify_risk(Decimal("1.100001")) == "high"


def test_formula_rejects_zero_reference_without_dividing():
    assert calculate_projected_area(Decimal("32"), Decimal("8")) == Decimal("40")
    with pytest.raises(ValueError, match="cannot be negative"):
        calculate_projected_area(Decimal("-1"), Decimal("8"))
    with pytest.raises(ValueError, match="cannot be negative"):
        calculate_projected_area(Decimal("1"), Decimal("-8"))
    with pytest.raises(ValueError, match="greater than zero"):
        calculate_ratio(Decimal("40"), Decimal("0"))


def test_plan_aggregation_filters_status_crop_geography_and_overlap():
    plans = [
        PlanRecord(
            "tomato", "mun-a", Decimal("10"), date(2027, 1, 1), date(2027, 1, 31), "active"
        ),
        PlanRecord(
            "tomato", "mun-a", Decimal("22"), date(2027, 3, 31), date(2027, 4, 1), "active"
        ),
        PlanRecord(
            "tomato", "mun-a", Decimal("99"), date(2027, 1, 1), date(2027, 3, 31), "cancelled"
        ),
        PlanRecord(
            "tomato", "mun-a", Decimal("88"), date(2027, 1, 1), date(2027, 3, 31), "completed"
        ),
        PlanRecord(
            "eggplant", "mun-a", Decimal("77"), date(2027, 1, 1), date(2027, 3, 31), "active"
        ),
        PlanRecord(
            "tomato", "mun-b", Decimal("66"), date(2027, 1, 1), date(2027, 3, 31), "active"
        ),
        PlanRecord(
            "tomato", "mun-a", Decimal("55"), date(2027, 4, 1), date(2027, 5, 1), "active"
        ),
    ]

    result = aggregate_relevant_plans(
        plans,
        crop_id="tomato",
        geography_id="mun-a",
        period_start=date(2027, 1, 1),
        period_end=date(2027, 3, 31),
    )

    assert result.existing_planned_area_ha == Decimal("32")
    assert result.contributing_plan_count == 2


def test_period_resolution_normalizes_dates_inside_one_configured_quarter():
    config = load_engine_config()
    start, end, period = resolve_supported_period("2027-01-15", "2027-03-15", config)

    assert (start, end) == (date(2027, 1, 15), date(2027, 3, 15))
    assert (period.start, period.end) == (date(2027, 1, 1), date(2027, 3, 31))


@pytest.mark.parametrize(
    ("start", "end", "code"),
    [
        ("2027-03-20", "2027-04-10", "HARVEST_PERIOD_SPANS_MULTIPLE_PERIODS"),
        ("2029-01-01", "2029-03-31", "UNSUPPORTED_HARVEST_PERIOD"),
        ("not-a-date", "2027-03-15", "INVALID_DATE"),
        ("2027-03-15", "2027-01-15", "INVALID_DATE_RANGE"),
    ],
)
def test_period_resolution_returns_stable_validation_codes(start, end, code):
    with pytest.raises(EngineInputError) as error:
        resolve_supported_period(start, end, load_engine_config())

    assert error.value.code == code


def test_comparison_calculates_current_and_same_area_projected_pressure():
    result = calculate_comparison(
        "eggplant",
        Decimal("12"),
        Decimal("18"),
        Decimal("8"),
    )

    assert result.current_ratio == Decimal("0.6666666666666666666666666667")
    assert result.current_risk == "low"
    assert result.projected_ratio_if_same_area == Decimal("1.111111111111111111111111111")
    assert result.projected_risk_if_same_area == "high"


def test_comparison_treats_zero_reference_as_unavailable():
    result = calculate_comparison("tomato", Decimal("12"), Decimal("0"), Decimal("8"))

    assert result.reference_area_ha is None
    assert result.current_ratio is None
    assert result.projected_risk_if_same_area is None


def test_comparisons_sort_by_projected_ratio_and_put_missing_references_last():
    low = calculate_comparison("low", Decimal("1"), Decimal("10"), Decimal("1"))
    missing = calculate_comparison("missing", Decimal("4"), None, Decimal("1"))
    high = calculate_comparison("high", Decimal("20"), Decimal("10"), Decimal("1"))

    assert [item.crop_id for item in sort_comparisons([missing, high, low])] == [
        "low",
        "high",
        "missing",
    ]


def test_explanation_is_deterministic_and_uses_calculated_values():
    result = calculate_risk(Decimal("32"), Decimal("8"), Decimal("25"))
    explanation = build_available_explanation(
        crop_name="Tomato",
        existing_planned_area_ha=Decimal("32"),
        proposed_area_ha=Decimal("8"),
        projected_planned_area_ha=result.projected_planned_area_ha,
        reference_area_ha=Decimal("25"),
        ratio=result.ratio,
        risk=result.risk,
    )

    assert explanation == (
        "Registered Tomato plans for this planning period total 32 ha. Adding 8 ha gives "
        "40 ha against a 25 ha reference. The supply pressure ratio is 1.60, which is "
        "High under the current TANIM prototype thresholds."
    )
