"""Validate canonical TANIM registries and one generated dataset version."""

import argparse
import csv
import json
import math
import re
import sys
import tempfile
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
        current_supply_period,
        is_finite_number,
        load_json,
        normalize_label,
        price_months,
        quarter_periods,
        sha256_file,
        supply_periods,
    )
    from scripts.generate_demo_data import (
        PRICE_FIELDS,
        PRICE_SOURCE_IDS,
        PROFILE_FIELDS,
        PROVENANCE_IDS,
        REFERENCE_FIELDS,
        SNAPSHOT_FIELDS,
        SUITABILITY_FIELDS,
        generate_dataset,
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
        current_supply_period,
        is_finite_number,
        load_json,
        normalize_label,
        price_months,
        quarter_periods,
        sha256_file,
        supply_periods,
    )
    from generate_demo_data import (
        PRICE_FIELDS,
        PRICE_SOURCE_IDS,
        PROFILE_FIELDS,
        PROVENANCE_IDS,
        REFERENCE_FIELDS,
        SNAPSHOT_FIELDS,
        SUITABILITY_FIELDS,
        generate_dataset,
    )

GEOGRAPHY_FIELDS = [
    "geography_id",
    "name",
    "level",
    "code",
    "parent_geography_id",
    "country",
    "island_group",
    "active",
]
CROP_FIELDS = [
    "crop_id",
    "canonical_name_en",
    "canonical_name_tl",
    "scientific_name",
    "category",
    "aliases_en",
    "aliases_tl",
    "active",
]
CROP_SCOPE_FIELDS = [
    "scope_id",
    "canonical_name_en",
    "category",
    "in_scope",
    "source_references",
    "aliases_en",
    "aliases_tl",
    "exclusion_reason",
]
ALLOWED_CATEGORIES = {"vegetable", "fruit", "root_crop", "legume", "herb", "spice"}
ALLOWED_LEVELS = {"region", "province", "municipality_city"}
ALLOWED_SUITABILITY = {"suitable", "moderately_suitable", "low_suitability", "no_data"}
ALLOWED_RISKS = {"low", "moderate", "high", "no_data"}
DATA_KIND = "synthetic_demo"
ID_PATTERNS = {
    "region": re.compile(r"^region_(\d{10})$"),
    "province": re.compile(r"^province_(\d{10})$"),
    "municipality_city": re.compile(r"^mun_(\d{10})$"),
}
ALLOWED_PROVENANCE = {
    "profile": {PROVENANCE_IDS["profile"]},
    "price": set(PRICE_SOURCE_IDS.split("|")),
    "reference": {PROVENANCE_IDS["reference"]},
    "current_supply": {PROVENANCE_IDS["current_supply"]},
    "future_supply": {PROVENANCE_IDS["future_supply"]},
    "soil": {PROVENANCE_IDS["soil"]},
}


def read_csv_document(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or []), list(reader)


def _missing_fields(fields: list[str], required: list[str], label: str, errors: list[str]) -> None:
    missing = sorted(set(required) - set(fields))
    if missing:
        errors.append(f"{label} is missing required columns: {', '.join(missing)}")


def _active_records(
    rows: list[dict[str, str]], label: str, errors: list[str]
) -> list[dict[str, str]]:
    active = []
    for row_number, row in enumerate(rows, start=2):
        value = row.get("active", "").strip().lower()
        if value not in {"true", "false"}:
            errors.append(f"{label} row {row_number}: active must be 'true' or 'false'")
        elif value == "true":
            active.append(row)
    return active


def validate_crop_registry(rows: list[dict[str, str]], errors: list[str]) -> list[dict[str, str]]:
    ids: dict[str, int] = {}
    aliases: dict[str, str] = {}
    for row_number, row in enumerate(rows, start=2):
        crop_id = row.get("crop_id", "").strip()
        if not re.fullmatch(r"[a-z][a-z0-9_]*", crop_id):
            errors.append(f"crop registry row {row_number}: invalid crop_id {crop_id!r}")
        if crop_id in ids:
            errors.append(f"crop registry row {row_number}: duplicate crop_id {crop_id!r}")
        ids[crop_id] = row_number
        if not row.get("canonical_name_en", "").strip():
            errors.append(f"crop registry row {row_number}: canonical_name_en is required")
        if not row.get("scientific_name", "").strip():
            errors.append(f"crop registry row {row_number}: scientific_name is required")
        if row.get("category", "") not in ALLOWED_CATEGORIES:
            errors.append(
                f"crop registry row {row_number}: unsupported category {row.get('category')!r}"
            )
        for field in ("canonical_name_en", "canonical_name_tl", "aliases_en", "aliases_tl"):
            value = row.get(field, "")
            names = [value.strip()] if field.startswith("canonical") and value.strip() else []
            if field.startswith("aliases"):
                names.extend(alias.strip() for alias in value.split("|") if alias.strip())
            for name in names:
                normalized = normalize_label(name)
                existing = aliases.get(normalized)
                if existing is not None and existing != crop_id:
                    errors.append(
                        f"crop registry row {row_number}: name or alias {name!r} is already "
                        f"assigned to crop {existing!r}"
                    )
                else:
                    aliases[normalized] = crop_id
    return _active_records(rows, "crop registry", errors)


def validate_crop_scope_inventory(
    rows: list[dict[str, str]], registry_rows: list[dict[str, str]], errors: list[str]
) -> set[str]:
    scope_ids: set[str] = set()
    in_scope_ids: set[str] = set()
    source_ids = {"DA-PRICE-MONITORING", "PSA-OPENSTAT-2M4AFN08"}
    for row_number, row in enumerate(rows, start=2):
        scope_id = row.get("scope_id", "").strip()
        if not re.fullmatch(r"[a-z][a-z0-9_]*", scope_id):
            errors.append(f"crop scope row {row_number}: invalid scope_id {scope_id!r}")
        if scope_id in scope_ids:
            errors.append(f"crop scope row {row_number}: duplicate scope_id {scope_id!r}")
        scope_ids.add(scope_id)
        if not row.get("canonical_name_en", "").strip():
            errors.append(f"crop scope row {row_number}: canonical_name_en is required")
        try:
            in_scope = row.get("in_scope", "").strip().lower()
            if in_scope not in {"true", "false"}:
                raise ValueError
        except ValueError:
            errors.append(f"crop scope row {row_number}: in_scope must be true or false")
            in_scope = "false"
        references = {
            value.strip()
            for value in row.get("source_references", "").split("|")
            if value.strip()
        }
        if not references or not references.issubset(source_ids):
            errors.append(
                f"crop scope row {row_number}: source_references must use the declared crop sources"
            )
        if in_scope == "true":
            in_scope_ids.add(scope_id)
            if row.get("exclusion_reason", "").strip():
                errors.append(
                    f"crop scope row {row_number}: included crop cannot have an exclusion reason"
                )
        elif not row.get("exclusion_reason", "").strip():
            errors.append(f"crop scope row {row_number}: excluded crop needs an exclusion reason")
    registry_ids = {
        row.get("crop_id", "").strip()
        for row in registry_rows
        if row.get("active", "").strip().lower() == "true"
    }
    if in_scope_ids != registry_ids:
        errors.append(
            "crop scope inventory and active crop registry disagree: "
            f"inventory_only={sorted(in_scope_ids - registry_ids)}, "
            f"registry_only={sorted(registry_ids - in_scope_ids)}"
        )
    return in_scope_ids


def _provenance_ids(value: str) -> set[str]:
    return {item.strip() for item in value.split("|") if item.strip()}


def _check_provenance(
    value: str, allowed: set[str], label: str, row_number: int, errors: list[str]
) -> None:
    values = _provenance_ids(value)
    if not values or not values.issubset(allowed):
        errors.append(
            f"{label} row {row_number}: malformed provenance IDs; allowed IDs are {sorted(allowed)}"
        )


def validate_geography_registry(
    rows: list[dict[str, str]], errors: list[str]
) -> list[dict[str, str]]:
    identifiers: dict[str, dict[str, str]] = {}
    codes: set[str] = set()
    names_by_parent: set[tuple[str, str, str]] = set()
    ordering: list[tuple[int, str]] = []
    for row_number, row in enumerate(rows, start=2):
        geography_id = row.get("geography_id", "").strip()
        level = row.get("level", "").strip()
        code = row.get("code", "").strip()
        parent_id = row.get("parent_geography_id", "").strip()
        name = row.get("name", "").strip()
        if level not in ALLOWED_LEVELS:
            errors.append(f"geography registry row {row_number}: unsupported level {level!r}")
            continue
        identifier_match = ID_PATTERNS[level].fullmatch(geography_id)
        if not identifier_match or identifier_match.group(1) != code:
            errors.append(
                f"geography registry row {row_number}: {geography_id!r} must use its stable "
                f"PSGC code for level {level!r}"
            )
        if geography_id in identifiers:
            errors.append(
                f"geography registry row {row_number}: duplicate geography_id {geography_id!r}"
            )
        identifiers[geography_id] = row
        if not re.fullmatch(r"\d{10}", code):
            errors.append(f"geography registry row {row_number}: code must be a 10 digit PSGC code")
        if code in codes:
            errors.append(f"geography registry row {row_number}: duplicate PSGC code {code!r}")
        codes.add(code)
        if not name:
            errors.append(f"geography registry row {row_number}: name is required")
        if row.get("country") != "Philippines":
            errors.append(f"geography registry row {row_number}: country must be Philippines")
        if row.get("island_group") != "Luzon":
            errors.append(f"geography registry row {row_number}: island_group must be Luzon")
        scope = (parent_id, level, normalize_label(name))
        if scope in names_by_parent:
            errors.append(
                f"geography registry row {row_number}: duplicate {level} name {name!r} "
                f"within parent {parent_id!r}"
            )
        names_by_parent.add(scope)
        ordering.append(({"region": 0, "province": 1, "municipality_city": 2}[level], code))
        if level == "region" and parent_id:
            errors.append(f"geography registry row {row_number}: a region must not have a parent")
        elif level in {"province", "municipality_city"} and not parent_id:
            errors.append(f"geography registry row {row_number}: {level} must have a parent")

    if ordering != sorted(ordering):
        errors.append("geography registry records must be ordered by level and PSGC code")

    active = _active_records(rows, "geography registry", errors)
    for row_number, row in enumerate(active, start=2):
        level = row.get("level", "")
        parent_id = row.get("parent_geography_id", "").strip()
        parent = identifiers.get(parent_id)
        if level == "region":
            continue
        if parent is None:
            errors.append(
                f"geography registry row {row_number}: dangling parent_geography_id {parent_id!r}"
            )
            continue
        if level == "province" and parent.get("level") != "region":
            errors.append(f"geography registry row {row_number}: province parent must be a region")
        elif level == "municipality_city":
            valid_province_parent = parent.get("level") == "province"
            valid_ncr_parent = (
                parent.get("level") == "region" and parent.get("code") == "1300000000"
            )
            if not (valid_province_parent or valid_ncr_parent):
                errors.append(
                    f"geography registry row {row_number}: municipality/city parent must be a "
                    "province, except for direct NCR children"
                )
    return active


def _check_unique(
    rows: list[dict[str, str]],
    key_fields: tuple[str, ...],
    label: str,
    errors: list[str],
) -> set[tuple[str, ...]]:
    found: set[tuple[str, ...]] = set()
    for row_number, row in enumerate(rows, start=2):
        key = tuple(row.get(field, "") for field in key_fields)
        if key in found:
            errors.append(f"{label} row {row_number}: duplicate natural key {key!r}")
        found.add(key)
    return found


def _check_dataset_rows(
    rows: list[dict[str, str]],
    crop_ids: set[str],
    geography_by_id: dict[str, dict[str, str]],
    version: str,
    label: str,
    errors: list[str],
) -> None:
    for row_number, row in enumerate(rows, start=2):
        if row.get("crop_id") not in crop_ids:
            errors.append(
                f"{label} row {row_number}: unknown or inactive crop_id {row.get('crop_id')!r}"
            )
        geography_id = row.get("geography_id")
        if geography_id is not None and geography_id not in geography_by_id:
            errors.append(
                f"{label} row {row_number}: unknown or inactive geography_id {geography_id!r}"
            )
        if row.get("data_kind") != DATA_KIND:
            errors.append(f"{label} row {row_number}: data_kind must be {DATA_KIND!r}")
        if row.get("dataset_version") != version:
            errors.append(f"{label} row {row_number}: dataset_version must match {version!r}")


def _parse_iso_date(value: str, label: str, row_number: int, errors: list[str]) -> date | None:
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError):
        errors.append(f"{label} row {row_number}: {value!r} is not an ISO date")
        return None
    if parsed.isoformat() != value:
        errors.append(f"{label} row {row_number}: {value!r} is not a canonical ISO date")
    return parsed


def _verify_scenarios(
    scenarios_path: Path,
    active_crop_ids: set[str],
    geography_by_id: dict[str, dict[str, str]],
    reference_by_key: dict[tuple[str, str, str, str], str],
    snapshot_by_key: dict[tuple[str, str, str, str], str],
    periods: set[tuple[str, str]],
    thresholds: dict[str, float],
    errors: list[str],
) -> None:
    if not scenarios_path.is_file():
        errors.append(f"required demo fixture file is missing: {scenarios_path}")
        return
    try:
        payload = load_json(scenarios_path)
        if not isinstance(payload, dict):
            errors.append(f"demo fixtures must be a JSON object: {scenarios_path}")
            return
        scenarios = payload.get("scenarios", [])
    except (OSError, json.JSONDecodeError, AttributeError) as error:
        errors.append(f"cannot read demo fixtures {scenarios_path}: {error}")
        return
    if not isinstance(scenarios, list):
        errors.append("demo fixture scenarios must be a list")
        return
    if not scenarios:
        errors.append("demo fixture file has no scenarios")
        return

    scenario_ids: set[str] = set()
    by_crop: dict[str, dict[str, Any]] = {}
    for index, scenario in enumerate(scenarios, start=1):
        label = f"demo scenario row {index}"
        if not isinstance(scenario, dict):
            errors.append(f"{label}: scenario must be an object")
            continue
        scenario_id = scenario.get("scenario_id", "")
        if not isinstance(scenario_id, str) or not scenario_id:
            errors.append(f"{label}: scenario_id is missing or duplicated")
        elif scenario_id in scenario_ids:
            errors.append(f"{label}: scenario_id is missing or duplicated")
        else:
            scenario_ids.add(scenario_id)
        crop_id = scenario.get("crop_id")
        geography_id = scenario.get("geography_id")
        if not isinstance(crop_id, str):
            errors.append(f"{label}: crop_id must be a string")
            crop_id = None
        if crop_id not in active_crop_ids:
            errors.append(f"{label}: crop_id {crop_id!r} is not active")
        if not isinstance(geography_id, str):
            errors.append(f"{label}: geography_id must be a string")
            geography_id = None
        geography = geography_by_id.get(geography_id)
        if geography is None or geography.get("level") != "municipality_city":
            errors.append(f"{label}: geography_id must identify a supported municipality or city")
        if scenario.get("data_kind") != DATA_KIND:
            errors.append(f"{label}: data_kind must be {DATA_KIND!r}")
        if scenario.get("period_kind") != "future_planning":
            errors.append(f"{label}: period_kind must be 'future_planning'")
        start_value = scenario.get("period_start", "")
        end_value = scenario.get("period_end", "")
        if not isinstance(start_value, str) or not isinstance(end_value, str):
            errors.append(f"{label}: period_start and period_end must be strings")
            start_value = end_value = ""
        start = _parse_iso_date(start_value, label, index + 1, errors)
        end = _parse_iso_date(end_value, label, index + 1, errors)
        if start and end and start > end:
            errors.append(f"{label}: period_end is before period_start")
        if (start_value, end_value) not in periods:
            errors.append(f"{label}: period is outside the supported future planning horizon")
        try:
            existing_area = float(scenario["existing_planned_area_ha"])
            proposed_area = float(scenario["proposed_future_plan_area_ha"])
            reference_area = float(scenario["reference_area_ha"])
            projected_area = float(scenario["projected_area_ha"])
            expected_ratio = float(scenario["expected_future_ratio"])
            values = [existing_area, proposed_area, reference_area, projected_area, expected_ratio]
            if not all(math.isfinite(value) for value in values):
                raise ValueError("scenario contains a non-finite number")
            if existing_area < 0 or proposed_area < 0 or reference_area <= 0:
                errors.append(
                    f"{label}: areas must be non-negative and reference area must be positive"
                )
            if not math.isclose(projected_area, existing_area + proposed_area, abs_tol=1e-9):
                errors.append(f"{label}: projected_area_ha must equal existing plus proposed area")
            actual_ratio = round(projected_area / reference_area, 6)
            if not math.isclose(actual_ratio, expected_ratio, abs_tol=0.0000005):
                errors.append(
                    f"{label}: expected_future_ratio does not match projected/reference area"
                )
            expected_risk = classify_snapshot_ratio(actual_ratio, thresholds)
            if scenario.get("expected_future_risk") != expected_risk:
                errors.append(f"{label}: expected_future_risk must be {expected_risk!r}")
            reference_key = (crop_id, geography_id, start_value, end_value)
            generated_reference = reference_by_key.get(reference_key)
            if generated_reference is None or not math.isclose(
                float(generated_reference), reference_area, abs_tol=0.0000001
            ):
                errors.append(f"{label}: reference_area_ha does not match generated reference data")
            generated_snapshot = snapshot_by_key.get(reference_key)
            if generated_snapshot is None or not math.isclose(
                float(generated_snapshot), existing_area, abs_tol=0.0000001
            ):
                errors.append(
                    f"{label}: existing_planned_area_ha does not match generated supply context"
                )
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
            errors.append(f"{label}: invalid numeric values ({error})")
        if crop_id and crop_id not in by_crop:
            by_crop[crop_id] = scenario

    def expected_fixture_values(row: dict[str, Any]) -> tuple[Any, ...] | None:
        try:
            return (
                float(row["existing_planned_area_ha"]),
                float(row["proposed_future_plan_area_ha"]),
                float(row["reference_area_ha"]),
                float(row["projected_area_ha"]),
                float(row["expected_future_ratio"]),
                row["expected_future_risk"],
            )
        except (KeyError, TypeError, ValueError):
            return None

    tomato = by_crop.get("tomato")
    if tomato is None:
        errors.append("demo fixtures must include the tomato Phase 3 scenario")
    else:
        expected_tomato = (32.0, 8.0, 25.0, 40.0, 1.6, "high")
        actual_tomato = expected_fixture_values(tomato)
        if actual_tomato is None:
            errors.append("tomato fixture is missing valid numeric values or expected risk")
        elif actual_tomato != expected_tomato:
            errors.append("tomato fixture must define 32 + 8 ha against 25 ha, ratio 1.60, high")
    eggplant = by_crop.get("eggplant")
    if eggplant is None:
        errors.append("demo fixtures must include a lower-pressure eggplant alternative")
    else:
        expected_eggplant = (12.0, 0.0, 18.0, 12.0, 0.666667, "low")
        actual_eggplant = expected_fixture_values(eggplant)
        if actual_eggplant is None:
            errors.append("eggplant fixture is missing valid numeric values or expected risk")
        elif actual_eggplant != expected_eggplant:
            errors.append(
                "eggplant fixture must define 12 ha against 18 ha, ratio about 0.666667, low"
            )


def validate_dataset(
    crops_path: Path = DEFAULT_CROPS,
    geographies_path: Path = DEFAULT_GEOGRAPHIES,
    config_path: Path = DEFAULT_CONFIG,
    dataset_dir: Path | None = None,
    scenarios_path: Path | None = DEFAULT_SCENARIOS,
    check_determinism: bool = False,
    crop_scope_path: Path | None = None,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    try:
        config = load_json(config_path)
        crop_fields, crops = read_csv_document(crops_path)
        geography_fields, geographies = read_csv_document(geographies_path)
    except (OSError, json.JSONDecodeError) as error:
        return [f"cannot load foundation input: {error}"], {}
    if not isinstance(config, dict):
        return ["dataset configuration must be a JSON object"], {}
    _missing_fields(crop_fields, CROP_FIELDS, "crop registry", errors)
    _missing_fields(geography_fields, GEOGRAPHY_FIELDS, "geography registry", errors)
    active_crops = validate_crop_registry(crops, errors)
    scope_path = crop_scope_path
    if scope_path is None and crops_path.resolve() == DEFAULT_CROPS.resolve():
        scope_path = DEFAULT_CROP_SCOPE
    scope_ids: set[str] = {row.get("crop_id", "") for row in active_crops}
    if scope_path is not None:
        if not scope_path.is_file():
            errors.append(f"required crop scope inventory is missing: {scope_path}")
        else:
            try:
                scope_fields, scope_rows = read_csv_document(scope_path)
                _missing_fields(scope_fields, CROP_SCOPE_FIELDS, "crop scope inventory", errors)
                scope_ids = validate_crop_scope_inventory(scope_rows, crops, errors)
            except (OSError, csv.Error) as error:
                errors.append(f"cannot read crop scope inventory: {error}")
    active_geographies = validate_geography_registry(geographies, errors)
    if not active_crops:
        errors.append("crop registry must contain at least one active crop")
    active_crop_ids = {row["crop_id"] for row in active_crops}
    if scope_path is not None and scope_ids != active_crop_ids:
        errors.append("active crop coverage must be defined by the crop scope inventory")
    active_geography_by_id = {row["geography_id"]: row for row in active_geographies}
    active_municipalities = [
        row for row in active_geographies if row["level"] == "municipality_city"
    ]
    active_provinces = [row for row in active_geographies if row["level"] == "province"]
    active_regions = [row for row in active_geographies if row["level"] == "region"]
    markets = [
        *active_provinces,
        *(row for row in active_regions if row.get("code") == "1300000000"),
    ]
    version = str(config.get("dataset_version", ""))
    try:
        current_period = current_supply_period(config)
        future_periods = quarter_periods(config)
        configured_supply_periods = supply_periods(config)
        months = price_months(config)
    except (KeyError, TypeError, ValueError) as error:
        errors.append(f"invalid dataset configuration: {error}")
        current_period = ("", "")
        future_periods = []
        configured_supply_periods = []
        months = []
    thresholds = config.get("snapshot_thresholds", {})
    try:
        low_threshold = float(thresholds["low_below"])
        high_threshold = float(thresholds["high_above"])
        if not (
            math.isfinite(low_threshold)
            and math.isfinite(high_threshold)
            and low_threshold < high_threshold
        ):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        errors.append("snapshot_thresholds must define finite low_below < high_above values")
        thresholds = {"low_below": 0.9, "high_above": 1.1}

    target = dataset_dir or GENERATED_ROOT / version
    metadata_path = target / "metadata.json"
    if not metadata_path.is_file():
        errors.append(f"generated dataset metadata is missing: {metadata_path}")
        return errors, {}
    try:
        metadata = load_json(metadata_path)
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"cannot read generated dataset metadata: {error}")
        return errors, {}
    if not isinstance(metadata, dict):
        errors.append("generated dataset metadata must be a JSON object")
        return errors, {}
    if metadata.get("dataset_version") != version:
        errors.append("metadata dataset_version does not match data/dataset_config.json")
    if metadata.get("seed") != config.get("seed"):
        errors.append("metadata seed does not match data/dataset_config.json")
    if metadata.get("data_kind") != DATA_KIND:
        errors.append(f"metadata data_kind must be {DATA_KIND!r}")
    input_checksums = metadata.get("input_sha256", {})
    if not isinstance(input_checksums, dict):
        errors.append("metadata input_sha256 must be an object")
        input_checksums = {}
    if input_checksums.get("crops.csv") != sha256_file(crops_path):
        errors.append("metadata crop registry checksum does not match the canonical crop registry")
    if scope_path is not None and scope_path.is_file():
        if input_checksums.get("crop_scope_inventory.csv") != sha256_file(scope_path):
            errors.append("metadata crop scope checksum does not match the crop scope inventory")
    if input_checksums.get("geographies.csv") != sha256_file(geographies_path):
        errors.append(
            "metadata geography registry checksum does not match the canonical geography registry"
        )
    if scenarios_path is not None and scenarios_path.is_file():
        if input_checksums.get("demo_scenarios.json") != sha256_file(scenarios_path):
            errors.append(
                "metadata demo scenario checksum does not match data/seeds/demo_scenarios.json"
            )
    declared_scope = metadata.get("geographic_scope", {})
    if not isinstance(declared_scope, dict):
        errors.append("metadata geographic_scope must be an object")
        declared_scope = {}
    if (
        declared_scope.get("country") != "Philippines"
        or declared_scope.get("island_group") != "Luzon"
    ):
        errors.append("metadata geographic_scope must be the Philippines and Luzon")
    if declared_scope.get("barangay_level_included") is not False:
        errors.append("metadata must declare that barangay-level records are not included")
    canonical_units = metadata.get("canonical_units", {})
    if not isinstance(canonical_units, dict):
        errors.append("metadata canonical_units must be an object")
        canonical_units = {}
    if canonical_units.get("price_history") != {
        "currency": "PHP",
        "unit": "PHP/kg",
    }:
        errors.append("metadata price unit must be PHP/kg")
    counts = declared_scope.get("counts", {})
    if not isinstance(counts, dict):
        errors.append("metadata geographic_scope counts must be an object")
        counts = {}
    expected_counts = {
        "active_crops": len(active_crops),
        "regions": len(active_regions),
        "provinces": len(active_provinces),
        "municipalities_cities": len(active_municipalities),
    }
    if counts != expected_counts:
        errors.append(
            f"metadata coverage counts do not match registries: expected {expected_counts}"
        )
    metadata_periods = metadata.get("periods", {})
    if not isinstance(metadata_periods, dict):
        errors.append("metadata periods must be an object")
        metadata_periods = {}
    current_metadata = metadata_periods.get("current_supply", {})
    if not isinstance(current_metadata, dict):
        current_metadata = {}
    if (
        current_metadata.get("period_start") != current_period[0]
        or current_metadata.get("period_end") != current_period[1]
    ):
        errors.append("metadata current supply period does not match dataset_config.json")
    metadata_future = metadata_periods.get("future_planning", {})
    if not isinstance(metadata_future, dict):
        metadata_future = {}
    expected_future_rows = [
        {"period_start": start, "period_end": end, "period_kind": "future_planning"}
        for start, end in future_periods
    ]
    if metadata_future.get("periods") != expected_future_rows:
        errors.append("metadata future planning periods do not match dataset_config.json")
    time_contract = metadata.get("time_contract", {})
    current_contract = (
        time_contract.get("current_supply_period", {})
        if isinstance(time_contract, dict)
        else {}
    )
    if not isinstance(current_contract, dict):
        current_contract = {}
    if (
        not isinstance(time_contract, dict)
        or current_contract.get("kind") != "current_supply"
    ):
        errors.append("metadata must declare a current_supply time contract")
    horizon = (
        time_contract.get("future_planning_horizon", {})
        if isinstance(time_contract, dict)
        else {}
    )
    if not isinstance(horizon, dict):
        horizon = {}
    configured_horizon = config.get("periods", {}).get("future_planning", {})
    if (
        horizon.get("start") != configured_horizon.get("start")
        or horizon.get("end") != configured_horizon.get("end")
    ):
        errors.append("metadata future planning horizon does not match dataset_config.json")
    provenance = metadata.get("provenance", {})
    if not isinstance(provenance, dict):
        errors.append("metadata provenance must be an object")
    else:
        required_provenance_tables = {
            "crop_profiles",
            "price_history",
            "crop_references",
            "supply_snapshots",
            "soil_suitability",
        }
        if not required_provenance_tables.issubset(provenance):
            errors.append("metadata provenance must document every generated dataset")
        expected_metadata_sources = {
            "crop_profiles": ALLOWED_PROVENANCE["profile"],
            "price_history": ALLOWED_PROVENANCE["price"],
            "crop_references": ALLOWED_PROVENANCE["reference"],
            "supply_snapshots": (
                ALLOWED_PROVENANCE["current_supply"]
                | ALLOWED_PROVENANCE["future_supply"]
            ),
            "soil_suitability": ALLOWED_PROVENANCE["soil"],
        }
        for table_name, allowed_sources in expected_metadata_sources.items():
            entry = provenance.get(table_name, {})
            source_values = entry.get("source_ids", []) if isinstance(entry, dict) else []
            if not isinstance(source_values, list) or not set(source_values).issubset(
                allowed_sources
            ):
                errors.append(f"metadata provenance has invalid source IDs for {table_name}")

    expected_files = {
        "crop_profiles.csv": PROFILE_FIELDS,
        "price_history.csv": PRICE_FIELDS,
        "crop_references.csv": REFERENCE_FIELDS,
        "supply_snapshots.csv": SNAPSHOT_FIELDS,
        "soil_suitability.csv": SUITABILITY_FIELDS,
    }
    manifest = metadata.get("files", {})
    if not isinstance(manifest, dict):
        errors.append("metadata files manifest must be an object")
        manifest = {}
    if set(manifest) != set(expected_files):
        errors.append("metadata files manifest does not list the required generated CSV files")
    actual_files = {
        path.name for path in target.iterdir() if path.is_file() and path.name != "metadata.json"
    }
    if actual_files != set(expected_files):
        errors.append(
            "generated directory contains an unexpected file set: "
            f"expected {sorted(expected_files)}, "
            f"found {sorted(actual_files)}"
        )

    tables: dict[str, list[dict[str, str]]] = {}
    for filename, required_fields in expected_files.items():
        path = target / filename
        if not path.is_file():
            errors.append(f"required generated file is missing: {path}")
            tables[filename] = []
            continue
        try:
            fields, rows = read_csv_document(path)
        except (OSError, csv.Error) as error:
            errors.append(f"cannot read {filename}: {error}")
            tables[filename] = []
            continue
        if fields != required_fields:
            errors.append(f"{filename} columns do not match the canonical field contract")
        tables[filename] = rows
        entry = manifest.get(filename, {})
        if not isinstance(entry, dict):
            errors.append(f"{filename} manifest entry must be an object")
            entry = {}
        if entry.get("row_count") != len(rows):
            errors.append(f"{filename} row count does not match metadata manifest")
        if entry.get("sha256") != sha256_file(path):
            errors.append(f"{filename} checksum does not match metadata manifest")

    for filename, rows in tables.items():
        _check_dataset_rows(
            rows, active_crop_ids, active_geography_by_id, version, filename, errors
        )

    profiles = tables["crop_profiles.csv"]
    profile_keys = _check_unique(profiles, ("crop_id",), "crop_profiles.csv", errors)
    if {key[0] for key in profile_keys} != active_crop_ids:
        errors.append("crop profile coverage must include every active crop exactly once")
    for row in profiles:
        for field in (
            "summary_en",
            "summary_tl",
            "growing_conditions_en",
            "growing_conditions_tl",
            "soil_notes_en",
            "soil_notes_tl",
        ):
            if not row.get(field, "").strip():
                errors.append(f"crop_profiles.csv has an empty required profile field: {field}")
    for row_number, row in enumerate(profiles, start=2):
        _check_provenance(
            row.get("reference_sources", ""),
            ALLOWED_PROVENANCE["profile"],
            "crop_profiles.csv",
            row_number,
            errors,
        )
    if len({row.get("summary_en", "") for row in profiles}) < min(3, len(active_crop_ids)):
        errors.append("crop profiles must contain crop-specific overview text")

    prices = tables["price_history.csv"]
    price_keys = _check_unique(
        prices, ("crop_id", "geography_id", "date", "dataset_version"), "price_history.csv", errors
    )
    expected_price_keys = {
        (crop_id, geography["geography_id"], month_value, version)
        for crop_id in active_crop_ids
        for geography in markets
        for month_value in months
    }
    if price_keys != expected_price_keys:
        errors.append(
            "price history must cover every active crop, province/NCR market, and configured month "
            f"({len(expected_price_keys)} rows expected, {len(price_keys)} natural keys found)"
        )
    previous_price_key: tuple[str, str, str] | None = None
    valid_price_dates: dict[tuple[str, str], list[date]] = {}
    for row_number, row in enumerate(prices, start=2):
        _check_provenance(
            row.get("reference_sources", ""),
            ALLOWED_PROVENANCE["price"],
            "price_history.csv",
            row_number,
            errors,
        )
        geography = active_geography_by_id.get(row.get("geography_id", ""))
        if geography and geography.get("level") not in {"province", "region"}:
            errors.append(
                f"price_history.csv row {row_number}: prices must use province/NCR geographies"
            )
        if row.get("currency") != "PHP" or row.get("price_unit") != "PHP/kg":
            errors.append(f"price_history.csv row {row_number}: price unit must be PHP/kg")
        parsed_date = _parse_iso_date(row.get("date", ""), "price_history.csv", row_number, errors)
        if parsed_date:
            date_key = (row.get("crop_id", ""), row.get("geography_id", ""))
            valid_price_dates.setdefault(date_key, []).append(parsed_date)
        raw_price = row.get("price_php_per_kg", "")
        if not is_finite_number(raw_price) or float(raw_price) < 0 or float(raw_price) > 1000:
            errors.append(
                f"price_history.csv row {row_number}: price must be finite and between "
                "0 and 1000 PHP/kg"
            )
        order_key = (row.get("crop_id", ""), row.get("geography_id", ""), row.get("date", ""))
        if previous_price_key is not None and order_key < previous_price_key:
            errors.append("price_history.csv must be ordered by crop, geography, and date")
        previous_price_key = order_key
    for date_key, values in valid_price_dates.items():
        if values != sorted(values):
            errors.append(f"price history dates are not chronological for {date_key!r}")

    references = tables["crop_references.csv"]
    reference_keys = _check_unique(
        references,
        ("crop_id", "geography_id", "period_start", "period_end", "dataset_version"),
        "crop_references.csv",
        errors,
    )
    expected_reference_keys = {
        (crop_id, geography["geography_id"], start, end, version)
        for crop_id in active_crop_ids
        for geography in active_municipalities
        for start, end, _kind in configured_supply_periods
    }
    if reference_keys != expected_reference_keys:
        errors.append(
            "reference supply must cover every active crop, municipality/city, and period "
            f"({len(expected_reference_keys)} rows expected, "
            f"{len(reference_keys)} natural keys found)"
        )
    reference_by_key: dict[tuple[str, str, str, str], str] = {}
    period_lookup = {(start, end) for start, end, _kind in configured_supply_periods}
    period_kind_lookup = {
        (start, end): kind for start, end, kind in configured_supply_periods
    }
    for row_number, row in enumerate(references, start=2):
        start = _parse_iso_date(
            row.get("period_start", ""), "crop_references.csv", row_number, errors
        )
        end = _parse_iso_date(row.get("period_end", ""), "crop_references.csv", row_number, errors)
        if start and end and start > end:
            errors.append(
                f"crop_references.csv row {row_number}: period_end is before period_start"
            )
        period_key = (row.get("period_start"), row.get("period_end"))
        if period_key not in period_lookup:
            errors.append(
                f"crop_references.csv row {row_number}: period is outside the "
                "supported time contract"
            )
        elif row.get("period_kind") != period_kind_lookup[period_key]:
            errors.append(
                f"crop_references.csv row {row_number}: period_kind must be "
                f"{period_kind_lookup[period_key]!r}"
            )
        if row.get("area_unit") != "ha":
            errors.append(f"crop_references.csv row {row_number}: area_unit must be ha")
        value = row.get("reference_area_ha", "")
        if not is_finite_number(value) or float(value) <= 0:
            errors.append(
                f"crop_references.csv row {row_number}: reference_area_ha must be finite "
                "and positive"
            )
        _check_provenance(
            row.get("reference_sources", ""),
            ALLOWED_PROVENANCE["reference"],
            "crop_references.csv",
            row_number,
            errors,
        )
        reference_by_key[
            (
                row.get("crop_id", ""),
                row.get("geography_id", ""),
                row.get("period_start", ""),
                row.get("period_end", ""),
            )
        ] = value

    snapshots = tables["supply_snapshots.csv"]
    snapshot_keys = _check_unique(
        snapshots,
        ("crop_id", "geography_id", "period_start", "period_end", "dataset_version"),
        "supply_snapshots.csv",
        errors,
    )
    if snapshot_keys != expected_reference_keys:
        errors.append(
            "supply snapshots must cover every active crop, municipality/city, and period "
            f"({len(expected_reference_keys)} rows expected, "
            f"{len(snapshot_keys)} natural keys found)"
        )
    snapshot_by_key: dict[tuple[str, str, str, str], str] = {}
    for row_number, row in enumerate(snapshots, start=2):
        start = _parse_iso_date(
            row.get("period_start", ""), "supply_snapshots.csv", row_number, errors
        )
        end = _parse_iso_date(row.get("period_end", ""), "supply_snapshots.csv", row_number, errors)
        if start and end and start > end:
            errors.append(
                f"supply_snapshots.csv row {row_number}: period_end is before period_start"
            )
        period_key = (row.get("period_start"), row.get("period_end"))
        if period_key not in period_lookup:
            errors.append(
                f"supply_snapshots.csv row {row_number}: period is outside the "
                "supported time contract"
            )
        else:
            expected_kind = period_kind_lookup[period_key]
            if row.get("period_kind") != expected_kind:
                errors.append(
                    f"supply_snapshots.csv row {row_number}: period_kind must be {expected_kind!r}"
                )
            provenance_key = (
                "current_supply" if expected_kind == "current_supply" else "future_supply"
            )
            _check_provenance(
                row.get("reference_sources", ""),
                ALLOWED_PROVENANCE[provenance_key],
                "supply_snapshots.csv",
                row_number,
                errors,
            )
        if row.get("area_unit") != "ha":
            errors.append(f"supply_snapshots.csv row {row_number}: area_unit must be ha")
        if row.get("risk_level") not in ALLOWED_RISKS:
            errors.append(
                f"supply_snapshots.csv row {row_number}: invalid risk_level "
                f"{row.get('risk_level')!r}"
            )
        planned = row.get("planned_area_ha", "")
        reference = row.get("reference_area_ha", "")
        ratio = row.get("ratio", "")
        if not is_finite_number(planned) or float(planned) < 0:
            errors.append(
                f"supply_snapshots.csv row {row_number}: planned_area_ha must be finite "
                "and non-negative"
            )
        if not is_finite_number(reference) or float(reference) <= 0:
            errors.append(
                f"supply_snapshots.csv row {row_number}: reference_area_ha must be finite "
                "and positive"
            )
        if not is_finite_number(ratio) or float(ratio) < 0:
            errors.append(
                f"supply_snapshots.csv row {row_number}: ratio must be finite and non-negative"
            )
        if is_finite_number(planned) and is_finite_number(reference) and float(reference) > 0:
            expected_ratio = round(float(planned) / float(reference), 6)
            if not is_finite_number(ratio) or not math.isclose(
                float(ratio), expected_ratio, abs_tol=0.0000005
            ):
                errors.append(
                    f"supply_snapshots.csv row {row_number}: ratio does not equal "
                    "planned/reference area"
                )
            else:
                expected_risk = classify_snapshot_ratio(expected_ratio, thresholds)
                if row.get("risk_level") != expected_risk:
                    errors.append(
                        f"supply_snapshots.csv row {row_number}: risk_level must be "
                        f"{expected_risk!r} "
                        "for the documented snapshot thresholds"
                    )
        key = (
            row.get("crop_id", ""),
            row.get("geography_id", ""),
            row.get("period_start", ""),
            row.get("period_end", ""),
        )
        snapshot_by_key[key] = planned
        matching_reference = reference_by_key.get(key)
        if matching_reference is None or matching_reference != reference:
            errors.append(
                f"supply_snapshots.csv row {row_number}: reference area does not match "
                "reference data"
            )

    suitability = tables["soil_suitability.csv"]
    suitability_keys = _check_unique(
        suitability,
        ("crop_id", "geography_id", "dataset_version"),
        "soil_suitability.csv",
        errors,
    )
    expected_suitability_keys = {
        (crop_id, geography["geography_id"], version)
        for crop_id in active_crop_ids
        for geography in active_municipalities
    }
    if suitability_keys != expected_suitability_keys:
        errors.append(
            "soil suitability must cover every active crop and municipality/city "
            f"({len(expected_suitability_keys)} rows expected, "
            f"{len(suitability_keys)} natural keys found)"
        )
    for row_number, row in enumerate(suitability, start=2):
        if row.get("suitability_class") not in ALLOWED_SUITABILITY:
            errors.append(
                f"soil_suitability.csv row {row_number}: invalid suitability_class "
                f"{row.get('suitability_class')!r}"
            )
        _check_provenance(
            row.get("reference_sources", ""),
            ALLOWED_PROVENANCE["soil"],
            "soil_suitability.csv",
            row_number,
            errors,
        )

    for table_name in ("crop_references.csv", "supply_snapshots.csv", "soil_suitability.csv"):
        for row_number, row in enumerate(tables[table_name], start=2):
            geography = active_geography_by_id.get(row.get("geography_id", ""))
            if geography and geography.get("level") != "municipality_city":
                errors.append(
                    f"{table_name} row {row_number}: map-compatible data must use "
                    "municipality/city IDs"
                )

    if scenarios_path is not None:
        _verify_scenarios(
            scenarios_path,
            active_crop_ids,
            active_geography_by_id,
            reference_by_key,
            snapshot_by_key,
            {(start, end) for start, end in future_periods},
            thresholds,
            errors,
        )

    summary = {
        "dataset_version": version,
        "seed": config.get("seed"),
        "active_crops": len(active_crops),
        "regions": len(active_regions),
        "provinces": len(active_provinces),
        "municipalities_cities": len(active_municipalities),
        "generated_rows": {filename: len(rows) for filename, rows in tables.items()},
        "current_supply_period": current_period,
        "supported_future_planning_periods": future_periods,
        "supported_future_planning_horizon": {
            "start": config.get("periods", {}).get("future_planning", {}).get("start"),
            "end": config.get("periods", {}).get("future_planning", {}).get("end"),
        },
        "path": str(target),
    }
    if check_determinism and not errors:
        try:
            with tempfile.TemporaryDirectory(prefix="tanim-determinism-") as temporary:
                root = Path(temporary)
                first = generate_dataset(
                    crops_path,
                    geographies_path,
                    config_path,
                    root / "first",
                    scenarios_path,
                    False,
                    scope_path,
                )
                second = generate_dataset(
                    crops_path,
                    geographies_path,
                    config_path,
                    root / "second",
                    scenarios_path,
                    False,
                    scope_path,
                )
                if first["metadata"]["files"] != second["metadata"]["files"]:
                    errors.append("generator determinism check failed: output manifests differ")
                else:
                    for filename in [*first["metadata"]["files"], "metadata.json"]:
                        if sha256_file(first["path"] / filename) != sha256_file(
                            second["path"] / filename
                        ):
                            errors.append(f"generator determinism check failed for {filename}")
                summary["determinism"] = "passed" if not errors else "failed"
        except (OSError, ValueError, KeyError) as error:
            errors.append(f"generator determinism check could not complete: {error}")
            summary["determinism"] = "failed"
    return errors, summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--crop-registry", type=Path, default=DEFAULT_CROPS)
    parser.add_argument("--geography-registry", type=Path, default=DEFAULT_GEOGRAPHIES)
    parser.add_argument("--crop-scope", type=Path, default=DEFAULT_CROP_SCOPE)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--dataset-dir", type=Path)
    parser.add_argument("--check-determinism", action="store_true", default=True)
    parser.add_argument("--skip-determinism", action="store_false", dest="check_determinism")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors, summary = validate_dataset(
        args.crop_registry,
        args.geography_registry,
        args.config,
        args.dataset_dir,
        args.scenarios,
        args.check_determinism,
        args.crop_scope,
    )
    if errors:
        print("TANIM data validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "TANIM data validation passed: "
        f"{summary['active_crops']} crops; {summary['regions']} regions; "
        f"{summary['provinces']} provinces; "
        f"{summary['municipalities_cities']} municipalities/cities; "
        f"dataset {summary['dataset_version']} with seed {summary['seed']}"
    )
    print(f"Generated rows: {summary['generated_rows']}")
    if summary.get("determinism") == "passed":
        print("Determinism check passed (all generated file hashes match).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
