CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('farmer', 'cooperative')),
    preferred_language TEXT NOT NULL DEFAULT 'en' CHECK (preferred_language IN ('en', 'tl')),
    has_completed_demo BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS privacy_consents (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    privacy_notice_version TEXT NOT NULL,
    accepted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    optional_data_improvement_consent BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS organizations (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    organization_type TEXT NOT NULL DEFAULT 'cooperative'
        CHECK (organization_type IN ('cooperative')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS organization_members (
    organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (organization_id, user_id)
);

CREATE TABLE IF NOT EXISTS geographies (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    level TEXT NOT NULL CHECK (level IN ('region', 'province', 'municipality_city')),
    code TEXT,
    parent_id BIGINT REFERENCES geographies(id) ON DELETE RESTRICT,
    country TEXT NOT NULL DEFAULT 'Philippines',
    island_group TEXT NOT NULL DEFAULT 'Luzon',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (level, name, parent_id)
);

CREATE TABLE IF NOT EXISTS crops (
    crop_id TEXT PRIMARY KEY,
    canonical_name_en TEXT NOT NULL,
    canonical_name_tl TEXT,
    scientific_name TEXT,
    category TEXT NOT NULL,
    aliases_en TEXT[] NOT NULL DEFAULT '{}',
    aliases_tl TEXT[] NOT NULL DEFAULT '{}',
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS planting_plans (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id BIGINT REFERENCES organizations(id) ON DELETE SET NULL,
    crop_id TEXT NOT NULL REFERENCES crops(crop_id) ON DELETE RESTRICT,
    geography_id BIGINT NOT NULL REFERENCES geographies(id) ON DELETE RESTRICT,
    area_ha NUMERIC(12, 4) NOT NULL CHECK (area_ha > 0),
    planting_date DATE NOT NULL,
    harvest_start DATE NOT NULL,
    harvest_end DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'completed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (harvest_end >= harvest_start)
);

CREATE INDEX IF NOT EXISTS idx_planting_plans_lookup
    ON planting_plans (crop_id, geography_id, harvest_start, harvest_end);

CREATE TABLE IF NOT EXISTS crop_references (
    id BIGSERIAL PRIMARY KEY,
    crop_id TEXT NOT NULL REFERENCES crops(crop_id) ON DELETE RESTRICT,
    geography_id BIGINT NOT NULL REFERENCES geographies(id) ON DELETE RESTRICT,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    reference_area_ha NUMERIC(12, 4) NOT NULL CHECK (reference_area_ha > 0),
    data_kind TEXT NOT NULL DEFAULT 'synthetic_demo'
        CHECK (data_kind IN ('synthetic_demo', 'derived', 'live_external', 'user_entered')),
    dataset_version TEXT NOT NULL,
    reference_sources TEXT,
    method_note TEXT,
    CHECK (period_end >= period_start)
);

CREATE INDEX IF NOT EXISTS idx_crop_references_lookup
    ON crop_references (crop_id, geography_id, period_start, period_end);

CREATE TABLE IF NOT EXISTS price_history (
    id BIGSERIAL PRIMARY KEY,
    crop_id TEXT NOT NULL REFERENCES crops(crop_id) ON DELETE RESTRICT,
    geography_id BIGINT NOT NULL REFERENCES geographies(id) ON DELETE RESTRICT,
    price_date DATE NOT NULL,
    price_php_per_kg NUMERIC(12, 4) NOT NULL CHECK (price_php_per_kg >= 0),
    data_kind TEXT NOT NULL DEFAULT 'synthetic_demo'
        CHECK (data_kind IN ('synthetic_demo', 'derived', 'live_external', 'user_entered')),
    dataset_version TEXT NOT NULL,
    reference_sources TEXT,
    UNIQUE (crop_id, geography_id, price_date, dataset_version)
);

CREATE TABLE IF NOT EXISTS supply_snapshots (
    id BIGSERIAL PRIMARY KEY,
    crop_id TEXT NOT NULL REFERENCES crops(crop_id) ON DELETE RESTRICT,
    geography_id BIGINT NOT NULL REFERENCES geographies(id) ON DELETE RESTRICT,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    planned_area_ha NUMERIC(12, 4) NOT NULL CHECK (planned_area_ha >= 0),
    reference_area_ha NUMERIC(12, 4),
    ratio NUMERIC(16, 6),
    risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'moderate', 'high', 'no_data')),
    data_kind TEXT NOT NULL DEFAULT 'derived'
        CHECK (data_kind IN ('synthetic_demo', 'derived', 'live_external', 'user_entered')),
    dataset_version TEXT NOT NULL,
    CHECK (period_end >= period_start),
    CHECK (reference_area_ha IS NULL OR reference_area_ha > 0)
);

CREATE TABLE IF NOT EXISTS soil_suitability (
    id BIGSERIAL PRIMARY KEY,
    crop_id TEXT NOT NULL REFERENCES crops(crop_id) ON DELETE RESTRICT,
    geography_id BIGINT NOT NULL REFERENCES geographies(id) ON DELETE RESTRICT,
    suitability_class TEXT NOT NULL
        CHECK (suitability_class IN ('suitable', 'moderately_suitable', 'low_suitability', 'no_data')),
    data_kind TEXT NOT NULL DEFAULT 'synthetic_demo'
        CHECK (data_kind IN ('synthetic_demo', 'derived', 'live_external', 'user_entered')),
    dataset_version TEXT NOT NULL,
    reference_sources TEXT,
    method_note TEXT,
    UNIQUE (crop_id, geography_id, dataset_version)
);
