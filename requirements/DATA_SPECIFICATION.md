# TANIM Data Specification

## 1. Purpose

This document defines the authoritative data model, coverage rules, units, provenance rules, and deterministic synthetic-data requirements for TANIM.

The goal is to keep the engine, maps, charts, Crop Library, API, and database consistent.

## 2. Core principles

TANIM data must be consistent, versioned, deterministic where generated, traceable, explicit about units, explicit about geography, and safe for use by the explainable engine.

## 3. Geography

Current product scope:

- Country: Philippines
- Island group: Luzon

Supported geographic levels:

1. Region
2. Province
3. Municipality or City

Barangay is not required.

Recommended geography fields:

```text
geography_id
name
level
code
parent_geography_id
country
island_group
active
```

Allowed levels:

- `region`
- `province`
- `municipality_city`

All active product geographies must belong to Luzon for the current MVP.

## 4. Canonical crop registry

Target location:

`data/registry/crops.csv` or an equivalent structured format.

Recommended fields:

```text
crop_id
canonical_name_en
canonical_name_tl
scientific_name
category
aliases_en
aliases_tl
active
```

### 4.1 Category scope

The registry may cover fruits, vegetables, root crops, legumes, herbs, spices, and other commonly marketed horticultural produce relevant to Luzon.

Do not automatically include livestock, fisheries, ornamental plants, or unrelated commodity categories.

### 4.2 Crop completeness rule

Every active crop must support:

- Crop Library profile;
- price history;
- planned/reference supply;
- soil suitability;
- supply-map rendering;
- engine lookup.

A completeness test must fail when an active crop is missing a required dataset.

## 5. Units

| Concept | Canonical unit |
|---|---|
| Farm or planned area | hectare |
| Reference area | hectare |
| Weight | kilogram or metric ton, explicitly identified |
| Prototype price | Philippine peso per kilogram unless dataset says otherwise |
| Temperature | degrees Celsius |
| Rainfall | millimeter |
| Ratio | decimal number |
| Percentage display | ratio multiplied by 100 |
| Dates | ISO 8601 |

Do not mix incompatible units without explicit conversion.

## 6. Required dataset families

1. crop registry;
2. geography registry;
3. planting plans;
4. crop reference levels;
5. price history;
6. supply snapshots;
7. soil suitability;
8. crop profiles;
9. demo accounts and demo scenario;
10. weather response data.

## 7. Data provenance fields

Generated agricultural datasets should include or be associated with:

```text
dataset_version
data_kind
generated_at
seed
geographic_scope
period_start
period_end
unit
reference_sources
method_note
```

Recommended `data_kind` values:

- `synthetic_demo`
- `user_entered`
- `derived`
- `live_external`

Weather uses `live_external` when loaded from the weather provider.

## 8. Synthetic data policy

TANIM may use realistic synthetic agricultural data where real access is limited.

Required rules:

- use a fixed seed;
- generate once for a named dataset version;
- commit stable generated output when appropriate;
- never regenerate at normal application startup;
- keep values within plausible ranges defined by generator inputs;
- preserve realistic variation across crop, geography, and time;
- avoid impossible negative values;
- maintain referential integrity with crop and geography registries;
- document reference sources used to shape ranges or trends;
- do not label a generated number as an exact value published by a referenced institution.

A visible warning banner is not required on every product screen.

Provenance must still be available through metadata and documentation.

## 9. Dataset versioning

Use a readable dataset version such as:

`demo-2026-09-v1`

When data meaning, generation logic, or a major input changes, create a new version.

Do not silently replace an existing version with different values.

## 10. Deterministic generation

The generator must accept:

- crop registry version;
- geography registry version;
- fixed numeric seed;
- output dataset version.

Given the same inputs, generated output must be identical.

Recommended tests:

- same seed produces same checksum;
- different version is explicit;
- no active crop is omitted;
- no unsupported geography is created;
- units are valid;
- values satisfy field constraints.

## 11. Planting plans

Recommended fields:

```text
plan_id
user_id
organization_id
crop_id
geography_id
area_ha
planting_date
harvest_start
harvest_end
status
created_at
updated_at
```

Rules:

- `area_ha` must be greater than zero;
- `harvest_end` must not be before `harvest_start`;
- crop must be active;
- geography must be supported.

## 12. Crop reference levels

Recommended fields:

```text
reference_id
crop_id
geography_id
period_start
period_end
reference_area_ha
data_kind
dataset_version
reference_sources
method_note
```

Rules:

- reference area must be positive for a numeric risk ratio;
- zero or missing reference area must produce an explicit unavailable or invalid state;
- period and geography must be compatible with the risk query.

## 13. Price history

Recommended fields:

```text
price_id
crop_id
geography_id
date
price_php_per_kg
data_kind
dataset_version
reference_sources
```

Rules:

- values must be non-negative;
- currency is PHP;
- canonical display is PHP per kilogram unless explicitly transformed;
- chart ordering is chronological.

## 14. Supply snapshots

Recommended fields:

```text
snapshot_id
crop_id
geography_id
period_start
period_end
planned_area_ha
reference_area_ha
ratio
risk_level
data_kind
dataset_version
```

Allowed risk values:

- `low`
- `moderate`
- `high`
- `no_data`

Supply snapshots may be generated for map performance, but their calculation must remain consistent with the engine.

## 15. Soil suitability

Recommended fields:

```text
suitability_id
crop_id
geography_id
suitability_class
data_kind
dataset_version
reference_sources
method_note
```

Allowed values:

- `suitable`
- `moderately_suitable`
- `low_suitability`
- `no_data`

Suitability is not a Glut Risk score.

## 16. Crop profiles

Recommended fields:

```text
crop_id
summary_en
summary_tl
growing_conditions_en
growing_conditions_tl
soil_notes_en
soil_notes_tl
source_notes
```

Profile content must not make unsupported medical, financial, or guaranteed-yield claims.

## 17. User and consent data

User records include:

```text
user_id
email
password_hash
display_name
role
preferred_language
has_completed_demo
created_at
```

Allowed roles:

- `farmer`
- `cooperative`

Consent records include:

```text
user_id
privacy_notice_version
accepted_at
optional_data_improvement_consent
```

Do not store plaintext passwords.

## 18. Demo accounts

Seed data must include one farmer account and one cooperative account.

Seed creation should use the same password-hashing logic as normal registration.

Do not place plaintext passwords inside committed SQL migration files.

## 19. First-time demo data

The onboarding demonstration must use isolated demo state.

The demo may use a fixed scenario such as Tomato with existing community plans, a sample new plan, a reference level, a High risk result, and Eggplant or another crop as a lower-pressure comparison.

The demo must not write temporary records into the user's normal planting-plan dataset unless the user explicitly chooses to keep a plan.

## 20. Weather

Weather is not part of the synthetic agricultural dataset.

Normalize provider data where available into fields such as:

```text
geography_or_coordinates
observed_at
temperature_c
rainfall_mm
condition
forecast_period
provider
retrieved_at
```

A failed provider request must not create synthetic current weather.

## 21. Source references

The concept note identifies intended reference categories including:

- PSA OpenSTAT historical crop production, planted area, and price data;
- Department of Agriculture price monitoring;
- PAGASA climate information;
- weather API data;
- supply utilization information;
- NCCAG crop suitability mapping.

A source reference does not mean every generated TANIM value was published by that source.

## 22. Data folders

```text
data/
├── registry/
├── generated/
├── seeds/
├── sources/
└── migrations/
```

Do not place random CSV files in the repository root.

## 23. Validation requirements

Automated validation must eventually cover:

- crop IDs unique;
- geography IDs unique;
- all foreign keys valid;
- all active crops complete;
- all current geographies in Luzon;
- dates parse correctly;
- units valid;
- price values non-negative;
- area values valid;
- no invalid risk labels;
- no duplicate natural-key records unless versioned;
- deterministic generated-data checksum.

## 24. Expansion rule

Future Visayas and Mindanao support should add geography and dataset coverage without changing the meaning of existing Luzon records.

Do not prefill unsupported island groups with fake current coverage in the MVP.
