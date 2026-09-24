import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from services.api.demo import DemoScenarioRecord, DemoService
from services.engine.config import load_engine_config

ROOT = Path(__file__).resolve().parents[1]


class FixtureDemoRepository:
    def __init__(self):
        fixture = json.loads((ROOT / "data/seeds/demo_scenarios.json").read_text(encoding="utf-8"))
        names = {"tomato": ("Tomato", "Kamatis"), "eggplant": ("Eggplant", "Talong")}
        self.records = []
        for row in fixture["scenarios"]:
            name_en, name_tl = names[row["crop_id"]]
            self.records.append(
                DemoScenarioRecord(
                    scenario_id=row["scenario_id"],
                    crop_id=row["crop_id"],
                    crop_name_en=name_en,
                    crop_name_tl=name_tl,
                    geography_id=row["geography_id"],
                    geography_name="Cabanatuan City",
                    period_start=date.fromisoformat(row["period_start"]),
                    period_end=date.fromisoformat(row["period_end"]),
                    existing_planned_area_ha=Decimal(str(row["existing_planned_area_ha"])),
                    proposed_future_plan_area_ha=Decimal(str(row["proposed_future_plan_area_ha"])),
                    reference_area_ha=Decimal(str(row["reference_area_ha"])),
                    data_kind=row["data_kind"],
                    dataset_version="demo-2026-09-v4",
                )
            )

    def get_scenarios(self, dataset_version):
        return [record for record in self.records if record.dataset_version == dataset_version]


def test_demo_service_uses_canonical_fixture_and_phase_three_comparison_logic():
    result = DemoService(FixtureDemoRepository(), load_engine_config()).get_scenario()

    assert result.primary.existing_planned_area_ha == Decimal("32")
    assert result.primary.proposed_future_plan_area_ha == Decimal("8")
    assert result.projected_area_ha == Decimal("40")
    assert result.ratio == Decimal("1.6")
    assert result.risk == "high"
    assert result.comparison_current_ratio.quantize(Decimal("0.000001")) == Decimal("0.666667")
    assert result.comparison_current_risk == "low"
    assert result.comparison_projected_ratio == Decimal("1.111111111111111111111111111")
    assert result.comparison_projected_risk == "high"
