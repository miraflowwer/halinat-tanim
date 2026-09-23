# TANIM Architecture Specification

## 1. Architecture goal

Build one organized local monorepo that presents four separate TANIM web applications while sharing one API, one PostgreSQL database, one TANIM engine, one crop registry, one localization system, and one reusable UI layer.

The architecture must remain simple enough for a hackathon MVP and clean enough for later expansion.

## 2. Technology baseline

Frontend:

- React
- TypeScript
- Vite
- React Router where routing is needed
- Chart.js for standard charts
- Leaflet with GeoJSON or an equivalently lightweight map layer for Luzon maps

Backend:

- Python 3.12 or later
- FastAPI
- PostgreSQL
- psycopg 3
- Pydantic

Testing and quality:

- pytest
- Ruff
- frontend test tooling selected inside each app as implemented

Do not introduce a second backend runtime unless there is a documented need.

## 3. Repository structure

```text
tanim/
├── AGENTS.md
├── README.md
├── PRODUCT.md
├── TANIM.bat
├── STOP_TANIM.bat
├── .env.example
├── .gitignore
├── .editorconfig
├── package.json
├── pyproject.toml
├── requirements/
├── apps/
├── services/
├── packages/
├── data/
├── scripts/
└── tests/
```

Do not create separate repositories for the four web applications.

## 4. Local services and ports

| Service | Address |
|---|---|
| Landing | `http://127.0.0.1:3000` |
| Authentication | `http://127.0.0.1:3001` |
| Platform | `http://127.0.0.1:3002` |
| Documentation | `http://127.0.0.1:3003` |
| API | `http://127.0.0.1:8000` |
| PostgreSQL | local PostgreSQL instance, normally port 5432 |

Ports should be configurable, but these are the project defaults.

## 5. Application responsibilities

### 5.1 `apps/landing`

Public entry point.

Responsibilities:

- product introduction;
- links to authentication and documentation;
- Luzon coverage explanation;
- core feature overview.

Must not contain risk calculation logic.

### 5.2 `apps/auth`

Responsibilities:

- privacy consent;
- account registration;
- login;
- session handoff to platform.

Must not own duplicate user persistence logic.

### 5.3 `apps/platform`

Responsibilities:

- dashboard;
- first-time demo;
- planting plans;
- risk results;
- cooperative aggregate view;
- Crop Library;
- supply map;
- price history;
- suitability;
- weather;
- settings/help.

### 5.4 `apps/docs`

Responsibilities:

- searchable and navigable documentation;
- left navigation on desktop;
- mobile navigation drawer;
- legal and ethics content.

This site must not become the source of truth for engineering requirements.

## 6. Shared packages

### 6.1 `packages/ui`

Shared functional components.

Initial components may include Button, Input, Select, Dialog, Alert, Card, Table, Tabs, Navigation, LanguageSelector, LoadingState, EmptyState, and ErrorState.

Before the Impeccable phase, these should be intentionally simple, accessible, and responsive.

### 6.2 `packages/i18n`

Owns English messages, Tagalog messages, locale selection, and shared formatting helpers.

Do not hard-code shared user-facing copy independently across applications.

### 6.3 `packages/types`

Owns shared TypeScript API and domain types.

These types must reflect, not replace, the backend contract.

### 6.4 `packages/config`

Owns shared frontend configuration, safe defaults, and route/service addresses.

No secrets.

## 7. Backend structure

### 7.1 `services/api`

FastAPI application.

Responsibilities:

- authentication/session API;
- consent API;
- crop registry API;
- geography API;
- planting-plan CRUD;
- risk-check API;
- cooperative aggregate API;
- price API;
- suitability API;
- supply-map API;
- weather provider adapter where appropriate;
- health endpoints.

### 7.2 `services/engine`

Pure or near-pure domain logic.

Responsibilities:

- aggregate relevant planting plans;
- calculate supply pressure;
- classify risk;
- build explanation;
- compare alternative crops;
- validate engine inputs.

Engine functions should be testable without starting the web server.

## 8. API boundary

Frontend applications must use the API for persisted product data and risk calculations.

Do not duplicate the risk formula in React.

Recommended baseline endpoints:

```text
GET    /health
GET    /health/db
POST   /auth/register
POST   /auth/login
POST   /auth/logout
GET    /auth/session
GET    /crops
GET    /crops/{crop_id}
GET    /geographies
GET    /geographies/{geography_id}
GET    /plans
POST   /plans
GET    /plans/{plan_id}
PATCH  /plans/{plan_id}
DELETE /plans/{plan_id}
POST   /risk/check
GET    /cooperative/overview
GET    /supply-map
GET    /prices
GET    /suitability
GET    /weather/status
GET    /weather
```

## 9. Risk response contract

A risk response must expose enough information for explanation.

Example shape:

```json
{
  "crop_id": "tomato",
  "geography_id": "example",
  "harvest_start": "2027-03-01",
  "harvest_end": "2027-03-31",
  "planned_area_ha": 40.0,
  "reference_area_ha": 25.0,
  "ratio": 1.6,
  "risk": "high",
  "assumption_version": "grci-v1",
  "dataset_version": "demo-2026-09-v3",
  "explanation": "Registered plans are above the current reference level for this period.",
  "alternatives": []
}
```

The API must not return a misleading numeric ratio when the denominator is missing or zero.

## 10. Database approach

Use PostgreSQL directly through psycopg for the MVP.

Avoid an ORM unless a later requirement clearly justifies it.

Database migrations belong in `data/migrations`.

The baseline schema covers:

- users;
- privacy consent;
- organizations;
- organization membership;
- geographies;
- crops;
- planting plans;
- crop reference values;
- price history;
- supply snapshots;
- soil suitability.

Password hashing belongs in the application, not SQL.

## 11. Authentication

Keep authentication simple.

Requirements:

- email and password;
- password hash stored in PostgreSQL;
- session managed securely for localhost development;
- role is Farmer or Cooperative;
- privacy consent recorded;
- first-time-demo completion stored.

Out of scope: password reset, email verification, OTP, social login, and 2FA.

## 12. Local launcher architecture

### 12.1 Root launcher

`TANIM.bat` calls `scripts/start-tanim.ps1`.

`STOP_TANIM.bat` calls `scripts/stop-tanim.ps1`.

### 12.2 Dependency checks

Required local tools:

- Node.js 20 or later;
- npm 10 or later;
- Python 3.12 or later;
- PostgreSQL client/server suitable for the local database.

When a required dependency is missing:

1. display the missing dependency;
2. ask whether the user wants TANIM to attempt installation;
3. only continue after explicit confirmation;
4. use Windows Package Manager when available;
5. if automatic installation fails or is unavailable, show a clear manual action and stop.

No silent installation.

### 12.3 Project dependency setup

The launcher may prompt before `npm install`, creation of `.venv`, or Python package installation.

Do not modify global Python packages.

### 12.4 Process ownership

The launcher must record TANIM-owned development process IDs under `.tanim/runtime/`.

The stop script kills only recorded TANIM process trees.

Do not kill every Node.js, Python, or PostgreSQL process on the machine.

### 12.5 Health checks

Required local checks:

- landing successful response;
- auth successful response;
- platform successful response;
- docs successful response;
- API `/health` healthy;
- API database health healthy.

External weather availability is not a launcher readiness requirement.

The landing page opens only after required local checks pass.

## 13. Weather integration

Weather is an external capability.

Rules:

- the main API and product must work when the weather provider is unreachable;
- weather status must be checked at request time;
- provider failure must map to a clear retryable product state;
- weather must not silently change the core Glut Risk unless a later requirement introduces such logic;
- provider API keys stay in `.env`.

## 14. Synthetic data architecture

Generated agricultural data is versioned and committed as stable project data where appropriate.

Suggested path:

`data/generated/{dataset_version}/`

Generation must use a fixed seed, canonical crop registry, canonical geography registry, documented units, and deterministic output.

Do not regenerate datasets during application startup.

## 15. Logging

Local logs belong under `.tanim/logs/`.

Logs must not include plaintext passwords, API keys, or full session secrets.

Logs are ignored by Git.

## 16. Environment

`.env.example` is committed.

`.env` is local and ignored.

Runtime configuration should be read from environment settings.

## 17. Design workflow boundary

Architecture and functionality are implemented before visual refinement.

Initial frontend code must support responsive structure, semantic HTML, accessibility, shared components, and all required product states.

Do not create elaborate final styling during the foundation or core-functional phases.

When the user begins Impeccable:

- `PRODUCT.md` is product context;
- `DESIGN.md` becomes visual-system context;
- `.impeccable/` may be created by the tool;
- design changes must preserve tested functional behavior.

## 18. Expansion

The architecture should permit future Visayas and Mindanao datasets without changing the fundamental data model.

Do not implement those geographies in the current UI or dataset unless the user changes scope.
