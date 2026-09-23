"""Validate and load one generated TANIM data version into PostgreSQL."""

import argparse
import os
import sys
from collections.abc import Iterable, Iterator
from itertools import islice
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
        load_json,
        read_csv_rows,
        sha256_file,
    )
    from scripts.validate_data import validate_dataset
else:
    from data_common import (
        DEFAULT_CONFIG,
        DEFAULT_CROP_SCOPE,
        DEFAULT_CROPS,
        DEFAULT_GEOGRAPHIES,
        DEFAULT_SCENARIOS,
        GENERATED_ROOT,
        load_json,
        read_csv_rows,
        sha256_file,
    )
    from validate_data import validate_dataset

ROOT = Path(__file__).resolve().parents[1]
BATCH_SIZE = 1000


class SeedError(RuntimeError):
    """A safe, actionable data seed failure."""


FINGERPRINT_QUERIES = {
    "crop_profiles": """
        SELECT md5(COALESCE(string_agg(
            concat_ws(chr(31), crop_id, dataset_version, summary_en, summary_tl,
                growing_conditions_en, growing_conditions_tl, soil_notes_en, soil_notes_tl,
                data_kind, COALESCE(reference_sources, ''), COALESCE(method_note, '')),
            chr(30) ORDER BY crop_id, dataset_version), ''))
        FROM crop_profiles WHERE dataset_version = %s
    """,
    "price_history": """
        SELECT md5(COALESCE(string_agg(
            concat_ws(chr(31), crop_id, geography_id, price_date, price_php_per_kg,
                currency, price_unit, data_kind, dataset_version, COALESCE(reference_sources, '')),
            chr(30) ORDER BY crop_id, geography_id, price_date, dataset_version), ''))
        FROM price_history WHERE dataset_version = %s
    """,
    "crop_references": """
        SELECT md5(COALESCE(string_agg(
            concat_ws(chr(31), crop_id, geography_id, period_start, period_end, period_kind,
                reference_area_ha, area_unit, data_kind, dataset_version,
                COALESCE(reference_sources, ''), COALESCE(method_note, '')),
            chr(30) ORDER BY crop_id, geography_id, period_start, period_end, dataset_version), ''))
        FROM crop_references WHERE dataset_version = %s
    """,
    "supply_snapshots": """
        SELECT md5(COALESCE(string_agg(
            concat_ws(chr(31), crop_id, geography_id, period_start, period_end, period_kind,
                planned_area_ha, reference_area_ha, area_unit, ratio, risk_level, data_kind,
                dataset_version, COALESCE(reference_sources, ''), COALESCE(method_note, '')),
            chr(30) ORDER BY crop_id, geography_id, period_start, period_end, dataset_version), ''))
        FROM supply_snapshots WHERE dataset_version = %s
    """,
    "soil_suitability": """
        SELECT md5(COALESCE(string_agg(
            concat_ws(chr(31), crop_id, geography_id, suitability_class, data_kind,
                dataset_version, COALESCE(reference_sources, ''), COALESCE(method_note, '')),
            chr(30) ORDER BY crop_id, geography_id, dataset_version), ''))
        FROM soil_suitability WHERE dataset_version = %s
    """,
    "demo_scenarios": """
        SELECT md5(COALESCE(string_agg(
            concat_ws(chr(31), scenario_id, dataset_version, crop_id, geography_id,
                period_start, period_end, period_kind, existing_planned_area_ha,
                proposed_future_plan_area_ha, reference_area_ha, projected_area_ha,
                expected_future_ratio, expected_future_risk, data_kind, fixture_data::text),
            chr(30) ORDER BY scenario_id, dataset_version), ''))
        FROM demo_scenarios WHERE dataset_version = %s
    """,
}


def _database_fingerprints(connection: Any, version: str) -> dict[str, str]:
    fingerprints: dict[str, str] = {}
    with connection.cursor() as cursor:
        for table, statement in FINGERPRINT_QUERIES.items():
            cursor.execute(statement, (version,))
            row = cursor.fetchone()
            fingerprints[table] = row[0] if row else ""
    return fingerprints


def _chunks(values: Iterable[tuple[Any, ...]], size: int) -> Iterator[list[tuple[Any, ...]]]:
    iterator = iter(values)
    while batch := list(islice(iterator, size)):
        yield batch


def _insert_new_rows(connection: Any, statement: str, values: Iterable[tuple[Any, ...]]) -> int:
    inserted = 0
    with connection.cursor() as cursor:
        for batch in _chunks(values, BATCH_SIZE):
            cursor.executemany(statement, batch)
            inserted += len(batch)
    return inserted


def _upsert_crops(connection: Any, crops: list[dict[str, str]]) -> None:
    statement = """
        INSERT INTO crops (
            crop_id, canonical_name_en, canonical_name_tl, scientific_name,
            category, aliases_en, aliases_tl, active
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (crop_id) DO UPDATE SET
            canonical_name_en = EXCLUDED.canonical_name_en,
            canonical_name_tl = EXCLUDED.canonical_name_tl,
            scientific_name = EXCLUDED.scientific_name,
            category = EXCLUDED.category,
            aliases_en = EXCLUDED.aliases_en,
            aliases_tl = EXCLUDED.aliases_tl,
            active = EXCLUDED.active
    """
    values = [
        (
            row["crop_id"],
            row["canonical_name_en"],
            row["canonical_name_tl"] or None,
            row["scientific_name"] or None,
            row["category"],
            [alias for alias in row["aliases_en"].split("|") if alias],
            [alias for alias in row["aliases_tl"].split("|") if alias],
            row["active"].lower() == "true",
        )
        for row in crops
    ]
    with connection.cursor() as cursor:
        cursor.executemany(statement, values)


def _resolve_geography(
    connection: Any,
    row: dict[str, str],
    parent_database_id: int | None,
) -> int:
    values = (
        row["name"],
        row["level"],
        row["code"],
        parent_database_id,
        row["country"],
        row["island_group"],
        row["active"].lower() == "true",
        row["geography_id"],
    )
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM geographies WHERE geography_id = %s", (row["geography_id"],))
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                """
                UPDATE geographies
                SET name = %s, level = %s, code = %s, parent_id = %s,
                    country = %s, island_group = %s, active = %s
                WHERE id = %s
                RETURNING id
                """,
                (*values[:7], existing[0]),
            )
            return cursor.fetchone()[0]

        cursor.execute(
            "SELECT id FROM geographies WHERE level = %s AND code = %s ORDER BY id LIMIT 2",
            (row["level"], row["code"]),
        )
        matching_code = cursor.fetchall()
        if len(matching_code) > 1:
            raise SeedError(f"multiple database geographies use PSGC code {row['code']}")
        if matching_code:
            database_id = matching_code[0][0]
        else:
            cursor.execute(
                """
                SELECT id FROM geographies
                WHERE level = %s AND name = %s AND parent_id IS NOT DISTINCT FROM %s
                ORDER BY id LIMIT 2
                """,
                (row["level"], row["name"], parent_database_id),
            )
            matching_scope = cursor.fetchall()
            if len(matching_scope) > 1:
                raise SeedError(
                    f"multiple database geographies match {row['name']!r} within the same parent"
                )
            if matching_scope:
                database_id = matching_scope[0][0]
            else:
                cursor.execute(
                    """
                    INSERT INTO geographies (
                        name, level, code, parent_id, country, island_group, active, geography_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    values,
                )
                return cursor.fetchone()[0]
        cursor.execute(
            """
            UPDATE geographies
            SET name = %s, level = %s, code = %s, parent_id = %s,
                country = %s, island_group = %s, active = %s, geography_id = %s
            WHERE id = %s
            RETURNING id
            """,
            (*values, database_id),
        )
        return cursor.fetchone()[0]


def _upsert_geographies(connection: Any, geographies: list[dict[str, str]]) -> dict[str, int]:
    resolved: dict[str, int] = {}
    level_order = {"region": 0, "province": 1, "municipality_city": 2}
    ordered = sorted(geographies, key=lambda row: (level_order[row["level"]], row["code"]))
    for row in ordered:
        parent_id = row["parent_geography_id"]
        if parent_id and parent_id not in resolved:
            raise SeedError(
                f"geography registry parent was not seeded before child {row['geography_id']}"
            )
        resolved[row["geography_id"]] = _resolve_geography(
            connection, row, resolved.get(parent_id) if parent_id else None
        )
    return resolved


def _version_exists(
    connection: Any,
    version: str,
    manifest_hash: str,
    metadata: dict[str, Any],
    scenario_count: int,
) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT manifest_sha256, metadata, content_fingerprints "
            "FROM dataset_metadata WHERE dataset_version = %s",
            (version,),
        )
        existing = cursor.fetchone()
        if existing:
            if existing[0] != manifest_hash or existing[1] != metadata:
                raise SeedError(
                    f"dataset version {version} is already registered with different content. "
                    "Create a new dataset_version instead of replacing it."
                )
            expected_tables = {
                "crop_profiles": "crop_profiles.csv.gz",
                "price_history": "price_history.csv.gz",
                "crop_references": "crop_references.csv.gz",
                "supply_snapshots": "supply_snapshots.csv.gz",
                "soil_suitability": "soil_suitability.csv.gz",
            }
            for table, filename in expected_tables.items():
                expected_count = metadata["files"][filename]["row_count"]
                cursor.execute(
                    f"SELECT count(*) FROM {table} WHERE dataset_version = %s",
                    (version,),
                )
                actual_count = cursor.fetchone()[0]
                if actual_count != expected_count:
                    raise SeedError(
                        f"dataset version {version} has {actual_count} rows in {table}, "
                        f"expected {expected_count}. No rows were changed."
                    )
            cursor.execute(
                "SELECT count(*) FROM demo_scenarios WHERE dataset_version = %s",
                (version,),
            )
            if cursor.fetchone()[0] != scenario_count:
                raise SeedError(
                    f"dataset version {version} does not have the expected demo fixture rows. "
                    "No rows were changed."
                )
            expected_fingerprints = existing[2] or {}
            if expected_fingerprints != _database_fingerprints(connection, version):
                raise SeedError(
                    f"dataset version {version} content fingerprint mismatch. "
                    "A same-count record may have changed; no rows were changed."
                )
            return True
    return False


def _ensure_version_rows_absent(connection: Any, version: str) -> None:
    tables = (
        "crop_profiles",
        "price_history",
        "crop_references",
        "supply_snapshots",
        "soil_suitability",
        "demo_scenarios",
    )
    with connection.cursor() as cursor:
        for table in tables:
            cursor.execute(f"SELECT 1 FROM {table} WHERE dataset_version = %s LIMIT 1", (version,))
            if cursor.fetchone():
                raise SeedError(
                    f"dataset version {version} has existing rows in {table} without matching "
                    "dataset metadata. No rows were changed."
                )


def _seed_version(
    connection: Any,
    dataset_dir: Path,
    crops: list[dict[str, str]],
    geographies: list[dict[str, str]],
    scenarios: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> dict[str, int]:
    from psycopg.types.json import Jsonb

    version = metadata["dataset_version"]
    manifest_hash = sha256_file(dataset_dir / "metadata.json")
    connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (f"tanim:{version}",))
    if _version_exists(connection, version, manifest_hash, metadata, len(scenarios)):
        return {"already_seeded": 1}
    _ensure_version_rows_absent(connection, version)

    _upsert_crops(connection, crops)
    database_geographies = _upsert_geographies(connection, geographies)
    connection.execute(
        """
        INSERT INTO dataset_metadata (
            dataset_version, data_kind, seed, manifest_sha256, metadata, content_fingerprints
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            version,
            metadata["data_kind"],
            metadata["seed"],
            manifest_hash,
            Jsonb(metadata),
            Jsonb({}),
        ),
    )

    profiles = read_csv_rows(dataset_dir / "crop_profiles.csv.gz")
    profile_statement = """
        INSERT INTO crop_profiles (
            crop_id, dataset_version, summary_en, summary_tl,
            growing_conditions_en, growing_conditions_tl, soil_notes_en, soil_notes_tl,
            data_kind, reference_sources, method_note
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    profile_count = _insert_new_rows(
        connection,
        profile_statement,
        (
            (
                row["crop_id"],
                row["dataset_version"],
                row["summary_en"],
                row["summary_tl"],
                row["growing_conditions_en"],
                row["growing_conditions_tl"],
                row["soil_notes_en"],
                row["soil_notes_tl"],
                row["data_kind"],
                row["reference_sources"],
                row["method_note"],
            )
            for row in profiles
        ),
    )

    prices = read_csv_rows(dataset_dir / "price_history.csv.gz")
    price_statement = """
        INSERT INTO price_history (
            crop_id, geography_id, price_date, price_php_per_kg, currency, price_unit,
            data_kind, dataset_version, reference_sources
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    price_count = _insert_new_rows(
        connection,
        price_statement,
        (
            (
                row["crop_id"],
                database_geographies[row["geography_id"]],
                row["date"],
                row["price_php_per_kg"],
                row["currency"],
                row["price_unit"],
                row["data_kind"],
                row["dataset_version"],
                row["reference_sources"],
            )
            for row in prices
        ),
    )

    references = read_csv_rows(dataset_dir / "crop_references.csv.gz")
    reference_statement = """
        INSERT INTO crop_references (
            crop_id, geography_id, period_start, period_end, period_kind, reference_area_ha,
            area_unit, data_kind, dataset_version, reference_sources, method_note
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    reference_count = _insert_new_rows(
        connection,
        reference_statement,
        (
            (
                row["crop_id"],
                database_geographies[row["geography_id"]],
                row["period_start"],
                row["period_end"],
                row["period_kind"],
                row["reference_area_ha"],
                row["area_unit"],
                row["data_kind"],
                row["dataset_version"],
                row["reference_sources"],
                row["method_note"],
            )
            for row in references
        ),
    )

    snapshots = read_csv_rows(dataset_dir / "supply_snapshots.csv.gz")
    snapshot_statement = """
        INSERT INTO supply_snapshots (
            crop_id, geography_id, period_start, period_end, period_kind, planned_area_ha,
            reference_area_ha, area_unit, ratio, risk_level, data_kind, dataset_version,
            reference_sources, method_note
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    snapshot_count = _insert_new_rows(
        connection,
        snapshot_statement,
        (
            (
                row["crop_id"],
                database_geographies[row["geography_id"]],
                row["period_start"],
                row["period_end"],
                row["period_kind"],
                row["planned_area_ha"],
                row["reference_area_ha"],
                row["area_unit"],
                row["ratio"],
                row["risk_level"],
                row["data_kind"],
                row["dataset_version"],
                row["reference_sources"],
                row["method_note"],
            )
            for row in snapshots
        ),
    )

    suitability = read_csv_rows(dataset_dir / "soil_suitability.csv.gz")
    suitability_statement = """
        INSERT INTO soil_suitability (
            crop_id, geography_id, suitability_class, data_kind, dataset_version,
            reference_sources, method_note
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    suitability_count = _insert_new_rows(
        connection,
        suitability_statement,
        (
            (
                row["crop_id"],
                database_geographies[row["geography_id"]],
                row["suitability_class"],
                row["data_kind"],
                row["dataset_version"],
                row["reference_sources"],
                row["method_note"],
            )
            for row in suitability
        ),
    )

    scenario_statement = """
        INSERT INTO demo_scenarios (
            scenario_id, dataset_version, crop_id, geography_id, period_start, period_end,
            period_kind,
            existing_planned_area_ha, proposed_future_plan_area_ha, reference_area_ha,
            projected_area_ha, expected_future_ratio, expected_future_risk, data_kind, fixture_data
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    scenario_count = _insert_new_rows(
        connection,
        scenario_statement,
        (
            (
                row["scenario_id"],
                version,
                row["crop_id"],
                database_geographies[row["geography_id"]],
                row["period_start"],
                row["period_end"],
                row["period_kind"],
                row["existing_planned_area_ha"],
                row["proposed_future_plan_area_ha"],
                row["reference_area_ha"],
                row["projected_area_ha"],
                row["expected_future_ratio"],
                row["expected_future_risk"],
                row["data_kind"],
                Jsonb(row),
            )
            for row in scenarios
        ),
    )
    connection.execute(
        "UPDATE dataset_metadata SET content_fingerprints = %s WHERE dataset_version = %s",
        (Jsonb(_database_fingerprints(connection, version)), version),
    )
    return {
        "crop_profiles": profile_count,
        "price_history": price_count,
        "crop_references": reference_count,
        "supply_snapshots": snapshot_count,
        "soil_suitability": suitability_count,
        "demo_scenarios": scenario_count,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--crop-registry", type=Path, default=DEFAULT_CROPS)
    parser.add_argument("--crop-scope", type=Path, default=DEFAULT_CROP_SCOPE)
    parser.add_argument("--geography-registry", type=Path, default=DEFAULT_GEOGRAPHIES)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--dataset-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_json(args.config)
        version = config["dataset_version"]
        dataset_dir = args.dataset_dir or GENERATED_ROOT / version
        errors, summary = validate_dataset(
            args.crop_registry,
            args.geography_registry,
            args.config,
            dataset_dir,
            args.scenarios,
            check_determinism=False,
            crop_scope_path=args.crop_scope,
        )
    except (OSError, KeyError, ValueError) as error:
        print(f"Data seeding stopped: {error}", file=sys.stderr)
        return 1
    if errors:
        print("Data seeding stopped because source data failed validation:")
        for error in errors:
            print(f"- {error}")
        return 1

    try:
        import psycopg
        from dotenv import load_dotenv

        if __package__:
            from scripts.init_db import main as initialize_database
        else:
            from init_db import main as initialize_database
    except ImportError:
        print("Data seeding requires the project Python dependencies in .venv.", file=sys.stderr)
        return 1

    if initialize_database() != 0:
        return 1

    try:
        load_dotenv(ROOT / ".env", override=False)
        database_url = os.getenv("DATABASE_URL", "").strip()
        if not database_url:
            print(
                "Data seeding stopped: DATABASE_URL is not set in .env or the environment.",
                file=sys.stderr,
            )
            return 1
        crops = read_csv_rows(args.crop_registry)
        geographies = read_csv_rows(args.geography_registry)
        scenarios = load_json(args.scenarios)["scenarios"]
        metadata = load_json(dataset_dir / "metadata.json")
        with psycopg.connect(database_url, connect_timeout=5) as connection:
            counts = _seed_version(
                connection,
                dataset_dir,
                crops,
                geographies,
                scenarios,
                metadata,
            )
    except SeedError as error:
        print(f"Data seeding failed: {error}", file=sys.stderr)
        return 1
    except (psycopg.OperationalError, psycopg.Error) as error:
        code = error.sqlstate or "unknown"
        print(
            "Data seeding failed while writing to PostgreSQL "
            f"(SQLSTATE {code}). Check the local database and applied migrations.",
            file=sys.stderr,
        )
        return 1
    except (OSError, KeyError, ValueError) as error:
        print(f"Data seeding failed: {error}", file=sys.stderr)
        return 1

    if counts.get("already_seeded"):
        print(
            f"Dataset {summary['dataset_version']} is already seeded and matches its metadata. "
            "No rows were changed."
        )
    else:
        print(
            f"Seeded dataset {summary['dataset_version']} for "
            f"{summary['active_crops']} active crops. "
            f"Inserted rows: {counts}."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
