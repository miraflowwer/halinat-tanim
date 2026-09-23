"""Generate one deterministic, versioned TANIM synthetic data package."""

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
        DEFAULT_CROPS,
        DEFAULT_GEOGRAPHIES,
        DEFAULT_SCENARIOS,
        GENERATED_ROOT,
        classify_snapshot_ratio,
        load_json,
        parse_active,
        price_months,
        quarter_periods,
        read_csv_rows,
        sha256_file,
        stable_int,
        write_csv_rows,
        write_json,
    )
else:
    from data_common import (
        DEFAULT_CONFIG,
        DEFAULT_CROPS,
        DEFAULT_GEOGRAPHIES,
        DEFAULT_SCENARIOS,
        GENERATED_ROOT,
        classify_snapshot_ratio,
        load_json,
        parse_active,
        price_months,
        quarter_periods,
        read_csv_rows,
        sha256_file,
        stable_int,
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
    "planned_area_ha",
    "reference_area_ha",
    "area_unit",
    "ratio",
    "risk_level",
    "data_kind",
    "dataset_version",
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
SEASONAL_PRICE_FACTORS = (1.00, 1.02, 1.04, 1.07, 1.05, 1.01, 0.98, 0.96, 0.97, 1.00, 1.03, 1.02)
QUARTER_REFERENCE_FACTORS = (0.96, 1.00, 1.08, 0.98)
DATA_KIND = "synthetic_demo"
GENERATOR_METHOD_NOTE = (
    "Synthetic illustrative data generated from the fixed seed. It is not an observed or "
    "official value."
)


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
    quarter_periods(config)
    price_months(config)


def _profile_rows(crops: list[dict[str, str]], version: str) -> Iterable[dict[str, str]]:
    condition_text = {
        "vegetable": (
            "This crop grows best with enough sunlight, regular water, and well-drained soil.",
            "Mas mainam itong itanim sa lugar na may sapat na sikat ng araw, regular na dilig, "
            "at lupang hindi naiipunan ng tubig.",
        ),
        "fruit": (
            "This crop grows best in a warm place with enough sunlight and well-drained soil.",
            "Mas mainam itong itanim sa mainit na lugar na may sapat na sikat ng araw at lupang "
            "hindi naiipunan ng tubig.",
        ),
        "root_crop": (
            "This crop grows best in loose soil that drains well.",
            "Mas mainam itong itanim sa maluwag na lupang madaling magpaagos ng tubig.",
        ),
        "legume": (
            "This crop grows best in warm conditions and well-drained soil.",
            "Mas mainam itong itanim sa mainit na lugar at lupang hindi naiipunan ng tubig.",
        ),
        "herb": (
            "This crop grows best with sunlight and well-drained soil.",
            "Mas mainam itong itanim sa lugar na may sikat ng araw at lupang hindi naiipunan ng "
            "tubig.",
        ),
        "spice": (
            "This crop grows best in warm conditions and well-drained soil.",
            "Mas mainam itong itanim sa mainit na lugar at lupang hindi naiipunan ng tubig.",
        ),
    }
    for crop in sorted(_active_rows(crops), key=lambda row: row["crop_id"]):
        crop_name_en = crop["canonical_name_en"].strip()
        crop_name_tl = crop["canonical_name_tl"].strip() or crop_name_en
        conditions_en, conditions_tl = condition_text[crop["category"]]
        yield {
            "crop_id": crop["crop_id"],
            "summary_en": f"{crop_name_en} is grown for food and local markets.",
            "summary_tl": (
                f"Ang {crop_name_tl} ay itinatanim para sa pagkain at lokal na pamilihan."
            ),
            "growing_conditions_en": conditions_en,
            "growing_conditions_tl": conditions_tl,
            "soil_notes_en": (
                "Soil needs vary by place. Check local soil conditions before planting."
            ),
            "soil_notes_tl": (
                "Nag-iiba ang pangangailangan sa lupa bawat lugar. Suriin muna ang lokal na lupa "
                "bago magtanim."
            ),
            "data_kind": DATA_KIND,
            "dataset_version": version,
            "method_note": "General crop context only. This is not local agronomic advice.",
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
    periods: list[tuple[str, str]],
    overrides: dict[tuple[str, str, str], tuple[float, float]],
    seed: int,
    version: str,
    thresholds: dict[str, float],
) -> tuple[Iterable[dict[str, str]], Iterable[dict[str, str]]]:
    def calculate_reference_area(
        crop: dict[str, str], geography: dict[str, str], period_start: str, quarter_index: int
    ) -> float:
        base = CATEGORY_REFERENCE_BASES[crop["category"]]
        crop_factor = 0.75 + (stable_int(seed, "crop-reference", crop["crop_id"]) % 51) / 100
        location_factor = (
            0.70
            + (stable_int(seed, "reference-location", crop["crop_id"], geography["code"]) % 61)
            / 100
        )
        seasonal_factor = QUARTER_REFERENCE_FACTORS[quarter_index % len(QUARTER_REFERENCE_FACTORS)]
        quarter_factor = (
            0.95 + (stable_int(seed, "quarter-reference", crop["crop_id"], period_start) % 11) / 100
        )
        return round(base * crop_factor * location_factor * seasonal_factor * quarter_factor, 4)

    def reference_rows() -> Iterable[dict[str, str]]:
        for crop in sorted(_active_rows(crops), key=lambda row: row["crop_id"]):
            for geography in sorted(municipalities, key=lambda row: row["geography_id"]):
                for quarter_index, (period_start, period_end) in enumerate(periods):
                    special = overrides.get(
                        (crop["crop_id"], geography["geography_id"], period_start)
                    )
                    if special is None:
                        reference_area_value = calculate_reference_area(
                            crop, geography, period_start, quarter_index
                        )
                    else:
                        reference_area_value = special[0]
                    yield {
                        "crop_id": crop["crop_id"],
                        "geography_id": geography["geography_id"],
                        "period_start": period_start,
                        "period_end": period_end,
                        "reference_area_ha": f"{reference_area_value:.4f}",
                        "area_unit": "ha",
                        "data_kind": DATA_KIND,
                        "dataset_version": version,
                        "reference_sources": "PSA-OPENSTAT-2M4AFN08",
                        "method_note": GENERATOR_METHOD_NOTE,
                    }

    def snapshot_rows() -> Iterable[dict[str, str]]:
        for crop in sorted(_active_rows(crops), key=lambda row: row["crop_id"]):
            for geography in sorted(municipalities, key=lambda row: row["geography_id"]):
                for period_index, (period_start, period_end) in enumerate(periods):
                    special = overrides.get(
                        (crop["crop_id"], geography["geography_id"], period_start)
                    )
                    if special is None:
                        reference_area_value = calculate_reference_area(
                            crop, geography, period_start, period_index
                        )
                        ratio_target = (
                            0.60
                            + (
                                stable_int(
                                    seed,
                                    "planned-ratio",
                                    crop["crop_id"],
                                    geography["code"],
                                    period_start,
                                )
                                % 121
                            )
                            / 100
                        )
                        planned_area = round(reference_area_value * ratio_target, 4)
                    else:
                        reference_area_value, planned_area = special
                    ratio = round(planned_area / reference_area_value, 6)
                    yield {
                        "crop_id": crop["crop_id"],
                        "geography_id": geography["geography_id"],
                        "period_start": period_start,
                        "period_end": period_end,
                        "planned_area_ha": f"{planned_area:.4f}",
                        "reference_area_ha": f"{reference_area_value:.4f}",
                        "area_unit": "ha",
                        "ratio": f"{ratio:.6f}",
                        "risk_level": classify_snapshot_ratio(ratio, thresholds),
                        "data_kind": DATA_KIND,
                        "dataset_version": version,
                    }

    return reference_rows(), snapshot_rows()


def _suitability_rows(
    crops: list[dict[str, str]],
    municipalities: list[dict[str, str]],
    seed: int,
    version: str,
) -> Iterable[dict[str, str]]:
    for crop in sorted(_active_rows(crops), key=lambda row: row["crop_id"]):
        for geography in sorted(municipalities, key=lambda row: row["geography_id"]):
            bucket = stable_int(seed, "soil-suitability", crop["crop_id"], geography["code"]) % 100
            if bucket < 50:
                suitability = "suitable"
            elif bucket < 84:
                suitability = "moderately_suitable"
            elif bucket < 96:
                suitability = "low_suitability"
            else:
                suitability = "no_data"
            yield {
                "crop_id": crop["crop_id"],
                "geography_id": geography["geography_id"],
                "suitability_class": suitability,
                "data_kind": DATA_KIND,
                "dataset_version": version,
                "reference_sources": "PSA-OPENSTAT-2M4AFN08",
                "method_note": (
                    "Synthetic hash allocation for demo coverage only. This is not a soil survey "
                    "or a real-world location assessment."
                ),
            }


def _write_dataset(
    output_dir: Path,
    crops_path: Path,
    geographies_path: Path,
    config: dict[str, Any],
    scenarios_path: Path | None,
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
    periods = quarter_periods(config)
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
            "reference_supply_start": periods[0][0],
            "reference_supply_end": periods[-1][1],
            "reference_periods": [
                {"period_start": start, "period_end": end} for start, end in periods
            ],
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
            "reference_supply": "one row per active crop, city or municipality, and quarter",
            "supply_snapshots": "one row per active crop, city or municipality, and quarter",
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
        ],
        "method_notes": [
            "All agricultural numeric values are deterministic synthetic demo values.",
            (
                "Price ranges use manually set crop-category baselines, stable location factors, "
                "a smooth trend, seasonal factors, and small bounded variation. Baselines are "
                "not statistically calibrated to source publications."
            ),
            (
                "Area values use broad crop-category baselines and stable crop, location, and "
                "period factors."
            ),
            (
                "Soil suitability labels use a separate deterministic allocation. They are not "
                "market supply scores or measured soil results."
            ),
            (
                "Public sources inform data structure, crop naming, geography, crop coverage, and "
                "suitability concepts. They do not publish these generated values."
            ),
        ],
        "input_sha256": {
            "crops.csv": sha256_file(crops_path),
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
) -> dict[str, Any]:
    config = load_json(config_path)
    target = output_dir or GENERATED_ROOT / str(config["dataset_version"])
    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(tempfile.mkdtemp(prefix=".tanim-generation-", dir=target.parent))
    staging = staging_root / "dataset"
    try:
        metadata = _write_dataset(staging, crops_path, geographies_path, config, scenarios_path)
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
                )
        else:
            result = generate_dataset(
                args.crop_registry,
                args.geography_registry,
                args.config,
                args.output,
                args.scenarios,
                args.replace,
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
