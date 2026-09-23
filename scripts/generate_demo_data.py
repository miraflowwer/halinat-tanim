"""Generate one deterministic, versioned TANIM synthetic data package."""

# Profile copy is intentionally kept beside the generator so every crop has a visible,
# simple explanation without an extra runtime dependency.
# ruff: noqa: E501

import argparse
import json
import math
import shutil
import sys
import tempfile
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import Any

if __package__:
    from scripts.data_common import (
        DEFAULT_CONFIG,
        DEFAULT_CROP_SCOPE,
        DEFAULT_CROPS,
        DEFAULT_GEOGRAPHIES,
        DEFAULT_SCENARIOS,
        GENERATED_ROOT,
        classify_snapshot_ratio,
        load_json,
        parse_active,
        price_months,
        read_csv_rows,
        sha256_file,
        stable_int,
        supply_periods,
        write_csv_rows,
        write_json,
    )
else:
    from data_common import (
        DEFAULT_CONFIG,
        DEFAULT_CROP_SCOPE,
        DEFAULT_CROPS,
        DEFAULT_GEOGRAPHIES,
        DEFAULT_SCENARIOS,
        GENERATED_ROOT,
        classify_snapshot_ratio,
        load_json,
        parse_active,
        price_months,
        read_csv_rows,
        sha256_file,
        stable_int,
        supply_periods,
        write_csv_rows,
        write_json,
    )

PROFILE_FIELDS = [
    "crop_id",
    "summary_en",
    "summary_tl",
    "growing_conditions_en",
    "growing_conditions_tl",
    "soil_notes_en",
    "soil_notes_tl",
    "reference_sources",
    "data_kind",
    "dataset_version",
    "method_note",
]
PRICE_FIELDS = [
    "crop_id",
    "geography_id",
    "date",
    "price_php_per_kg",
    "currency",
    "price_unit",
    "data_kind",
    "dataset_version",
    "reference_sources",
]
REFERENCE_FIELDS = [
    "crop_id",
    "geography_id",
    "period_start",
    "period_end",
    "period_kind",
    "reference_area_ha",
    "area_unit",
    "data_kind",
    "dataset_version",
    "reference_sources",
    "method_note",
]
SNAPSHOT_FIELDS = [
    "crop_id",
    "geography_id",
    "period_start",
    "period_end",
    "period_kind",
    "planned_area_ha",
    "reference_area_ha",
    "area_unit",
    "ratio",
    "risk_level",
    "data_kind",
    "dataset_version",
    "reference_sources",
    "method_note",
]
SUITABILITY_FIELDS = [
    "crop_id",
    "geography_id",
    "suitability_class",
    "data_kind",
    "dataset_version",
    "reference_sources",
    "method_note",
]

CATEGORY_PRICE_BASES = {
    "vegetable": 65.0,
    "fruit": 55.0,
    "root_crop": 45.0,
    "legume": 95.0,
    "herb": 80.0,
    "spice": 120.0,
}
CATEGORY_REFERENCE_BASES = {
    "vegetable": 32.0,
    "fruit": 22.0,
    "root_crop": 18.0,
    "legume": 16.0,
    "herb": 8.0,
    "spice": 12.0,
}
PROVENANCE_IDS = {
    "profile": "TANIM-SYNTH-CROP-PROFILE-V1",
    "reference": "TANIM-SYNTH-REFERENCE-AREA-V1",
    "current_supply": "TANIM-SYNTH-CURRENT-SUPPLY-V1",
    "future_supply": "TANIM-SYNTH-FUTURE-SUPPLY-CONTEXT-V1",
    "soil": "TANIM-SYNTH-SOIL-BASELINE-V1",
}
PRICE_SOURCE_IDS = "PSA-OPENSTAT-2M4AFN08|DA-PRICE-MONITORING"
REGION_AGRICULTURAL_PROFILES = {
    "01": 0.92,
    "02": 0.98,
    "03": 1.16,
    "04": 1.04,
    "05": 0.90,
    "13": 0.16,
    "14": 0.78,
    "17": 0.68,
}
URBAN_NAME_MARKERS = (
    "city",
    "manila",
    "baguio",
    "antipolo",
    "angeles",
    "dagupan",
    "olongapo",
    "malolos",
    "meycauayan",
    "calamba",
    "batangas",
    "lipa",
    "lucena",
    "cavite",
    "tagaytay",
    "mariveles",
)
SOIL_CATEGORY_BASELINES = {
    "vegetable": 0.70,
    "fruit": 0.76,
    "root_crop": 0.80,
    "legume": 0.73,
    "herb": 0.67,
    "spice": 0.72,
}
SOIL_CROP_ADJUSTMENTS = {
    "avocado": 0.06,
    "banana": 0.08,
    "basil": 0.02,
    "bell_pepper": 0.04,
    "bitter_gourd": 0.02,
    "broccoli": -0.03,
    "cabbage": -0.02,
    "calamansi": 0.04,
    "carrot": -0.02,
    "cassava": 0.05,
    "cauliflower": -0.03,
    "chili_pepper": 0.03,
    "cucumber": 0.02,
    "eggplant": 0.04,
    "garlic": -0.01,
    "ginger": 0.03,
    "guava": 0.04,
    "lettuce": -0.04,
    "lemongrass": 0.03,
    "mango": 0.05,
    "mung_bean": 0.02,
    "okra": 0.03,
    "onion": -0.01,
    "papaya": 0.04,
    "peanut": 0.01,
    "pechay": 0.02,
    "pineapple": 0.05,
    "purple_yam": 0.03,
    "squash": 0.03,
    "string_bean": 0.02,
    "sweet_potato": 0.04,
    "taro": 0.01,
    "tomato": 0.04,
    "turmeric": 0.03,
    "watermelon": 0.02,
}
SEASONAL_PRICE_FACTORS = (1.00, 1.02, 1.04, 1.07, 1.05, 1.01, 0.98, 0.96, 0.97, 1.00, 1.03, 1.02)
QUARTER_REFERENCE_FACTORS = (0.96, 1.00, 1.08, 0.98)
DATA_KIND = "synthetic_demo"


def _active_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if parse_active(row.get("active", ""), "active")]


def _validate_generator_inputs(
    crops: list[dict[str, str]], geographies: list[dict[str, str]], config: dict[str, Any]
) -> None:
    if not config.get("dataset_version"):
        raise ValueError("dataset_config.json must set dataset_version")
    if not isinstance(config.get("seed"), int):
        raise ValueError("dataset_config.json seed must be an integer")
    active_crops = _active_rows(crops)
    active_geographies = _active_rows(geographies)
    if not active_crops:
        raise ValueError("crop registry has no active crops")
    if not active_geographies:
        raise ValueError("geography registry has no active records")
    invalid_crop_categories = sorted(
        {row.get("category", "") for row in active_crops} - set(CATEGORY_PRICE_BASES)
    )
    if invalid_crop_categories:
        raise ValueError(f"active crops use unsupported categories: {invalid_crop_categories}")
    if any(row.get("island_group") != "Luzon" for row in active_geographies):
        raise ValueError("active geography registry records must belong to Luzon")
    crop_ids = [row["crop_id"] for row in active_crops]
    geography_ids = [row["geography_id"] for row in active_geographies]
    if len(crop_ids) != len(set(crop_ids)):
        raise ValueError("active crop registry contains duplicate crop_id values")
    if len(geography_ids) != len(set(geography_ids)):
        raise ValueError("active geography registry contains duplicate geography_id values")
    supply_periods(config)
    price_months(config)


def _profile_rows(crops: list[dict[str, str]], version: str) -> Iterable[dict[str, str]]:
    context = {
        "avocado": ("A tree fruit with creamy flesh and a long growing cycle.", "Puno itong namumunga ng malambot na prutas at mahaba ang panahon ng paglaki.", "Warm weather, sun, and steady moisture support the tree.", "Kailangan nito ng mainit na panahon, araw, at tuloy-tuloy na kahalumigmigan.", "Use deep soil with good drainage and enough space for roots.", "Pumili ng malalim at maayos ang paagusan na lupa para sa mga ugat."),
        "banana": ("A perennial fruit crop that produces bunches from a clump.", "Pangmatagalang pananim ito na namumunga ng kumpol mula sa isang tuod.", "Warm, humid places with regular water suit banana.", "Angkop dito ang mainit at mahalumigmig na lugar na may regular na tubig.", "Use fertile soil that drains well but does not dry too quickly.", "Gumamit ng matabang lupang may maayos na paagusan pero hindi agad natutuyo."),
        "basil": ("A leafy herb used fresh for flavor and cooking.", "Dahon itong halamang-gamot na ginagamit na sariwa sa pagluluto.", "Basil likes warm sun, regular light watering, and air movement.", "Gusto ng balanoy ang init, banayad na regular na dilig, at maaliwalas na hangin.", "Loose soil with compost and good drainage helps the leaves grow.", "Makakatulong ang maluwag na lupang may compost at maayos na paagusan."),
        "bell_pepper": ("A mild pepper crop grown for its crisp, hollow fruit.", "Banayad ang anghang ng pamintang kampana at malutong ang bunga nito.", "It needs warm weather, sun, and even water during fruiting.", "Kailangan nito ng init, araw, at pantay na tubig habang namumunga.", "Use fertile loam that drains well and does not stay flooded.", "Gumamit ng matabang loam na maayos ang paagusan at hindi binabaha."),
        "bitter_gourd": ("A climbing vine with ridged fruit used as a vegetable.", "Baging itong may gulugod na bunga na ginagamit na gulay.", "Warm sun and a trellis help the vine grow and set fruit.", "Nakakatulong ang mainit na araw at balag para lumaki at mamunga ito.", "Use loose, fertile soil that drains well around the roots.", "Pumili ng maluwag at matabang lupang maayos ang paagusan sa paligid ng ugat."),
        "broccoli": ("A cool-season vegetable that forms a compact flower head.", "Gulay itong mas malamig na panahon ang gusto at bumubuo ng kumpol na bulaklak.", "Mild temperatures and steady water support a firm head.", "Mas gusto nito ang katamtamang lamig at regular na tubig.", "Use fertile soil rich in organic matter with good drainage.", "Gumamit ng matabang lupang may organikong bagay at maayos na paagusan."),
        "cabbage": ("A leafy vegetable that forms a tight head above the soil.", "Madahong gulay itong bumubuo ng siksik na ulo sa ibabaw ng lupa.", "Cool to mild weather and regular water help the head form.", "Nakakatulong ang malamig hanggang banayad na panahon at regular na tubig.", "Use fertile, moisture-holding soil that still drains excess water.", "Gumamit ng matabang lupang may kahalumigmigan pero umaagos ang sobrang tubig."),
        "calamansi": ("A small citrus fruit used for juice, seasoning, and drinks.", "Maliit itong prutas na citrus para sa katas, sawsawan, at inumin.", "Warm sun and steady moisture support flowering and fruiting.", "Nakakatulong ang init, araw, at regular na kahalumigmigan sa pamumulaklak at bunga.", "Use slightly acidic, well-drained soil and avoid standing water.", "Pumili ng bahagyang maasim na lupang maayos ang paagusan at walang nakatigil na tubig."),
        "carrot": ("A root vegetable valued for its crisp, colored root.", "Ugat na gulay ito na pinahahalagahan dahil sa malutong at makulay na ugat.", "Cool conditions and even moisture help the root develop.", "Mas gusto nito ang malamig na kondisyon at pantay na kahalumigmigan.", "Use deep, stone-free, loose soil so the root can expand.", "Gumamit ng malalim, maluwag, at walang bato na lupa para lumaki ang ugat."),
        "cassava": ("A hardy root crop that stores energy in thick underground roots.", "Matibay itong ugat na gulay na nag-iimbak ng pagkain sa malalaking ugat.", "Warm weather and a long, mostly dry growing period suit cassava.", "Angkop dito ang init at mahabang panahong hindi palaging basa ang lupa.", "Use loose soil with good drainage so roots can enlarge.", "Pumili ng maluwag at maayos ang paagusan na lupa para lumaki ang ugat."),
        "cauliflower": ("A cool-season vegetable that forms a pale flower head.", "Gulay itong malamig na panahon ang gusto at bumubuo ng maputing kumpol na bulaklak.", "Mild temperatures, sun, and steady water support head quality.", "Nakakatulong ang banayad na temperatura, araw, at regular na tubig sa kumpol.", "Use fertile soil with organic matter and good drainage.", "Gumamit ng matabang lupang may organikong bagay at maayos na paagusan."),
        "chili_pepper": ("A pepper crop grown for its hot, slender fruits.", "Paminta itong itinatanim para sa maanghang at pahabang bunga.", "Warm sun and regular water support flowering and fruit set.", "Nakakatulong ang mainit na araw at regular na tubig sa pamumulaklak at bunga.", "Use fertile, well-drained soil and avoid long periods of flooding.", "Gumamit ng matabang lupang maayos ang paagusan at iwasan ang matagal na baha."),
        "cucumber": ("A fast-growing vine that produces crisp fruits.", "Mabilis lumaking baging ito na namumunga ng malutong na pipino.", "Warm weather, sun, and steady water help the vine fruit.", "Gusto nito ang init, araw, at pantay na tubig habang namumunga.", "Use loose fertile soil and a support system when space is limited.", "Gumamit ng maluwag na matabang lupa at balag kung maliit ang espasyo."),
        "eggplant": ("A warm-season vegetable with smooth purple or pale fruit.", "Gulay itong mahilig sa init at may makinis na lila o mapusyaw na bunga.", "Warm sun and regular water support continued fruiting.", "Nakakatulong ang init, araw, at regular na tubig sa tuloy-tuloy na pamumunga.", "Use fertile loam that drains well and holds moderate moisture.", "Pumili ng matabang loam na umaagos ang tubig at may katamtamang kahalumigmigan."),
        "garlic": ("A bulb crop used as a strong-flavored cooking ingredient.", "Ugat-bulb ito na ginagamit na pampalasa sa maraming lutuin.", "Mild weather, sun, and a drier period near harvest help bulb formation.", "Mas angkop ang banayad na panahon, araw, at mas tuyong panahon bago anihin.", "Use loose, well-drained soil so bulbs do not stay wet.", "Gumamit ng maluwag at maayos ang paagusan na lupa para hindi mabasa ang bulb."),
        "ginger": ("A rhizome crop used fresh, dried, and as a cooking spice.", "Rhizome itong ginagamit na sariwa, tuyo, at pampalasa sa pagluluto.", "Warm conditions, filtered sun, and regular moisture support rhizomes.", "Nakakatulong ang init, bahagyang lilim, at regular na kahalumigmigan sa rhizome.", "Use loose soil rich in organic matter with good drainage.", "Gumamit ng maluwag na lupang may organikong bagay at maayos na paagusan."),
        "guava": ("A fruit tree with fragrant fruit that may be eaten fresh.", "Punong namumunga ito ng mabangong bayabas na maaaring kainin nang sariwa.", "Warm sun and regular moisture help the tree grow and fruit.", "Nakakatulong ang mainit na araw at regular na tubig sa paglaki at bunga.", "Use deep, fertile soil that drains excess water.", "Gumamit ng malalim at matabang lupang umaagos ang sobrang tubig."),
        "lettuce": ("A leafy crop used fresh in salads and simple meals.", "Madahong gulay ito na karaniwang sariwa sa salad at magagaan na pagkain.", "Cool conditions and light, regular water help keep leaves tender.", "Mas gusto nito ang malamig na kondisyon at banayad na regular na dilig.", "Use fertile soil with good drainage and enough organic matter.", "Gumamit ng matabang lupang maayos ang paagusan at may organikong bagay."),
        "lemongrass": ("An aromatic grass used in soups, drinks, and seasoning.", "Mabangong damo ito na ginagamit sa sabaw, inumin, at pampalasa.", "Warm sun and regular moisture support strong leafy clumps.", "Nakakatulong ang mainit na araw at regular na tubig sa malalaking kumpol ng dahon.", "Use ordinary fertile soil that drains well and is not waterlogged.", "Gumamit ng matabang lupang maayos ang paagusan at hindi binabaha."),
        "mango": ("A long-lived fruit tree with sweet seasonal fruit.", "Pangmatagalang puno ito na namumunga ng matamis na prutas sa panahon nito.", "Warm sun and a dry period can support flowering before fruiting.", "Nakakatulong ang mainit na araw at tuyong panahon bago mamulaklak.", "Use deep soil with good drainage and room for a large root system.", "Pumili ng malalim na lupang maayos ang paagusan at may espasyo para sa ugat."),
        "mung_bean": ("A short-season legume grown for small green beans.", "Maikling-panahong legume ito na itinatanim para sa maliliit na butil.", "Warm weather and moderate water suit the crop.", "Angkop dito ang mainit na panahon at katamtamang tubig.", "Use well-drained soil and avoid standing water around the roots.", "Gumamit ng lupang maayos ang paagusan at iwasan ang tubig na nakatigil."),
        "okra": ("A warm-season vegetable with edible tender pods.", "Gulay itong mahilig sa init at may malalambot na pod na kinakain.", "Warm sun and regular picking help the plant keep producing pods.", "Nakakatulong ang init, araw, at regular na pamimitas para patuloy ang pod.", "Use fertile soil that drains well and holds moderate moisture.", "Pumili ng matabang lupang maayos ang paagusan at may katamtamang kahalumigmigan."),
        "onion": ("A bulb crop used for flavor in many everyday dishes.", "Ugat-bulb ito na pampalasa sa maraming pang-araw-araw na lutuin.", "Mild weather, sun, and a drier finish help bulbs mature.", "Mas gusto nito ang banayad na panahon, araw, at tuyong panahon bago anihin.", "Use loose, fertile soil that does not hold water around bulbs.", "Gumamit ng maluwag at matabang lupang hindi nag-iipon ng tubig sa bulb."),
        "papaya": ("A fast-growing fruit tree that can bear fruit over a long season.", "Mabilis lumaking puno ito na maaaring mamunga sa mahabang panahon.", "Warm sun and steady moisture support leaves, flowers, and fruit.", "Nakakatulong ang init, araw, at regular na tubig sa dahon, bulaklak, at bunga.", "Use deep, fertile soil with strong drainage around the stem.", "Gumamit ng malalim at matabang lupang mabilis umagos ang tubig sa puno."),
        "peanut": ("A legume that develops its pods below the soil surface.", "Legume itong bumubuo ng pod sa ilalim ng lupa.", "Warm weather and a mostly dry harvest period suit peanut.", "Angkop dito ang init at mas tuyong panahon bago anihin.", "Use loose sandy loam so pods can form and be lifted easily.", "Gumamit ng maluwag na sandy loam para mabuo at madaling mahukay ang pod."),
        "pechay": ("A quick leafy vegetable used in soups and stir-fries.", "Mabilis lumaking madahong gulay ito para sa sabaw at ginisa.", "Mild weather, sun, and regular water support tender leaves.", "Nakakatulong ang banayad na panahon, araw, at regular na tubig sa malambot na dahon.", "Use fertile, well-drained soil with enough organic matter.", "Gumamit ng matabang lupang maayos ang paagusan at may organikong bagay."),
        "pineapple": ("A perennial fruit crop that forms one fruit on each mature plant.", "Pangmatagalang prutas ito na karaniwang isang bunga bawat hustong halaman.", "Warm sun and moderate moisture support leaf and fruit growth.", "Nakakatulong ang init, araw, at katamtamang tubig sa dahon at bunga.", "Use acidic, well-drained soil and avoid standing water.", "Pumili ng bahagyang maasim na lupang maayos ang paagusan at walang nakatigil na tubig."),
        "purple_yam": ("A climbing root crop known for its purple underground tuber.", "Baging itong ugat na gulay na kilala sa lilang tuber sa ilalim ng lupa.", "Warm weather and a long season support tuber growth.", "Nakakatulong ang init at mahabang panahon sa paglaki ng tuber.", "Use deep, loose soil so tubers can enlarge without standing water.", "Gumamit ng malalim at maluwag na lupang walang naiipong tubig."),
        "squash": ("A spreading vine with large fruit used in many local dishes.", "Baging itong kumakalat at may malaking bungang ginagamit sa maraming lutuin.", "Warm sun, space, and regular water help vines set fruit.", "Kailangan nito ng init, araw, espasyo, at regular na tubig para mamunga.", "Use fertile soil with good drainage and room for the roots.", "Gumamit ng matabang lupang maayos ang paagusan at may espasyo sa ugat."),
        "string_bean": ("A climbing bean harvested while the pods are still tender.", "Baging itong bean na inaani habang malambot pa ang pod.", "Warm weather, sun, and a trellis support a long picking period.", "Nakakatulong ang init, araw, at balag sa mahabang panahon ng pamimitas.", "Use fertile, well-drained soil with moderate moisture.", "Gumamit ng matabang lupang maayos ang paagusan at may katamtamang tubig."),
        "sweet_potato": ("A spreading root crop that forms edible storage roots.", "Gumagapang itong ugat na gulay na bumubuo ng nakakain na ugat.", "Warm weather and moderate moisture support root bulking.", "Nakakatulong ang init at katamtamang kahalumigmigan sa paglaki ng ugat.", "Use loose soil that drains well so roots can expand.", "Gumamit ng maluwag at maayos ang paagusan na lupa para lumaki ang ugat."),
        "taro": ("A root crop that grows edible corms and broad leaves.", "Ugat na gulay ito na may nakakain na corm at malalapad na dahon.", "Warm, moist conditions support corm and leaf growth.", "Nakakatulong ang mainit at mamasa-masang kondisyon sa corm at dahon.", "Use moisture-holding soil, but keep the planting area from stagnant water.", "Gumamit ng lupang may kahalumigmigan pero walang matagal na nakatigil na tubig."),
        "tomato": ("A fruiting vegetable used fresh, cooked, and in sauces.", "Bungang gulay ito na ginagamit na sariwa, luto, at sawsawan o sarsa.", "Warm sun, regular water, and support for branches help fruiting.", "Nakakatulong ang init, araw, regular na tubig, at suporta sa mga sanga.", "Use fertile loam with good drainage and avoid waterlogged roots.", "Pumili ng matabang loam na maayos ang paagusan at hindi binabaha ang ugat."),
        "turmeric": ("A rhizome crop used for color, flavor, and traditional cooking.", "Rhizome itong ginagamit sa kulay, lasa, at tradisyonal na pagluluto.", "Warm conditions, filtered sun, and steady moisture support rhizomes.", "Nakakatulong ang init, bahagyang lilim, at regular na kahalumigmigan sa rhizome.", "Use loose soil rich in organic matter with good drainage.", "Gumamit ng maluwag na lupang may organikong bagay at maayos na paagusan."),
        "watermelon": ("A warm-season vine that produces large, water-rich fruit.", "Baging itong mahilig sa init at may malaking bungang maraming tubig.", "Warm sun, open space, and steady water support fruit filling.", "Kailangan nito ng init, araw, maluwag na espasyo, at regular na tubig.", "Use sandy loam that drains well so vines and fruit stay healthy.", "Gumamit ng sandy loam na maayos ang paagusan para sa baging at bunga."),
    }
    for crop in sorted(_active_rows(crops), key=lambda row: row["crop_id"]):
        crop_name_en = crop["canonical_name_en"].strip()
        crop_name_tl = crop["canonical_name_tl"].strip() or crop_name_en
        summary_en, summary_tl, conditions_en, conditions_tl, soil_en, soil_tl = context.get(
            crop["crop_id"],
            (
                f"{crop_name_en} is a {crop['category'].replace('_', ' ')} crop for food and local markets.",
                f"Ang {crop_name_tl} ay {crop['category'].replace('_', ' ')} na pananim para sa pagkain at lokal na pamilihan.",
                "This crop needs suitable local weather, enough light, and regular water.",
                "Kailangan nito ng angkop na panahon, sapat na liwanag, at regular na tubig.",
                "Check local soil drainage and fertility before planting.",
                "Suriin ang paagusan at katabaan ng lokal na lupa bago magtanim.",
            ),
        )
        yield {
            "crop_id": crop["crop_id"],
            "summary_en": summary_en,
            "summary_tl": summary_tl,
            "growing_conditions_en": conditions_en,
            "growing_conditions_tl": conditions_tl,
            "soil_notes_en": soil_en,
            "soil_notes_tl": soil_tl,
            "reference_sources": PROVENANCE_IDS["profile"],
            "data_kind": DATA_KIND,
            "dataset_version": version,
            "method_note": "Simple crop context for the demo. It is not local agronomic advice or a yield guarantee.",
        }


def _price_rows(
    crops: list[dict[str, str]],
    markets: list[dict[str, str]],
    months: list[str],
    seed: int,
    version: str,
) -> Iterable[dict[str, str]]:
    base_month = date.fromisoformat(months[0])
    for crop in sorted(_active_rows(crops), key=lambda row: row["crop_id"]):
        category_base = CATEGORY_PRICE_BASES[crop["category"]]
        crop_adjustment = 0.75 + (stable_int(seed, "crop-price", crop["crop_id"]) % 51) / 100
        crop_base = category_base * crop_adjustment
        season_shift = stable_int(seed, "season-shift", crop["crop_id"]) % len(
            SEASONAL_PRICE_FACTORS
        )
        for geography in sorted(markets, key=lambda row: row["geography_id"]):
            geography_factor = (
                0.90
                + (stable_int(seed, "price-location", crop["crop_id"], geography["code"]) % 21)
                / 100
            )
            for month_value in months:
                month = date.fromisoformat(month_value)
                month_offset = (month.year - base_month.year) * 12 + month.month - base_month.month
                seasonal_index = (month.month - 1 + season_shift) % len(SEASONAL_PRICE_FACTORS)
                seasonal_factor = SEASONAL_PRICE_FACTORS[seasonal_index]
                trend_factor = 0.93 + 0.14 * month_offset / max(1, len(months) - 1)
                small_change = (
                    0.985
                    + (
                        stable_int(
                            seed, "price-change", crop["crop_id"], geography["code"], month_value
                        )
                        % 31
                    )
                    / 1000
                )
                price = max(
                    0.01,
                    crop_base * geography_factor * seasonal_factor * trend_factor * small_change,
                )
                yield {
                    "crop_id": crop["crop_id"],
                    "geography_id": geography["geography_id"],
                    "date": month_value,
                    "price_php_per_kg": f"{price:.2f}",
                    "currency": "PHP",
                    "price_unit": "PHP/kg",
                    "data_kind": DATA_KIND,
                    "dataset_version": version,
                    "reference_sources": "PSA-OPENSTAT-2M4AFN08|DA-PRICE-MONITORING",
                }


def _scenario_overrides(
    scenarios_path: Path | None,
) -> dict[tuple[str, str, str], tuple[float, float]]:
    if scenarios_path is None or not scenarios_path.is_file():
        return {}
    payload = load_json(scenarios_path)
    if not isinstance(payload, dict):
        raise ValueError("demo fixtures must be a JSON object")
    scenarios = payload.get("scenarios", [])
    if not isinstance(scenarios, list):
        raise ValueError("demo fixture scenarios must be a list")
    result: dict[tuple[str, str, str], tuple[float, float]] = {}
    for index, scenario in enumerate(scenarios, start=1):
        if not isinstance(scenario, dict):
            raise ValueError(f"demo scenario row {index} must be an object")
        for field in ("crop_id", "geography_id", "period_start"):
            if not isinstance(scenario.get(field), str) or not scenario[field]:
                raise ValueError(f"demo scenario row {index}: {field} must be a non-empty string")
        key = (scenario["crop_id"], scenario["geography_id"], scenario["period_start"])
        if key in result:
            raise ValueError(f"duplicate demo scenario target for {key}")
        try:
            reference_area = float(scenario["reference_area_ha"])
            existing_area = float(scenario["existing_planned_area_ha"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"demo scenario row {index} has invalid override areas") from error
        if not math.isfinite(reference_area) or reference_area <= 0:
            raise ValueError(f"demo scenario row {index} reference_area_ha must be positive")
        if not math.isfinite(existing_area) or existing_area < 0:
            raise ValueError(
                f"demo scenario row {index} existing_planned_area_ha must be non-negative"
            )
        result[key] = (reference_area, existing_area)
    return result


def _reference_and_snapshot_rows(
    crops: list[dict[str, str]],
    municipalities: list[dict[str, str]],
    periods: list[tuple[str, str, str]],
    overrides: dict[tuple[str, str, str], tuple[float, float]],
    seed: int,
    version: str,
    thresholds: dict[str, float],
) -> tuple[Iterable[dict[str, str]], Iterable[dict[str, str]]]:
    def geographic_profile(geography: dict[str, str]) -> tuple[float, float]:
        region_factor = REGION_AGRICULTURAL_PROFILES.get(geography["code"][:2], 0.85)
        province_band = 0.90 + (int(geography["code"][2:4]) % 5) * 0.035
        normalized_name = geography["name"].casefold()
        if geography["code"].startswith("13"):
            municipality_scale = 0.10
        elif any(marker in normalized_name for marker in URBAN_NAME_MARKERS):
            municipality_scale = 0.45
        else:
            municipality_scale = 0.86 + (int(geography["code"][6:8]) % 5) * 0.035
        return region_factor * province_band, municipality_scale

    def calculate_reference_area(
        crop: dict[str, str],
        geography: dict[str, str],
        period_start: str,
        period_kind: str,
        period_index: int,
    ) -> float:
        base = CATEGORY_REFERENCE_BASES[crop["category"]]
        crop_factor = 0.84 + (
            stable_int(seed, "crop-reference-behavior", crop["crop_id"]) % 33
        ) / 100
        geographic_factor, municipality_scale = geographic_profile(geography)
        bounded_variation = 0.97 + (
            stable_int(seed, "reference-variation", crop["crop_id"], geography["code"]) % 7
        ) / 100
        if period_kind == "current_supply":
            seasonal_factor = 0.94
            period_variation = 0.99 + (
                stable_int(seed, "current-supply-period", crop["crop_id"]) % 5
            ) / 100
        else:
            seasonal_factor = QUARTER_REFERENCE_FACTORS[(period_index - 1) % len(QUARTER_REFERENCE_FACTORS)]
            period_variation = 0.98 + (
                stable_int(seed, "future-period-variation", crop["crop_id"], period_start) % 5
            ) / 100
        return round(
            max(
                0.2,
                base
                * crop_factor
                * geographic_factor
                * municipality_scale
                * seasonal_factor
                * period_variation
                * bounded_variation,
            ),
            4,
        )

    def reference_rows() -> Iterable[dict[str, str]]:
        for crop in sorted(_active_rows(crops), key=lambda row: row["crop_id"]):
            for geography in sorted(municipalities, key=lambda row: row["geography_id"]):
                for period_index, (period_start, period_end, period_kind) in enumerate(periods):
                    special = overrides.get(
                        (crop["crop_id"], geography["geography_id"], period_start)
                    )
                    if special is None:
                        reference_area_value = calculate_reference_area(
                            crop, geography, period_start, period_kind, period_index
                        )
                    else:
                        reference_area_value = special[0]
                    yield {
                        "crop_id": crop["crop_id"],
                        "geography_id": geography["geography_id"],
                        "period_start": period_start,
                        "period_end": period_end,
                        "period_kind": period_kind,
                        "reference_area_ha": f"{reference_area_value:.4f}",
                        "area_unit": "ha",
                        "data_kind": DATA_KIND,
                        "dataset_version": version,
                        "reference_sources": PROVENANCE_IDS["reference"],
                        "method_note": (
                            "Reference area uses crop behavior, regional and province profiles, "
                            "municipality scale, a period factor, and bounded deterministic variation. "
                            "It is synthetic context, not an agronomic prediction."
                        ),
                    }

    def snapshot_rows() -> Iterable[dict[str, str]]:
        for crop in sorted(_active_rows(crops), key=lambda row: row["crop_id"]):
            for geography in sorted(municipalities, key=lambda row: row["geography_id"]):
                for period_index, (period_start, period_end, period_kind) in enumerate(periods):
                    special = overrides.get(
                        (crop["crop_id"], geography["geography_id"], period_start)
                    )
                    if special is None:
                        reference_area_value = calculate_reference_area(
                            crop, geography, period_start, period_kind, period_index
                        )
                        ratio_base = 0.76 if period_kind == "current_supply" else 0.82
                        ratio_target = ratio_base + (
                            stable_int(
                                seed,
                                "planned-ratio",
                                crop["crop_id"],
                                geography["code"],
                                period_start,
                            )
                            % 39
                        ) / 100
                        planned_area = round(reference_area_value * ratio_target, 4)
                    else:
                        reference_area_value, planned_area = special
                    ratio = round(planned_area / reference_area_value, 6)
                    yield {
                        "crop_id": crop["crop_id"],
                        "geography_id": geography["geography_id"],
                        "period_start": period_start,
                        "period_end": period_end,
                        "period_kind": period_kind,
                        "planned_area_ha": f"{planned_area:.4f}",
                        "reference_area_ha": f"{reference_area_value:.4f}",
                        "area_unit": "ha",
                        "ratio": f"{ratio:.6f}",
                        "risk_level": classify_snapshot_ratio(ratio, thresholds),
                        "data_kind": DATA_KIND,
                        "dataset_version": version,
                        "reference_sources": (
                            PROVENANCE_IDS["current_supply"]
                            if period_kind == "current_supply"
                            else PROVENANCE_IDS["future_supply"]
                        ),
                        "method_note": (
                            "Current supply context for the map. It is not a registered future planting plan."
                            if period_kind == "current_supply"
                            else "Future reference context for later planning work. It is not a Phase 3 decision result."
                        ),
                    }

    return reference_rows(), snapshot_rows()


def _suitability_rows(
    crops: list[dict[str, str]],
    municipalities: list[dict[str, str]],
    seed: int,
    version: str,
) -> Iterable[dict[str, str]]:
    def geographic_baseline(geography: dict[str, str]) -> float:
        region_factor = REGION_AGRICULTURAL_PROFILES.get(geography["code"][:2], 0.85)
        if geography["code"].startswith("13"):
            return 0.28
        if any(marker in geography["name"].casefold() for marker in URBAN_NAME_MARKERS):
            return 0.62 * region_factor
        return min(1.0, region_factor * (0.92 + (int(geography["code"][2:4]) % 4) * 0.04))

    for crop in sorted(_active_rows(crops), key=lambda row: row["crop_id"]):
        for geography in sorted(municipalities, key=lambda row: row["geography_id"]):
            baseline = (
                SOIL_CATEGORY_BASELINES[crop["category"]]
                + SOIL_CROP_ADJUSTMENTS.get(crop["crop_id"], 0.0)
            ) * geographic_baseline(geography)
            variation = (
                stable_int(seed, "soil-suitability-variation", crop["crop_id"], geography["code"])
                % 7
                - 3
            ) / 100
            score = max(0.0, min(1.0, baseline + variation))
            if score >= 0.72:
                suitability = "suitable"
            elif score >= 0.48:
                suitability = "moderately_suitable"
            elif score >= 0.22:
                suitability = "low_suitability"
            else:
                suitability = "no_data"
            yield {
                "crop_id": crop["crop_id"],
                "geography_id": geography["geography_id"],
                "suitability_class": suitability,
                "data_kind": DATA_KIND,
                "dataset_version": version,
                "reference_sources": PROVENANCE_IDS["soil"],
                "method_note": (
                    "Synthetic suitability baseline from crop behavior, broad geography profile, "
                    "urban scale, and bounded deterministic variation. This is not a soil survey "
                    "or a real-world location assessment."
                ),
            }


def _write_dataset(
    output_dir: Path,
    crops_path: Path,
    geographies_path: Path,
    config: dict[str, Any],
    scenarios_path: Path | None,
    crop_scope_path: Path,
) -> dict[str, Any]:
    crops = read_csv_rows(crops_path)
    geographies = read_csv_rows(geographies_path)
    _validate_generator_inputs(crops, geographies, config)
    active_crops = _active_rows(crops)
    active_geographies = _active_rows(geographies)
    municipalities = [row for row in active_geographies if row["level"] == "municipality_city"]
    provinces = [row for row in active_geographies if row["level"] == "province"]
    regions = [row for row in active_geographies if row["level"] == "region"]
    markets = [*provinces, *(row for row in regions if row["code"] == "1300000000")]
    if not municipalities:
        raise ValueError("geography registry has no active municipality or city records")
    if not markets:
        raise ValueError("geography registry has no active province or NCR market records")

    version = str(config["dataset_version"])
    seed = int(config["seed"])
    thresholds = config["snapshot_thresholds"]
    periods = supply_periods(config)
    months = price_months(config)
    overrides = _scenario_overrides(scenarios_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    files: dict[str, dict[str, Any]] = {}
    profiles_path = output_dir / "crop_profiles.csv"
    files[profiles_path.name] = {
        "row_count": write_csv_rows(profiles_path, PROFILE_FIELDS, _profile_rows(crops, version)),
        "sha256": sha256_file(profiles_path),
    }
    prices_path = output_dir / "price_history.csv"
    files[prices_path.name] = {
        "row_count": write_csv_rows(
            prices_path, PRICE_FIELDS, _price_rows(crops, markets, months, seed, version)
        ),
        "sha256": sha256_file(prices_path),
    }

    references, snapshots = _reference_and_snapshot_rows(
        crops, municipalities, periods, overrides, seed, version, thresholds
    )
    reference_path = output_dir / "crop_references.csv"
    files[reference_path.name] = {
        "row_count": write_csv_rows(reference_path, REFERENCE_FIELDS, references),
        "sha256": sha256_file(reference_path),
    }
    snapshot_path = output_dir / "supply_snapshots.csv"
    files[snapshot_path.name] = {
        "row_count": write_csv_rows(snapshot_path, SNAPSHOT_FIELDS, snapshots),
        "sha256": sha256_file(snapshot_path),
    }
    suitability_path = output_dir / "soil_suitability.csv"
    files[suitability_path.name] = {
        "row_count": write_csv_rows(
            suitability_path,
            SUITABILITY_FIELDS,
            _suitability_rows(crops, municipalities, seed, version),
        ),
        "sha256": sha256_file(suitability_path),
    }

    counts = {
        "active_crops": len(active_crops),
        "regions": len(regions),
        "provinces": len(provinces),
        "municipalities_cities": len(municipalities),
    }
    metadata = {
        "dataset_version": version,
        "data_kind": DATA_KIND,
        "generation_version": config["generation_version"],
        "seed": seed,
        "geographic_scope": {
            "country": "Philippines",
            "island_group": "Luzon",
            "levels": ["region", "province", "municipality_city"],
            "counts": counts,
            "barangay_level_included": False,
            "parent_note": (
                "NCR cities and Pateros link directly to NCR because PSGC does not define "
                "provinces within NCR."
            ),
        },
        "periods": {
            "price_history_start": months[0],
            "price_history_end": months[-1],
            "current_supply": {
                "period_start": periods[0][0],
                "period_end": periods[0][1],
                "period_kind": periods[0][2],
            },
            "future_planning": {
                "period_start": periods[1][0],
                "period_end": periods[-1][1],
                "period_kind": "future_planning",
                "periods": [
                    {"period_start": start, "period_end": end, "period_kind": kind}
                    for start, end, kind in periods[1:]
                ],
            },
        },
        "canonical_units": {
            "price_history": {"currency": "PHP", "unit": "PHP/kg"},
            "planned_area": "ha",
            "reference_area": "ha",
            "ratio": "dimensionless decimal",
        },
        "coverage": {
            "profiles": "one row for each active crop",
            "prices": "36 monthly points per active crop and province, plus NCR",
            "reference_supply": (
                "one current supply context row and one future planning reference row per active "
                "crop and city or municipality"
            ),
            "supply_snapshots": (
                "one current map context row and one future supply context row per active crop "
                "and city or municipality"
            ),
            "soil_suitability": "one row per active crop and city or municipality",
        },
        "snapshot_formula": {
            "ratio": "planned_area_ha / reference_area_ha, rounded to 6 decimal places",
            "risk_labels": {
                "low": f"ratio < {thresholds['low_below']}",
                "moderate": (f"{thresholds['low_below']} <= ratio <= {thresholds['high_above']}"),
                "high": f"ratio > {thresholds['high_above']}",
                "no_data": "reference area is missing or invalid",
            },
            "scope_note": (
                "This formula labels synthetic context snapshots only, not Phase 3 risk results."
            ),
        },
        "reference_sources": [
            "PSGC-Q2-2026",
            "PSA-OPENSTAT-2M4AFN08",
            "DA-PRICE-MONITORING",
            "Kew-Plants-of-the-World-Online",
            *PROVENANCE_IDS.values(),
        ],
        "provenance": {
            "crop_profiles": {
                "source_ids": [PROVENANCE_IDS["profile"]],
                "meaning": "TANIM method supplies simple crop context; no source published these profile sentences.",
            },
            "price_history": {
                "source_ids": ["PSA-OPENSTAT-2M4AFN08", "DA-PRICE-MONITORING"],
                "meaning": "Sources informed price concepts and crop coverage. They did not publish the generated prices.",
            },
            "crop_references": {
                "source_ids": [PROVENANCE_IDS["reference"]],
                "meaning": "TANIM method generated reference areas from structured synthetic geography and crop profiles.",
            },
            "supply_snapshots": {
                "source_ids": [
                    PROVENANCE_IDS["current_supply"],
                    PROVENANCE_IDS["future_supply"],
                ],
                "meaning": "TANIM methods generated current map context and future reference context separately.",
            },
            "soil_suitability": {
                "source_ids": [PROVENANCE_IDS["soil"]],
                "meaning": "TANIM method generated a baseline label. No external suitability record was copied.",
            },
        },
        "time_contract": {
            "current_supply_period": {
                "start": periods[0][0],
                "end": periods[0][1],
                "kind": "current_supply",
            },
            "future_planning_horizon": {
                "start": config["periods"]["future_planning"]["start"],
                "end": config["periods"]["future_planning"]["end"],
                "granularity": config["periods"]["future_planning"]["period_granularity"],
                "period_count": len(periods) - 1,
            },
        },
        "synthetic_model": {
            "reference_area": (
                "crop baseline x crop behavior x region profile x province band x municipality "
                "scale x period factor x bounded deterministic variation"
            ),
            "soil_suitability": (
                "crop and category baseline x geography suitability baseline x bounded deterministic "
                "variation; no hash bucket is the primary decision"
            ),
            "scope_note": "These are explainable demo values, not agronomic predictions or yield guarantees.",
        },
        "method_notes": [
            "All agricultural numeric values are deterministic synthetic demo values.",
            (
                "Price ranges use manually set crop-category baselines, stable location factors, "
                "a smooth trend, seasonal factors, and small bounded variation. Baselines are "
                "not statistically calibrated to source publications."
            ),
            (
                "Reference areas use crop behavior, region and province profiles, municipality "
                "scale, period factors, and small bounded deterministic variation. Obvious urban "
                "locations receive a lower scale."
            ),
            (
                "Soil suitability starts from crop and geographic baselines and then applies small "
                "bounded deterministic variation. It is not a soil survey or market supply score."
            ),
            (
                "Public sources inform data structure, crop naming, geography, crop coverage, and "
                "suitability concepts. They do not publish these generated values."
            ),
        ],
        "input_sha256": {
            "crops.csv": sha256_file(crops_path),
            "crop_scope_inventory.csv": sha256_file(crop_scope_path),
            "geographies.csv": sha256_file(geographies_path),
            **(
                {"demo_scenarios.json": sha256_file(scenarios_path)}
                if scenarios_path is not None and scenarios_path.is_file()
                else {}
            ),
        },
        "files": files,
    }
    write_json(output_dir / "metadata.json", metadata)
    return metadata


def _same_dataset(existing: Path, candidate: Path) -> bool:
    existing_files = {path.name for path in existing.iterdir() if path.is_file()}
    candidate_files = {path.name for path in candidate.iterdir() if path.is_file()}
    return existing_files == candidate_files and all(
        sha256_file(existing / name) == sha256_file(candidate / name)
        for name in sorted(candidate_files)
    )


def generate_dataset(
    crops_path: Path = DEFAULT_CROPS,
    geographies_path: Path = DEFAULT_GEOGRAPHIES,
    config_path: Path = DEFAULT_CONFIG,
    output_dir: Path | None = None,
    scenarios_path: Path | None = DEFAULT_SCENARIOS,
    replace: bool = False,
    crop_scope_path: Path | None = None,
) -> dict[str, Any]:
    config = load_json(config_path)
    scope_path = crop_scope_path or DEFAULT_CROP_SCOPE
    if not scope_path.is_file() and crops_path.resolve() == DEFAULT_CROPS.resolve():
        raise FileNotFoundError(f"crop scope inventory is missing: {scope_path}")
    if not scope_path.is_file():
        scope_path = DEFAULT_CROP_SCOPE
    target = output_dir or GENERATED_ROOT / str(config["dataset_version"])
    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(tempfile.mkdtemp(prefix=".tanim-generation-", dir=target.parent))
    staging = staging_root / "dataset"
    try:
        metadata = _write_dataset(
            staging, crops_path, geographies_path, config, scenarios_path, scope_path
        )
        if target.exists():
            if _same_dataset(target, staging):
                return {"path": target, "metadata": metadata, "unchanged": True}
            if not replace:
                raise FileExistsError(
                    f"dataset version already exists with different content: {target}. "
                    "Choose a new dataset_version or pass --replace explicitly."
                )
            backup = staging_root / "previous-dataset"
            target.replace(backup)
            try:
                staging.replace(target)
            except OSError:
                backup.replace(target)
                raise
            shutil.rmtree(backup)
        else:
            staging.replace(target)
        return {"path": target, "metadata": metadata, "unchanged": False}
    finally:
        if staging_root.exists():
            shutil.rmtree(staging_root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--crop-registry", type=Path, default=DEFAULT_CROPS)
    parser.add_argument("--crop-scope", type=Path, default=DEFAULT_CROP_SCOPE)
    parser.add_argument("--geography-registry", type=Path, default=DEFAULT_GEOGRAPHIES)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dataset-version")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--replace", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_json(args.config)
        if args.dataset_version:
            config["dataset_version"] = args.dataset_version
        if args.seed is not None:
            config["seed"] = args.seed
        if args.dataset_version or args.seed is not None:
            with tempfile.TemporaryDirectory(prefix="tanim-data-config-") as temporary:
                temporary_config = Path(temporary) / "dataset_config.json"
                write_json(temporary_config, config)
                result = generate_dataset(
                    args.crop_registry,
                    args.geography_registry,
                    temporary_config,
                    args.output,
                    args.scenarios,
                    args.replace,
                    args.crop_scope,
                )
        else:
            result = generate_dataset(
                args.crop_registry,
                args.geography_registry,
                args.config,
                args.output,
                args.scenarios,
                args.replace,
                args.crop_scope,
            )
    except (
        FileNotFoundError,
        FileExistsError,
        ValueError,
        OSError,
        KeyError,
        json.JSONDecodeError,
    ) as error:
        print(f"Demo data generation failed: {error}", file=sys.stderr)
        return 1

    metadata = result["metadata"]
    state = "already matches" if result["unchanged"] else "generated"
    print(
        f"Dataset {metadata['dataset_version']} {state} at {result['path']} "
        f"({metadata['geographic_scope']['counts']['active_crops']} active crops)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
