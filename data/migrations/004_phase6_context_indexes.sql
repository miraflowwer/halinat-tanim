CREATE INDEX IF NOT EXISTS idx_price_history_dataset_crop_date_location
    ON price_history (dataset_version, crop_id, price_date, geography_id);

CREATE INDEX IF NOT EXISTS idx_supply_snapshots_dataset_crop_period_location
    ON supply_snapshots (dataset_version, crop_id, period_start, period_end, geography_id);

CREATE INDEX IF NOT EXISTS idx_soil_suitability_dataset_crop_location
    ON soil_suitability (dataset_version, crop_id, geography_id);
