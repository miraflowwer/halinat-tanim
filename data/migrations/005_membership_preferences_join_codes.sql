ALTER TABLE organizations
    ADD COLUMN IF NOT EXISTS join_code TEXT;

UPDATE organizations
SET join_code = 'TANIM-' || UPPER(SUBSTRING(MD5('tanim-organization:' || id::TEXT) FROM 1 FOR 6))
WHERE join_code IS NULL OR BTRIM(join_code) = '';

ALTER TABLE organizations
    ALTER COLUMN join_code SET DEFAULT (
        'TANIM-' || UPPER(SUBSTRING(MD5(RANDOM()::TEXT || CLOCK_TIMESTAMP()::TEXT) FROM 1 FOR 6))
    ),
    ALTER COLUMN join_code SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_organizations_join_code
    ON organizations (join_code);

CREATE UNIQUE INDEX IF NOT EXISTS uq_organization_members_user_id
    ON organization_members (user_id);

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS preferred_language TEXT NOT NULL DEFAULT 'en';

CREATE INDEX IF NOT EXISTS idx_planting_plans_user_status
    ON planting_plans (user_id, status);

CREATE INDEX IF NOT EXISTS idx_planting_plans_organization_status
    ON planting_plans (organization_id, status);
