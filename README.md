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

## Start TANIM

On Windows, double-click `TANIM.bat`.

The launcher checks local dependencies before starting TANIM. It must ask before attempting to install missing software.

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
