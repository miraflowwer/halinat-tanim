# Phase 1 Foundation

## Goal

Create a clean, runnable project foundation before building TANIM features.

Phase 1 does not require finished product screens. It establishes the repository contract, local toolchain, database foundation, launcher behavior, and health-check path that later phases build on.

## Deliverables

Required root files:

- `AGENTS.md`
- `README.md`
- `PRODUCT.md`
- `.env.example`
- `.gitignore`
- `.editorconfig`
- `package.json`
- `pyproject.toml`
- `TANIM.bat`
- `STOP_TANIM.bat`

Required requirement files:

- `requirements/PRODUCT_REQUIREMENTS.md`
- `requirements/ARCHITECTURE.md`
- `requirements/DATA_SPECIFICATION.md`
- `requirements/PHASE_1_FOUNDATION.md`

Required scaffold:

- `apps/landing`
- `apps/auth`
- `apps/platform`
- `apps/docs`
- `services/api`
- `services/engine`
- `packages/ui`
- `packages/i18n`
- `packages/types`
- `packages/config`
- `data/registry`
- `data/generated`
- `data/seeds`
- `data/sources`
- `data/migrations`
- `scripts`
- `tests`

## Step 1. Verify repository rules

Read `AGENTS.md`.

Do not begin final UI design work.

Do not create `DESIGN.md` yet.

## Step 2. Establish Node workspace

Root `package.json` must be private, declare app and package workspaces, contain shared verification/test/lint commands, and support the four frontend development commands once apps are implemented.

Do not add unnecessary framework packages at the root.

## Step 3. Establish Python environment

Root `pyproject.toml` must require Python 3.12 or later and include the packages required by the architecture specification.

Use `.venv` locally.

Do not install project dependencies globally.

## Step 4. Establish database foundation

Apply `data/migrations/001_foundation.sql` to a local PostgreSQL development database.

The migration creates the baseline tables for users, consent, organizations, geographies, crops, planting plans, reference levels, prices, supply snapshots, and suitability.

Do not seed plaintext passwords through SQL.

## Step 5. Establish launcher scripts

`TANIM.bat` calls `scripts/start-tanim.ps1`.

`STOP_TANIM.bat` calls `scripts/stop-tanim.ps1`.

The start script must check dependencies, ask before attempted installation, prepare local project dependencies with user confirmation when needed, start implemented frontend and API processes, record TANIM process IDs, run health checks, and open the landing page only when required checks pass.

The stop script must kill only recorded TANIM process trees.

## Step 6. Establish health-check contract

The final local system must expose:

- Landing: `http://127.0.0.1:3000`
- Auth: `http://127.0.0.1:3001`
- Platform: `http://127.0.0.1:3002`
- Docs: `http://127.0.0.1:3003`
- API health: `http://127.0.0.1:8000/health`
- API database health: `http://127.0.0.1:8000/health/db`

Weather availability is not required for startup health.

## Step 7. Verify clean foundation

Run:

```text
python scripts/verify_foundation.py
```

Before completing Phase 1:

- no `.env` is committed;
- no `node_modules` is committed;
- no `.venv` is committed;
- no build output is committed;
- no runtime logs are committed;
- no random root-level working files remain.

## Acceptance criteria

Phase 1 is complete when:

- the repository structure matches the architecture specification;
- authoritative requirements exist;
- agent rules exist;
- Node and Python workspace configuration exists;
- the baseline database migration exists;
- the Windows start/stop entry points exist;
- dependency checks are implemented;
- startup has a defined health-check contract;
- local runtime files are Git-ignored;
- foundation verification passes.

Finished product screens are not required for Phase 1.
