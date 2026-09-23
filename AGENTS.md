# AGENTS.md

## Purpose

This file is the operating contract for AI coding agents working on TANIM.

TANIM is a local-first web platform for crop planning and coordination in Luzon, Philippines. It serves farmers and cooperatives. The core product helps users compare planned crop supply with a reference level before planting decisions are finalized.

Agents must preserve product scope, data meaning, repository cleanliness, accessibility, and testability.

## Required reading order

Before making changes, read these files in order:

1. `AGENTS.md`
2. `requirements/PRODUCT_REQUIREMENTS.md`
3. `requirements/ARCHITECTURE.md`
4. `requirements/DATA_SPECIFICATION.md`
5. `PRODUCT.md` when working on product-facing or frontend behavior
6. `DESIGN.md` only after the Impeccable design phase creates it

Do not invent a requirement that conflicts with these files.

## Source of truth

When files disagree, use this priority:

1. `requirements/PRODUCT_REQUIREMENTS.md` for product behavior and scope
2. `requirements/ARCHITECTURE.md` for system structure and integration
3. `requirements/DATA_SPECIFICATION.md` for data contracts, units, provenance, and coverage
4. `PRODUCT.md` for short product and design context
5. Implementation code and comments

If a conflict cannot be resolved from the repository, stop and ask the user.

## Product constraints

- Current geographic scope is Luzon only.
- Supported geographic detail is Region, Province, and Municipality or City.
- Barangay-level product behavior is out of scope.
- User-facing interfaces must support English and Tagalog.
- User-facing English should target CEFR ESL A2.
- Documentation content should target CEFR ESL B1.
- Documentation must not use em dashes or bold Markdown formatting.
- The product must work on mobile and desktop web.
- The product runs on localhost. Do not add cloud deployment work unless requested.
- New registered users must receive the first-time interactive demo.
- Seeded demo accounts must also be available.
- Authentication is intentionally simple for the MVP.
- Password reset, email verification, OTP, social login, and 2FA are out of scope.
- Privacy consent is required before normal registration is completed.
- Weather is the only core feature that may depend on live internet access.
- Weather must never silently fail. The UI must explain the connection requirement, test service reachability, and allow retry.
- The core TANIM risk engine must remain explainable and deterministic.
- Do not introduce machine learning into the core risk calculation unless the user explicitly changes the requirement.
- Visayas and Mindanao are future expansion areas and must not be presented as currently supported.

## Functional-first frontend rule

Build functionality before visual polish.

Before the Impeccable phase:

- use simple, accessible, responsive layouts;
- keep shared UI components reusable;
- implement all required states and flows;
- avoid elaborate visual systems, decorative animation, or unnecessary styling;
- do not create `DESIGN.md` unless the user starts the design phase.

After functional freeze, Impeccable may refine visual presentation. Impeccable must not change product behavior, API contracts, data meaning, accessibility, or tested flows unless the user approves the change.

## Repository rules

- Keep the repository small and organized.
- Do not duplicate shared logic across applications.
- Shared UI belongs in `packages/ui`.
- Shared localization belongs in `packages/i18n`.
- Shared TypeScript types belong in `packages/types`.
- Shared configuration belongs in `packages/config`.
- API code belongs in `services/api`.
- Risk and recommendation logic belongs in `services/engine`.
- Authoritative requirements belong in `requirements`.
- Generated datasets belong in `data/generated`.
- Canonical registries belong in `data/registry`.
- Dataset provenance and source notes belong in `data/sources`.
- Database migrations belong in `data/migrations`.
- Do not commit caches, logs, build artifacts, local runtime files, secrets, or `.env`.
- Avoid one-off temporary files in the repository root.
- Do not create duplicate specification files.

## Data rules

TANIM uses deterministic synthetic demo data for limited-access datasets.

Agents must:

- keep one canonical crop registry;
- cover every active crop in the registry across required TANIM datasets;
- use a fixed seed for generated data;
- keep units consistent;
- keep synthetic values distinguishable in metadata from live or externally observed values;
- never attribute a generated numeric value as if a government source published that exact value;
- preserve source references used for structure, range, geography, crop naming, or trend inspiration;
- keep weather data separate from synthetic agricultural data;
- never randomly regenerate production demo data at application startup.

## API and engine rules

- The frontend must not reimplement risk logic.
- The API is the boundary between frontend applications and the engine/database.
- Risk calculations must return an explanation and the inputs used.
- Invalid or missing reference values must produce an explicit non-misleading state.
- Do not divide by zero or silently substitute missing reference data.
- Dates, units, and geographic identifiers must be validated at API boundaries.
- Health endpoints must not depend on the external weather provider.

## Launcher rules

`TANIM.bat` and `STOP_TANIM.bat` are required root files.

`TANIM.bat` must:

- check required local dependencies;
- tell the user what is missing;
- ask before attempting installation;
- never silently install software;
- start TANIM services;
- wait for local health checks;
- open the landing page only when required local services are healthy;
- give a clear failure message when startup is incomplete.

`STOP_TANIM.bat` must stop TANIM-owned processes without killing unrelated Node.js, Python, browser, or PostgreSQL processes.

## Security and privacy

- Never commit passwords, API keys, access tokens, or private database credentials.
- Use `.env` locally and keep `.env.example` safe to commit.
- Hash passwords using a current password-hashing library.
- Do not store plaintext passwords.
- Do not treat service-operation consent as consent for unrelated research or secondary data use.
- Keep optional data-improvement consent separate from required service consent.

## Coding expectations

- Prefer simple implementations over abstractions that are not needed by the current product.
- Avoid microservices, message queues, vector databases, and distributed infrastructure for this MVP.
- Keep functions small enough to test.
- Use descriptive names.
- Remove dead code instead of commenting it out.
- Do not swallow exceptions without a user-safe or developer-actionable outcome.
- Do not use mock behavior in production code when a real local implementation is required.
- Keep comments focused on why, not on restating the code.

## Testing requirements

Before calling work complete:

- run the relevant frontend tests;
- run Python tests;
- verify API health;
- verify the affected flow on desktop and mobile widths;
- verify English and Tagalog do not break the layout;
- test empty, loading, success, validation, and error states when relevant;
- test first-time demo behavior when authentication or onboarding changes;
- verify deterministic data generation when data code changes;
- verify the repository contains no generated junk or secrets.

Do not weaken or delete tests to make a change pass.

## Documentation style

User documentation must be:

- CEFR ESL B1;
- direct and organized;
- written with short paragraphs and clear headings;
- free of em dashes;
- free of bold Markdown syntax;
- linked to related documentation where useful.

Code comments and internal requirements do not need to follow the no-bold rule, but clarity is still required.

## Change discipline

Before editing:

1. inspect the affected files;
2. identify the requirement being implemented;
3. reuse existing shared code where appropriate;
4. make the smallest coherent change.

After editing:

1. run relevant tests;
2. inspect changed files for accidental scope expansion;
3. update requirements only when the user has changed the requirement;
4. do not rewrite unrelated files.

## Definition of done

A change is done only when:

- required behavior works;
- tests pass;
- accessibility and responsive behavior are preserved;
- data meaning remains correct;
- no secrets or generated junk are committed;
- the repository remains organized;
- documentation is updated when behavior changed.

Working code that violates the requirements is not done.
