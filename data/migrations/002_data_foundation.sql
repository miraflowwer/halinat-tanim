BEGIN;

ALTER TABLE geographies
    ADD COLUMN IF NOT EXISTS geography_id TEXT;

UPDATE geographies
SET geography_id = CASE
    WHEN code ~ '^[0-9]{10}$' THEN
        CASE level
            WHEN 'region' THEN 'region_' || code
            WHEN 'province' THEN 'province_' || code
            WHEN 'municipality_city' THEN 'mun_' || code
            ELSE 'legacy_' || id::TEXT
        END
    ELSE 'legacy_' || id::TEXT
END
WHERE geography_id IS NULL;

ALTER TABLE geographies
    ALTER COLUMN geography_id SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_geographies_geography_id
    ON geographies (geography_id);

COMMENT ON COLUMN geographies.geography_id IS
    'Stable canonical dataset identifier. The id column remains the internal database key.';

ALTER TABLE crop_references
    ADD COLUMN IF NOT EXISTS area_unit TEXT NOT NULL DEFAULT 'ha'
        CHECK (area_unit = 'ha');

CREATE UNIQUE INDEX IF NOT EXISTS uq_crop_references_dataset_period
    ON crop_references (crop_id, geography_id, period_start, period_end, dataset_version);

ALTER TABLE price_history
    ADD COLUMN IF NOT EXISTS currency TEXT NOT NULL DEFAULT 'PHP'
        CHECK (currency = 'PHP'),
    ADD COLUMN IF NOT EXISTS price_unit TEXT NOT NULL DEFAULT 'PHP/kg'
        CHECK (price_unit = 'PHP/kg');

ALTER TABLE supply_snapshots
    ADD COLUMN IF NOT EXISTS area_unit TEXT NOT NULL DEFAULT 'ha'
        CHECK (area_unit = 'ha');

CREATE UNIQUE INDEX IF NOT EXISTS uq_supply_snapshots_dataset_period
    ON supply_snapshots (crop_id, geography_id, period_start, period_end, dataset_version);

CREATE TABLE IF NOT EXISTS crop_profiles (
    crop_id TEXT NOT NULL REFERENCES crops(crop_id) ON DELETE RESTRICT,
    dataset_version TEXT NOT NULL,
    summary_en TEXT NOT NULL,
    summary_tl TEXT NOT NULL,
    growing_conditions_en TEXT NOT NULL,
    growing_conditions_tl TEXT NOT NULL,
    soil_notes_en TEXT NOT NULL,
    soil_notes_tl TEXT NOT NULL,
    data_kind TEXT NOT NULL CHECK (data_kind IN ('synthetic_demo', 'derived', 'live_external', 'user_entered')),
    reference_sources TEXT,
    method_note TEXT,
    PRIMARY KEY (crop_id, dataset_version)
);

CREATE TABLE IF NOT EXISTS dataset_metadata (
    dataset_version TEXT PRIMARY KEY,
    data_kind TEXT NOT NULL CHECK (data_kind = 'synthetic_demo'),
    seed BIGINT NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    metadata JSONB NOT NULL,
    seeded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS demo_scenarios (
    scenario_id TEXT NOT NULL,
    dataset_version TEXT NOT NULL REFERENCES dataset_metadata(dataset_version) ON DELETE RESTRICT,
    crop_id TEXT NOT NULL REFERENCES crops(crop_id) ON DELETE RESTRICT,
    geography_id BIGINT NOT NULL REFERENCES geographies(id) ON DELETE RESTRICT,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    existing_planned_area_ha NUMERIC(12, 4) NOT NULL CHECK (existing_planned_area_ha >= 0),
    proposed_future_plan_area_ha NUMERIC(12, 4) NOT NULL CHECK (proposed_future_plan_area_ha >= 0),
    reference_area_ha NUMERIC(12, 4) NOT NULL CHECK (reference_area_ha > 0),
    projected_area_ha NUMERIC(12, 4) NOT NULL CHECK (projected_area_ha >= 0),
    expected_future_ratio NUMERIC(16, 6) NOT NULL CHECK (expected_future_ratio >= 0),
    expected_future_risk TEXT NOT NULL CHECK (expected_future_risk IN ('low', 'moderate', 'high', 'no_data')),
    data_kind TEXT NOT NULL CHECK (data_kind = 'synthetic_demo'),
    fixture_data JSONB NOT NULL,
    PRIMARY KEY (scenario_id, dataset_version),
    CHECK (period_end >= period_start),
    CHECK (projected_area_ha = existing_planned_area_ha + proposed_future_plan_area_ha)
);

CREATE INDEX IF NOT EXISTS idx_crop_profiles_dataset_version
    ON crop_profiles (dataset_version, crop_id);

CREATE INDEX IF NOT EXISTS idx_dataset_metadata_data_kind
    ON dataset_metadata (data_kind, dataset_version);

COMMIT;
