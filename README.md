# TANIM

TANIM stands for Timely Agricultural Network for Informed Market.

TANIM is a local-first crop planning and coordination platform for farmers and cooperatives in Luzon, Philippines. It helps users compare planned crop supply with a reference level before planting decisions are finalized.

## Current scope

- Luzon only
- Farmer and cooperative workflows
- English and Tagalog
- Mobile and desktop web
- Localhost development
- Explainable Glut Risk
- Crop Library
- Supply heatmap
- Price history
- Soil suitability
- Weather map
- First-time demo
- Documentation website

## Repository

- `requirements/` contains authoritative product, architecture, and data requirements.
- `apps/` contains the four frontend applications.
- `services/` contains the API and TANIM engine.
- `packages/` contains shared frontend and configuration packages.
- `data/` contains registries, generated datasets, sources, seeds, and migrations.
- `scripts/` contains local development and verification scripts.
- `tests/` contains cross-project tests.

## Data foundation

The canonical crop and Luzon geography registries are in `data/registry/`. The fixed seed, dataset version, and periods are in `data/dataset_config.json`.

Run the data generator and validator with:

```text
python scripts/generate_demo_data.py
python scripts/validate_data.py
```

To load the validated dataset into the local PostgreSQL database, set `DATABASE_URL` in `.env` and run:

```text
python scripts/seed_data.py
```

Read [the data foundation notes](data/sources/DATA_FOUNDATION.md) and [the source notes](data/sources/SOURCES.md) for coverage, units, methods, and limits.

## Start TANIM

On Windows, double-click `TANIM.bat`.

The launcher checks local dependencies before starting TANIM. It must ask before attempting to install missing software.

## Local development setup

Install Node.js 20 or later, npm 10 or later, Python 3.12 or later, and PostgreSQL. Copy `.env.example` to `.env` and set `DATABASE_URL` for your local database. Do not put real credentials in tracked files.

From the repository folder, install the project dependencies and create the database tables:

```powershell
npm install
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe scripts/init_db.py
```

The database command checks the connection and applies all numbered migrations in order. It can be run again safely. After setup, `npm run db:init` runs the same command using the local `.venv`.

## Stop TANIM

Double-click `STOP_TANIM.bat`.

This stops TANIM-owned development processes.

## Requirements

Read:

1. `AGENTS.md`
2. `requirements/PRODUCT_REQUIREMENTS.md`
3. `requirements/ARCHITECTURE.md`
4. `requirements/DATA_SPECIFICATION.md`

## Design

The product is built functionally first.

Visual refinement is performed later with Impeccable. `DESIGN.md` is intentionally not part of the initial foundation and should be created during the design phase.
