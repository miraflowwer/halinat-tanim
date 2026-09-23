# TANIM Data Foundation

## Canonical registries

The canonical crop list is `data/registry/crops.csv`. Each crop has a stable `crop_id`. Generated records use that ID instead of a display name.

The canonical geography list is `data/registry/geographies.csv`. It uses the official PSGC code in a stable ID such as `province_0304900000` or `mun_0304903000`. The database keeps its own numeric key and stores the canonical ID in `geographies.geography_id`.

The geography registry covers Luzon. It has 8 regions, 38 provinces, and 771 cities or municipalities. NCR has no province records in PSGC. Its cities and Pateros link to the NCR region. TANIM does not include barangays.

## Dataset version and generation

`data/dataset_config.json` is the one source for the dataset version, fixed seed, time periods, and demo snapshot thresholds. The current version is `demo-2026-09-v1` with seed `20260924`.

Run the generator with:

```text
python scripts/generate_demo_data.py
```

The generator writes files under the folder named by `dataset_version` in `data/dataset_config.json`. It uses stable SHA-256 based values and stable sorting. It does not use Python's randomized `hash()` function. If the same version already exists with the same content, it reports that the data match. If that version exists with different content, the command stops. Use a new dataset version for changed inputs or methods. `--replace` is available for a deliberate replacement of the current generated files.

The output files are:

- `crop_profiles.csv`
- `price_history.csv`
- `crop_references.csv`
- `supply_snapshots.csv`
- `soil_suitability.csv`
- `metadata.json`

All synthetic prices use PHP/kg. All reference and planned areas use hectares. Prices have 36 monthly records per active crop and province, plus NCR. Supply, reference, and suitability records cover each active crop and supported municipality or city.

## Snapshot labels

Demo snapshots show initial context. Their ratio is planned area divided by reference area, rounded to six decimal places. The labels use the prototype thresholds in `data/dataset_config.json`: Low below 0.90, Moderate from 0.90 through 1.10, and High above 1.10. A missing reference would use `no_data`.

This helper labels synthetic snapshots only. It is not the Phase 3 risk engine. Soil suitability is generated separately and is not a supply pressure score.

## Validation and database seeding

Validate registries, generated files, provenance, units, coverage, fixtures, and deterministic output with:

```text
python scripts/validate_data.py
```

Seed the database with:

```text
python scripts/seed_data.py
```

The seed command validates the data before it changes the database, applies numbered migrations, and loads the dataset in one transaction. Repeating the command with the same version and files makes no duplicate rows. It stops if the version was already registered with different content.

The fixture file `data/seeds/demo_scenarios.json` defines the Tomato 32 + 8 ha against 25 ha example and a lower-pressure Eggplant example. The fixtures state expected future values. They do not add a risk-check API or engine.

See [SOURCES.md](SOURCES.md) for source details and usage notes.
