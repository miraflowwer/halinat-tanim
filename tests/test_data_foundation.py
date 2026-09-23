import csv
import json
import re
from pathlib import Path

import pytest

from scripts.data_common import (
    DEFAULT_CROP_SCOPE,
    current_supply_period,
    quarter_periods,
    read_csv_rows,
    sha256_file,
    supply_periods,
    supported_future_period,
    write_csv_rows,
    write_json,
)
from scripts.generate_demo_data import PROVENANCE_IDS, generate_dataset
from scripts.seed_data import SeedError, _seed_version
from scripts.validate_data import _verify_scenarios, validate_crop_scope_inventory, validate_dataset


def _write_minimal_inputs(root: Path, seed: int = 7) -> tuple[Path, Path, Path]:
    crops_path = root / "crops.csv"
    geographies_path = root / "geographies.csv"
    config_path = root / "dataset_config.json"

    write_csv_rows(
        crops_path,
        [
            "crop_id",
            "canonical_name_en",
            "canonical_name_tl",
            "scientific_name",
            "category",
            "aliases_en",
            "aliases_tl",
            "active",
        ],
        [
            {
                "crop_id": "test_crop",
                "canonical_name_en": "Test Crop",
                "canonical_name_tl": "Pananim na Pagsubok",
                "scientific_name": "Testus cropus",
                "category": "vegetable",
                "aliases_en": "",
                "aliases_tl": "",
                "active": "true",
            }
        ],
    )
    write_csv_rows(
        geographies_path,
        [
            "geography_id",
            "name",
            "level",
            "code",
            "parent_geography_id",
            "country",
            "island_group",
            "active",
        ],
        [
            {
                "geography_id": "region_0100000000",
                "name": "Region I",
                "level": "region",
                "code": "0100000000",
                "parent_geography_id": "",
                "country": "Philippines",
                "island_group": "Luzon",
                "active": "true",
            },
            {
                "geography_id": "province_0100100000",
                "name": "Test Province",
                "level": "province",
                "code": "0100100000",
                "parent_geography_id": "region_0100000000",
                "country": "Philippines",
                "island_group": "Luzon",
                "active": "true",
            },
            {
                "geography_id": "mun_0100101000",
                "name": "Test Municipality",
                "level": "municipality_city",
                "code": "0100101000",
                "parent_geography_id": "province_0100100000",
                "country": "Philippines",
                "island_group": "Luzon",
                "active": "true",
            },
        ],
    )
    write_json(
        config_path,
        {
            "dataset_version": "test-v1",
            "seed": seed,
            "generation_version": "1.0.0",
            "periods": {
                "price_start_month": "2025-01",
                "price_month_count": 2,
                "current_supply": {"start": "2024-12-01", "end": "2024-12-31"},
                "future_planning": {
                    "start": "2025-01-01",
                    "end": "2025-03-31",
                    "period_granularity": "quarter",
                    "quarter_starts": ["2025-01-01"],
                },
            },
            "snapshot_thresholds": {"low_below": 0.9, "high_above": 1.1},
        },
    )
    return crops_path, geographies_path, config_path


def test_generator_outputs_validate_and_are_byte_deterministic(tmp_path):
    crops, geographies, config = _write_minimal_inputs(tmp_path)
    first = generate_dataset(crops, geographies, config, tmp_path / "first", scenarios_path=None)
    second = generate_dataset(crops, geographies, config, tmp_path / "second", scenarios_path=None)

    filenames = sorted(path.name for path in first["path"].iterdir())
    assert filenames == sorted(path.name for path in second["path"].iterdir())
    assert all(
        (first["path"] / filename).read_bytes() == (second["path"] / filename).read_bytes()
        for filename in filenames
    )

    errors, summary = validate_dataset(
        crops, geographies, config, first["path"], scenarios_path=None
    )
    assert errors == []
    assert summary["generated_rows"]["price_history.csv"] == 2
    assert summary["generated_rows"]["crop_references.csv"] == 2


def test_canonical_dataset_has_complete_crop_and_geography_coverage():
    errors, summary = validate_dataset(check_determinism=False)

    assert errors == []
    scope_rows = list(csv.DictReader(DEFAULT_CROP_SCOPE.open(encoding="utf-8", newline="")))
    expected_crop_count = sum(row["in_scope"].lower() == "true" for row in scope_rows)
    config = json.loads(Path("data/dataset_config.json").read_text(encoding="utf-8"))
    future_count = len(quarter_periods(config))
    assert summary["active_crops"] == expected_crop_count
    assert summary["regions"] == 8
    assert summary["provinces"] == 38
    assert summary["municipalities_cities"] == 771
    assert summary["generated_rows"]["crop_profiles.csv"] == expected_crop_count
    assert summary["generated_rows"]["price_history.csv"] == expected_crop_count * 1404
    expected_supply_rows = expected_crop_count * 771 * (future_count + 1)
    assert summary["generated_rows"]["crop_references.csv"] == expected_supply_rows
    assert summary["generated_rows"]["supply_snapshots.csv"] == expected_supply_rows
    assert summary["generated_rows"]["soil_suitability.csv"] == expected_crop_count * 771
    assert summary["current_supply_period"] == current_supply_period(config)
    assert len(summary["supported_future_planning_periods"]) == future_count


def test_validation_rejects_a_dangling_geography_parent(tmp_path):
    crops, geographies, config = _write_minimal_inputs(tmp_path)
    generated = generate_dataset(
        crops, geographies, config, tmp_path / "dataset", scenarios_path=None
    )
    rows = []
    with geographies.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    rows[1]["parent_geography_id"] = "region_9900000000"
    write_csv_rows(geographies, list(rows[0]), rows)

    errors, _ = validate_dataset(crops, geographies, config, generated["path"], scenarios_path=None)

    assert any("dangling parent_geography_id" in error for error in errors)


def test_fixture_validation_reports_missing_fields_without_crashing(tmp_path):
    scenarios_path = tmp_path / "scenarios.json"
    write_json(
        scenarios_path,
        {
            "scenarios": [
                {
                    "scenario_id": "tomato_incomplete",
                    "crop_id": "tomato",
                    "geography_id": "mun_0304903000",
                    "period_start": "2027-01-01",
                    "period_end": "2027-03-31",
                    "data_kind": "synthetic_demo",
                }
            ]
        },
    )
    errors = []

    _verify_scenarios(
        scenarios_path,
        {"tomato", "eggplant"},
        {},
        {},
        {},
        {("2027-01-01", "2027-03-31")},
        {"low_below": 0.9, "high_above": 1.1},
        errors,
    )

    assert any("invalid numeric values" in error for error in errors)
    assert any("tomato fixture is missing valid numeric values" in error for error in errors)


def test_generator_does_not_replace_changed_content_without_explicit_flag(tmp_path):
    crops, geographies, config = _write_minimal_inputs(tmp_path)
    target = tmp_path / "dataset"
    first = generate_dataset(crops, geographies, config, target, scenarios_path=None)
    before = (target / "metadata.json").read_bytes()

    _, _, second_config = _write_minimal_inputs(tmp_path / "changed", seed=8)
    with pytest.raises(FileExistsError, match="Choose a new dataset_version"):
        generate_dataset(crops, geographies, second_config, target, scenarios_path=None)

    assert (target / "metadata.json").read_bytes() == before
    assert first["metadata"]["seed"] == 7
    replaced = generate_dataset(
        crops,
        geographies,
        second_config,
        target,
        scenarios_path=None,
        replace=True,
    )
    assert replaced["metadata"]["seed"] == 8
    assert (target / "metadata.json").read_bytes() != before


def test_validation_rejects_a_modified_generated_file(tmp_path):
    crops, geographies, config = _write_minimal_inputs(tmp_path)
    generated = generate_dataset(
        crops, geographies, config, tmp_path / "dataset", scenarios_path=None
    )
    prices_path = generated["path"] / "price_history.csv.gz"
    rows = read_csv_rows(prices_path)
    rows[0]["price_php_per_kg"] = "-1"
    write_csv_rows(
        prices_path,
        list(rows[0]),
        rows,
    )

    errors, _ = validate_dataset(crops, geographies, config, generated["path"], scenarios_path=None)
    assert any("SHA-256" in error or "checksum" in error for error in errors)
    assert any("price must be finite" in error for error in errors)


class ExistingDatasetCursor:
    def __init__(
        self,
        metadata,
        manifest_hash,
        row_counts,
        fingerprints=None,
        stored_fingerprints=None,
    ):
        self.metadata = metadata
        self.manifest_hash = manifest_hash
        self.row_counts = row_counts
        self.fingerprints = fingerprints or {
            "crop_profiles": "profile-fingerprint",
            "price_history": "price-fingerprint",
            "crop_references": "reference-fingerprint",
            "supply_snapshots": "snapshot-fingerprint",
            "soil_suitability": "soil-fingerprint",
            "demo_scenarios": "scenario-fingerprint",
        }
        self.stored_fingerprints = stored_fingerprints or self.fingerprints
        self.row = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, statement, _params=None):
        if "SELECT manifest_sha256, metadata, content_fingerprints" in statement:
            self.row = (self.manifest_hash, self.metadata, self.stored_fingerprints)
            return
        if "SELECT md5(" in statement:
            table = statement.split("FROM", maxsplit=1)[1].split(maxsplit=1)[0]
            self.row = (self.fingerprints[table],)
            return
        if "SELECT count(*) FROM" in statement:
            table = statement.split("FROM", maxsplit=1)[1].split(maxsplit=1)[0]
            self.row = (self.row_counts[table],)
            return
        raise AssertionError(f"unexpected SQL in idempotency check: {statement}")

    def fetchone(self):
        return self.row


class ExistingDatasetConnection:
    def __init__(self, cursor):
        self.existing_cursor = cursor
        self.statements = []

    def execute(self, statement, _params=None):
        self.statements.append(statement)

    def cursor(self):
        return self.existing_cursor


def test_seeder_skips_a_matching_dataset_version_without_writes(tmp_path):
    metadata = {
        "dataset_version": "test-v1",
        "data_kind": "synthetic_demo",
        "seed": 7,
        "files": {
            "crop_profiles.csv.gz": {"row_count": 1},
            "price_history.csv.gz": {"row_count": 2},
            "crop_references.csv.gz": {"row_count": 1},
            "supply_snapshots.csv.gz": {"row_count": 1},
            "soil_suitability.csv.gz": {"row_count": 1},
        },
    }
    dataset_dir = tmp_path / "dataset"
    write_json(dataset_dir / "metadata.json", metadata)
    counts = {
        "crop_profiles": 1,
        "price_history": 2,
        "crop_references": 1,
        "supply_snapshots": 1,
        "soil_suitability": 1,
        "demo_scenarios": 0,
    }
    cursor = ExistingDatasetCursor(metadata, sha256_file(dataset_dir / "metadata.json"), counts)
    connection = ExistingDatasetConnection(cursor)

    result = _seed_version(connection, dataset_dir, [], [], [], metadata)

    assert result == {"already_seeded": 1}
    assert len(connection.statements) == 1
    assert "pg_advisory_xact_lock" in connection.statements[0]


def test_seeder_rejects_an_incomplete_existing_version(tmp_path):
    metadata = {
        "dataset_version": "test-v1",
        "data_kind": "synthetic_demo",
        "seed": 7,
        "files": {
            "crop_profiles.csv.gz": {"row_count": 1},
            "price_history.csv.gz": {"row_count": 2},
            "crop_references.csv.gz": {"row_count": 1},
            "supply_snapshots.csv.gz": {"row_count": 1},
            "soil_suitability.csv.gz": {"row_count": 1},
        },
    }
    dataset_dir = tmp_path / "dataset"
    write_json(dataset_dir / "metadata.json", metadata)
    counts = {
        "crop_profiles": 1,
        "price_history": 1,
        "crop_references": 1,
        "supply_snapshots": 1,
        "soil_suitability": 1,
        "demo_scenarios": 0,
    }
    cursor = ExistingDatasetCursor(metadata, sha256_file(dataset_dir / "metadata.json"), counts)
    connection = ExistingDatasetConnection(cursor)

    with pytest.raises(SeedError, match="expected 2"):
        _seed_version(connection, dataset_dir, [], [], [], metadata)

    assert len(connection.statements) == 1


def test_seeder_rejects_same_count_modified_content(tmp_path):
    metadata = {
        "dataset_version": "test-v1",
        "data_kind": "synthetic_demo",
        "seed": 7,
        "files": {
            "crop_profiles.csv.gz": {"row_count": 1},
            "price_history.csv.gz": {"row_count": 2},
            "crop_references.csv.gz": {"row_count": 1},
            "supply_snapshots.csv.gz": {"row_count": 1},
            "soil_suitability.csv.gz": {"row_count": 1},
        },
    }
    dataset_dir = tmp_path / "dataset"
    write_json(dataset_dir / "metadata.json", metadata)
    counts = {
        "crop_profiles": 1,
        "price_history": 2,
        "crop_references": 1,
        "supply_snapshots": 1,
        "soil_suitability": 1,
        "demo_scenarios": 0,
    }
    stored = {
        "crop_profiles": "profile-fingerprint",
        "price_history": "original-price-fingerprint",
        "crop_references": "reference-fingerprint",
        "supply_snapshots": "snapshot-fingerprint",
        "soil_suitability": "soil-fingerprint",
        "demo_scenarios": "scenario-fingerprint",
    }
    current = dict(stored)
    current["price_history"] = "modified-price-fingerprint"
    cursor = ExistingDatasetCursor(
        metadata,
        sha256_file(dataset_dir / "metadata.json"),
        counts,
        fingerprints=current,
        stored_fingerprints=stored,
    )
    connection = ExistingDatasetConnection(cursor)

    with pytest.raises(SeedError, match="content fingerprint mismatch"):
        _seed_version(connection, dataset_dir, [], [], [], metadata)


def test_migrations_leave_transaction_control_to_init_db():
    migration_dir = Path("data/migrations")
    for migration in sorted(migration_dir.glob("[0-9][0-9][0-9]_*.sql")):
        sql = migration.read_text(encoding="utf-8").upper()
        assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\s*;", sql), migration
    init_source = Path("scripts/init_db.py").read_text(encoding="utf-8")
    assert "INSERT INTO tanim_schema_migrations" in init_source


def test_crop_scope_inventory_matches_registry():
    crops = list(csv.DictReader(Path("data/registry/crops.csv").open(encoding="utf-8", newline="")))
    scope_rows = list(csv.DictReader(DEFAULT_CROP_SCOPE.open(encoding="utf-8", newline="")))
    errors = []
    scope_ids = validate_crop_scope_inventory(scope_rows, crops, errors)
    assert errors == []
    assert scope_ids == {row["crop_id"] for row in crops if row["active"] == "true"}
    assert len(scope_rows) > len(scope_ids)
    in_scope = {
        row["scope_id"]: row
        for row in scope_rows
        if row["in_scope"].strip().lower() == "true"
    }
    assert {
        "white_potato",
        "chayote",
        "celery",
        "kangkong",
        "radish",
        "habichuelas",
        "patola",
    } <= set(in_scope)
    for crop_id in ("white_potato", "chayote", "celery"):
        assert "DA-AMAS-PM-2026-02-25" in in_scope[crop_id]["source_references"].split("|")
    for crop_id in ("kangkong", "radish", "habichuelas", "patola"):
        assert "PSA-QUEZON-VRC-2025" in in_scope[crop_id]["source_references"].split("|")


def test_time_contract_has_current_period_and_identifies_unsupported_dates():
    config = json.loads(Path("data/dataset_config.json").read_text(encoding="utf-8"))
    assert current_supply_period(config) == ("2026-09-01", "2026-09-30")
    assert len(supply_periods(config)) == 10
    assert supported_future_period(config, "2026-10-01", "2026-12-31")
    assert supported_future_period(config, "2027-01-01", "2027-03-31")
    assert not supported_future_period(config, "2029-01-01", "2029-03-31")


def test_generated_provenance_keeps_price_and_suitability_purposes_separate():
    config = json.loads(Path("data/dataset_config.json").read_text(encoding="utf-8"))
    generated = Path("data/generated") / config["dataset_version"]
    prices = read_csv_rows(generated / "price_history.csv.gz")
    references = read_csv_rows(generated / "crop_references.csv.gz")
    soil = read_csv_rows(generated / "soil_suitability.csv.gz")
    assert set(prices[0]["reference_sources"].split("|")) == {
        "PSA-OPENSTAT-2M4AFN08",
        "DA-PRICE-MONITORING",
    }
    assert {row["reference_sources"] for row in references} == {PROVENANCE_IDS["reference"]}
    assert {row["reference_sources"] for row in soil} == {PROVENANCE_IDS["soil"]}
    assert not any("PSA-OPENSTAT-2M4AFN08" in row["reference_sources"] for row in references)
    assert not any("PSA-OPENSTAT-2M4AFN08" in row["reference_sources"] for row in soil)


def test_generated_supply_periods_and_profiles_are_auditable():
    config = json.loads(Path("data/dataset_config.json").read_text(encoding="utf-8"))
    generated = Path("data/generated") / config["dataset_version"]
    scope_rows = read_csv_rows(DEFAULT_CROP_SCOPE)
    expected_crop_ids = {
        row["scope_id"] for row in scope_rows if row["in_scope"].strip().lower() == "true"
    }
    snapshots = read_csv_rows(generated / "supply_snapshots.csv.gz")
    profiles = read_csv_rows(generated / "crop_profiles.csv.gz")
    current_snapshots = [row for row in snapshots if row["period_kind"] == "current_supply"]
    assert {row["period_kind"] for row in snapshots} == {"current_supply", "future_planning"}
    assert len(current_snapshots) == len(expected_crop_ids) * 771
    assert {row["crop_id"] for row in current_snapshots} == expected_crop_ids
    assert {row["crop_id"] for row in profiles} == expected_crop_ids
    assert len({row["summary_en"] for row in profiles}) == len(expected_crop_ids)
    assert len({row["growing_conditions_en"] for row in profiles}) >= 20


def test_suitability_generation_is_repeatable(tmp_path):
    crops, geographies, config = _write_minimal_inputs(tmp_path)
    first = generate_dataset(crops, geographies, config, tmp_path / "first", scenarios_path=None)
    second = generate_dataset(crops, geographies, config, tmp_path / "second", scenarios_path=None)
    assert (first["path"] / "soil_suitability.csv.gz").read_bytes() == (
        second["path"] / "soil_suitability.csv.gz"
    ).read_bytes()


def test_validator_rejects_malformed_provenance(tmp_path):
    crops, geographies, config = _write_minimal_inputs(tmp_path)
    generated = generate_dataset(
        crops, geographies, config, tmp_path / "dataset", scenarios_path=None
    )
    soil_path = generated["path"] / "soil_suitability.csv.gz"
    rows = read_csv_rows(soil_path)
    rows[0]["reference_sources"] = "PSA-OPENSTAT-2M4AFN08"
    write_csv_rows(soil_path, list(rows[0]), rows)
    errors, _ = validate_dataset(crops, geographies, config, generated["path"], scenarios_path=None)
    assert any("soil_suitability.csv row" in error and "provenance" in error for error in errors)
