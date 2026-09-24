# Phase 6 crop and context utilities

## Scope

Phase 6 adds read-only context tools for crops, prices, soil suitability, supply, and weather. It does not add planting-plan records or change the Glut Risk calculation.

The utilities use the active version in `data/dataset_config.json`. If that version is not seeded in PostgreSQL, the API returns a clear dataset error. It does not use an older version as a fallback.

## Crop Library

`GET /crops` returns active crops with English and Tagalog names, scientific names, category, aliases, data kind, and dataset version. It accepts `q`, `category`, `limit`, and `offset` filters.

`GET /crops/{crop_id}` returns the crop profile, growing context, soil notes, source IDs, method note, dataset provenance, and links to price, supply, and suitability context. Profile text is general demo context. It is not official local agronomic advice.

## Price history

`GET /prices` requires `crop_id`. It accepts `geography_id`, `range` (`1m`, `3m`, `1y`, or `all`), optional `start_date` and `end_date`, and a bounded `limit`.

Each price record reports its date, PHP/kg value, location, data kind, dataset version, and source references. Generated values are synthetic demo values. PSA and DA sources informed crop and price context, but they did not publish the generated values.

The page has an SVG chart with keyboard-readable points and a table view. It always shows PHP per kilogram. The chart does not need a large chart library.

## Soil suitability

`GET /suitability` requires `crop_id` and `geography_id`. It returns `suitable`, `moderately_suitable`, `low_suitability`, or `no_data`, with data kind, version, and method or source notes when available.

Suitability is not supply pressure. A crop can have suitable soil and still have High Glut Risk. Synthetic labels are not a BSWM or NCCAG survey.

## Supply map

`GET /supply-map` requires `crop_id` and accepts `period`. The period is `current` or a supported ISO period start date. The response returns regional planned and reference context, ratio, level, data status, active dataset version, and available periods.

The Supply Map visualization level is Region. The API aggregates `supply_snapshots` for municipality and city locations to the Luzon region level. These are synthetic context snapshots. They are not registered farmer planting plans. Regional ratios use the configured snapshot thresholds. This is separate from the Phase 3 Glut Risk engine. Crop and risk planning can still use Municipality or City geography.

`GET /map-geometry` returns the local eight-region GeoJSON layer. The map uses this file and does not request online tiles. The page also provides a keyboard-accessible region list with text labels and values.

### Local map geometry

The geometry comes from the geoBoundaries `gbOpen` Philippines ADM1 layer, boundary ID `PHL-ADM1-36201628`, represented as 2020. Its source metadata names the National Mapping and Resource Information Authority, the Philippine Statistics Authority, and OCHA Philippines. The source metadata reports CC BY 3.0 IGO. The geoBoundaries project also reports CC BY 4.0 for its generated files. Check the individual source metadata before reuse outside this project.

TANIM keeps the pre-simplified eight Luzon region features, removes the other Philippine regions, and adds the canonical TANIM geography IDs and names. No boundary was drawn or manually changed. The layer is a demo display aid, not a legal or official map.

## Weather provider boundary

Weather uses an Open-Meteo provider adapter. `GET /weather/status` checks whether the provider can return weather data. `GET /weather` returns current conditions and a short forecast for a selected Luzon region. The response is live external data and is kept separate from synthetic agricultural data.

The user must choose Continue before the platform calls either weather endpoint. A Wi-Fi connection alone does not prove the provider is reachable. On failure, TANIM shows the required connection message and a Retry action. Weather is not part of `/health`, `/health/db`, or launcher readiness.

The Open-Meteo free API is for non-commercial use. It requires attribution. Commercial use needs an Open-Meteo commercial plan. See the [Open-Meteo terms](https://open-meteo.com/en/terms) and [forecast API guide](https://open-meteo.com/en/docs).

## Provenance and offline behavior

Crop profiles, prices, suitability, and supply snapshots use the configured synthetic dataset version. Each response keeps the dataset version and available data kind or source context. The API never labels a synthetic price as a PSA or DA observation.

Crop, price, suitability, supply, and map geometry use local TANIM data. They work without internet when the local API and database are running. Only live weather needs internet access. A weather failure does not block other TANIM features.

## Accessibility

All controls use labels and work with a keyboard. The supply map includes text labels and a region list alternative. The price chart includes keyboard-readable points and a data table. Status, empty, loading, and error states are shown in English and Tagalog. Layouts support mobile widths from about 360 px.

## Non-goals

Phase 6 does not add planting-plan CRUD, dashboards, authentication, first-time demo changes, a documentation website, online map tiles, soil surveys, market forecasts, or a weather-based risk score. It does not change the Phase 3 Glut Risk formula.

The authenticated Phase 5 platform shell owns final navigation integration. Phase 6 utility components stay under `apps/platform/src/features/phase6/` and their feature folders until that shell is ready.
