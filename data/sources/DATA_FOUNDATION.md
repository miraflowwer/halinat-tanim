# TANIM Data Foundation

## Canonical registries

The canonical crop list is `data/registry/crops.csv`. Each crop has a stable `crop_id`. Generated records use that ID instead of a display name. The declared crop universe is `data/registry/crop_scope_inventory.csv`. Validation requires the active registry membership to equal the inventory rows marked `in_scope = true`. The inventory also records aliases, source context, and reasons for exclusions.

The canonical geography list is `data/registry/geographies.csv`. It uses the official PSGC code in a stable ID such as `province_0304900000` or `mun_0304903000`. The database keeps its own numeric key and stores the canonical ID in `geographies.geography_id`.

The geography registry covers Luzon. It has 8 regions, 38 provinces, and 771 cities or municipalities. NCR has no province records in PSGC. Its cities and Pateros link to the NCR region. TANIM does not include barangays.

## Dataset version and generation

`data/dataset_config.json` is the one source for the dataset version, fixed seed, time periods, and demo snapshot thresholds. The current version is `demo-2026-09-v3` with seed `20260924`.

The time contract has two parts:

- Current supply context is 2026-09-01 through 2026-09-30. It is used for the current supply map.
- Future planning periods are the complete quarterly horizon from 2026-10-01 through 2028-12-31. This includes October through December 2026 and all eight quarters in 2027 and 2028. A date outside this horizon is unsupported and must be reported as such.

Run the generator with:

```text
python scripts/generate_demo_data.py
```

The generator writes files under the folder named by `dataset_version` in `data/dataset_config.json`. It uses stable SHA-256 based values, stable sorting, and deterministic gzip output. It does not use Python's randomized `hash()` function. If the same version already exists with the same content, it reports that the data match. If that version exists with different content, the command stops. Use a new dataset version for changed inputs or methods. `--replace` is available for a deliberate replacement of the current generated files.

The output files are:

- `crop_profiles.csv.gz`
- `price_history.csv.gz`
- `crop_references.csv.gz`
- `supply_snapshots.csv.gz`
- `soil_suitability.csv.gz`
- `metadata.json`

All synthetic prices use PHP/kg. All reference and planned areas use hectares. Prices have 36 monthly records per active crop and province, plus NCR. Reference and snapshot records cover each active crop and supported municipality or city for the current period and every future planning quarter. Suitability records cover each active crop and supported municipality or city.

Current supply context and future planned supply are separate concepts. `supply_snapshots.csv.gz` rows marked `current_supply` are map context. Rows marked `future_planning` are synthetic future context for later planning work. Neither dataset silently creates `planting_plans` records. The two demo fixtures in `data/seeds/demo_scenarios.json` are future planning fixtures and preserve the Tomato and Eggplant examples.

## Snapshot labels

Demo snapshots show initial context. Their ratio is planned area divided by reference area, rounded to six decimal places. The labels use the prototype thresholds in `data/dataset_config.json`: Low below 0.90, Moderate from 0.90 through 1.10, and High above 1.10. A missing reference would use `no_data`.

This helper labels synthetic snapshots only. It is not the Phase 3 risk engine. Soil suitability is generated separately and is not a supply pressure score.

## Synthetic model

Reference area values use this deterministic hierarchy: crop category baseline, crop behavior factor, region agricultural profile, province band, municipality scale, period factor, and small bounded variation. NCR and obvious urban locations receive a lower municipality scale. The model makes neighboring locations follow their regional and province context instead of using a hash bucket as the primary value.

Suitability starts from a crop and category baseline with a geographic suitability baseline. A small bounded deterministic variation is applied after the baseline. The labels are synthetic demo context and are not an agronomic prediction, soil survey, yield guarantee, or profitability claim.

External price sources remain attached only to price rows. Reference area and suitability rows use their TANIM synthetic method identifiers because no external area or suitability number was copied into those rows.

## Validation and database seeding

Validate registries, generated files, provenance, units, coverage, fixtures, and deterministic output with:

```text
python scripts/validate_data.py
```

Seed the database with:

```text
python scripts/seed_data.py
```

The seed command validates the data before it changes the database, applies numbered migrations, and loads the dataset in one transaction. Repeating the command with the same version and files makes no duplicate rows. It checks row counts and a small deterministic content fingerprint for every seeded table, so a same-count record edit is detected. It stops if the version was already registered with different content.

Numbered migrations contain schema statements only. `scripts/init_db.py` owns the transaction and writes `tanim_schema_migrations` after the migration statements succeed. The migration ledger insert and migration DDL therefore commit atomically.

The fixture file `data/seeds/demo_scenarios.json` defines the Tomato 32 + 8 ha against 25 ha example and a lower-pressure Eggplant example. The fixtures state expected future values. They do not add a risk-check API or engine.

See [SOURCES.md](SOURCES.md) for source details and usage notes.
