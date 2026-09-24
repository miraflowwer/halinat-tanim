# Phase 8 Audit Fixes

## Purpose

This document records the Phase 1 to Phase 6 integration and correction pass. It is an audit record, not a new product phase. The work preserves the current TANIM product scope and does not start Phase 7 documentation or the Impeccable design phase.

## Integration baseline

- `feat/phase-6-utilities` was rebased onto the latest `main` without a merge commit.
- The rebased Phase 6 commit is `5a85a42`.
- The audit changes are isolated on `feat/phases-1-6-audit-fixes`.
- The Phase 7 worktrees were not changed.
- Existing unrelated user changes in the Phase 6 worktree were preserved.

## Corrected API contracts

The Phase 6 context routes are the only crop and geography lookup routes:

- `GET /crops` returns `{ items, total, categories, dataset_version }`.
- `GET /geographies` returns `{ items, dataset_version }`.
- `GET /crops/{crop_id}`, `GET /prices`, `GET /suitability`, `GET /supply-map`, `GET /map-geometry`, `GET /weather/status`, and `GET /weather` remain the context routes.
- The duplicate Phase 5 crop and geography routes were removed.
- Plan-form consumers read lookup values from `items`.

The authenticated platform shell now exposes the Phase 6 tools through the shared route and navigation structure. The Supply Map is explicitly Region level and includes a level filter, text alternatives, and links to crop and price context.

## Authentication and membership corrections

- `/risk/check` requires an authenticated session.
- CSRF tokens are stable for a session, so restoring a session in another tab does not invalidate the first tab.
- Language changes are saved through the authenticated, CSRF-protected account preferences endpoint.
- Login redirects users who have completed the demo to `/dashboard`.
- Cooperative registration requires an organization name.
- Organizations receive a join code during migration or creation.
- A Farmer can have at most one cooperative membership.
- A Farmer can join with a valid code. Active independent plans are assigned to that cooperative in the same transaction.
- Cooperative plan creation requires cooperative membership. Farmer plans remain owned by the Farmer and are visible only through the intended aggregate boundary.
- Community detail is masked when fewer than two registered plans contribute to a risk context. The response explains the limited detail.

## Data and startup corrections

- Planning-area validation is shared by the risk engine and plan API, including finite values, positive values, and the supported precision and maximum.
- `GET /health/readiness` separately checks database access, required tables, the latest migration, the active synthetic dataset, and active crops. It does not call the weather provider.
- The launcher checks the lockfile fingerprint, asks before installing dependencies, applies migrations, seeds the configured dataset, prepares demo accounts only when both configured passwords exist, waits for health and readiness, and opens the landing page only after all checks pass.
- Weather remains the only live external data path. Its attribution is shown in the UI and Open-Meteo is documented as a prototype, noncommercial provider.
- Unused weather API key and base URL settings were removed from `.env.example`.

## Landing and frontend corrections

- The landing app now has functional English and Tagalog copy, links to sign in and register, explains the TANIM problem and solution, and identifies Luzon as the current scope.
- The platform shell links to working Dashboard, Plans, Crops, Map, Weather, and Help destinations.
- Mobile navigation includes the same functional destinations.
- Risk preview, cooperative aggregate views, loading states, error states, privacy-limited values, and bilingual labels remain accessible and responsive.

## Verification record

The audit branch passes:

- `npm test`: 17 frontend tests and 85 Python tests passed, with 9 expected integration skips;
- `npm run lint`: TypeScript and Ruff checks passed;
- `npm run build`: all frontend workspaces built successfully;
- `npm run smoke:risk`, `npm run smoke:platform`, and `npm run smoke:context` passed;
- `scripts/check-health.ps1`: all local services and application readiness passed;
- repeat-safe migration, deterministic dataset seed, and configured demo-account seed completed against local PostgreSQL.

Manual browser verification covered the landing page in English and Tagalog, privacy-gated registration, the required Cooperative organization field, unauthenticated redirect to login, context links, desktop layout, and a mobile-sized layout around 360 pixels. Password-based login, first-time demo completion, and cooperative join submission were not entered through the browser during this pass because that would transmit a local password through UI automation. Their API and frontend contracts are covered by the automated tests and smoke flows.

## Out of scope

This audit does not add cloud deployment, machine learning, Barangay behavior, Visayas or Mindanao support, Phase 7 documentation work, or Impeccable visual refinement.
