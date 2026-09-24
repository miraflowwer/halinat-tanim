# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary users are smallholder farmers and farmer cooperatives in Luzon, Philippines.

Farmers use TANIM before planting or while planning a crop, often on a phone, to check whether too much of the same crop is already planned for the same harvest period.

Cooperative users need a wider view of registered crop plans so they can coordinate production across members.

Users have different levels of digital experience and agricultural technical knowledge. The interface must remain usable for first-time and low-confidence users.

## Product Purpose

TANIM makes collective planting plans visible before planting decisions are finalized.

It combines registered planting plans for the same crop, place, and harvest period, compares projected planned supply with a reference level, and returns an explainable Low, Moderate, or High Glut Risk with the inputs and assumptions behind the result.

Success means a farmer can ask before planting if planned supply is already high for that period, understand the answer, compare another crop, and save or change the plan. Success for cooperatives means seeing the collective picture to support coordination.

The product supports coordination. It does not promise a market outcome.

## Positioning

TANIM considers what other registered farmers or cooperative members are already planning for the same crop, place, and harvest period, instead of recommending a crop only from historical price or individual farm conditions.

Its risk result is deterministic and explainable, shows its inputs, and keeps its assumptions visible.

## Operating Context

Core planting-plan flow:

1. User chooses a supported Luzon location at Region, Province, or Municipality or City level.
2. User chooses a crop from the canonical registry.
3. User enters farm area, planting date, and expected harvest period.
4. TANIM retrieves relevant registered plans and the applicable reference level.
5. TANIM calculates supply pressure and returns Low, Moderate, or High Glut Risk with an explanation.
6. User can compare another crop, then save, change, or cancel the plan.
7. Cooperatives can view the aggregated crop picture by period.

Product surfaces, all local web on localhost:

- Public landing site, default `http://127.0.0.1:3000`, opened by `TANIM.bat` after health checks pass.
- Authentication site, default `http://127.0.0.1:3001`, with privacy consent, registration, login, logout, and session handoff.
- Farmer and cooperative platform, default `http://127.0.0.1:3002`, with dashboard, plans, Crop Library, supply map, price history, soil suitability, weather, account or settings, and help link.
- Documentation site, default `http://127.0.0.1:3003`, with left navigation on desktop and drawer on mobile.

Every normal registration completes a first-time interactive demo from isolated demo state, covering purpose, sample plan, community contribution, example risk, crop comparison, collective view, and a clear action to start. A replay action is available from Help or Settings. Seeded farmer and cooperative demo accounts exist for testing.

Weather is the only core feature that may use live internet data. The UI explains the connection requirement, checks service reachability on user request, loads only on success, shows a direct failure message with retry, and never blocks the rest of TANIM.

## Capabilities and Constraints

Confirmed capabilities:

- Luzon-only coverage at Region, Province, and Municipality or City. No barangay workflows.
- English and Tagalog interface. Language switch does not require logout. Layouts tolerate longer translations.
- User-facing English targets CEFR ESL A2.
- Planting-plan CRUD, explainable risk check, crop comparison, cooperative aggregate view.
- Crop Library, Luzon supply heatmap with Low, Moderate or Balanced, High, and No Data states, price history with units and metadata, soil suitability kept separate from supply pressure, and weather with explicit offline handling.
- Deterministic Glut Risk: `Supply Pressure Ratio = Projected Planned Supply / Reference Requirement`. Prototype thresholds below 0.90 Low, 0.90 through 1.10 Moderate, above 1.10 High, configurable and documented. Missing or zero reference produces an explicit non-misleading state, never a fake score or silent substitution.
- Deterministic synthetic demo data where real access is limited, with fixed seed, versioned output, stable committed datasets, and provenance metadata including dataset version and data kind. Generated numbers stay identifiable as generated and are never presented as exact values published by a government source. Weather data stays separate as live external data.
- Simple localhost authentication with hashed passwords, Farmer or Cooperative roles, recorded privacy notice version and timestamp, and separate optional data-improvement consent. No password reset, email verification, OTP, social login, or 2FA in the MVP.
- API is the boundary for persisted data and risk calculation. The frontend does not reimplement risk logic. Health endpoints do not depend on the weather provider.
- Focused and lightweight experience. No dashboard clutter, unnecessary decoration, excessive animation, or enterprise-style complexity.
- Existing CSS and placeholder components are functional scaffolding only, not binding brand decisions, and may be redesigned.

Explicitly out of scope unless the user changes the requirement: Visayas or Mindanao coverage, barangay workflows, native mobile apps, payments, marketplace, logistics, chat, AI chatbot, machine-learning core risk scoring, automated ingestion from every government source, advanced organization administration, and cloud deployment.

No open product decisions carried forward from this round. Visual world and surface strategy belong to later new-work, not to this record.

## Brand Commitments

Name is TANIM, Timely Agricultural Network for Informed Market.

Voice is simple and direct. No binding logo, palette, typography, imagery, or component system is recorded. Existing colors, typography, cards, spacing, and borders are pre-design scaffolding and are not brand commitments.

Volunteered direction recorded without expansion: TANIM should feel credible, calm, practical, agricultural, local, and public-service oriented rather than like a generic SaaS dashboard.

## Evidence on Hand

Working sources in this repository:

- `requirements/PRODUCT_REQUIREMENTS.md`, `requirements/ARCHITECTURE.md`, `requirements/DATA_SPECIFICATION.md`
- `AGENTS.md`
- Four app scaffolds under `apps/landing`, `apps/auth`, `apps/platform`, `apps/docs`
- Shared layers under `packages/ui`, `packages/i18n`, `packages/types`, `packages/config`
- API and engine under `services/api` and `services/engine`
- Registries, generated datasets, sources, seeds, and migrations under `data/`

Absences future work must not fabricate: no testimonials, adoption figures, accuracy percentages, government endorsements, customer logos, or other proof the project does not have. Do not invent them in copy or design.

## Product Principles

1. Coordination over prediction. Show what is planned together, do not guarantee what the market will do.
2. Explainability before confidence. Every risk result shows its inputs, reference, and assumptions.
3. Inclusive and lightweight. Work for varied digital experience on phone and desktop, with simple language and no clutter.
4. Honest local data. Stay Luzon-only, keep synthetic values labeled, and keep provenance traceable.
5. Function first. Preserve behavior, accessibility, responsive flow, and data meaning through any visual change.

## Accessibility & Inclusion

Users include people with low digital confidence and varied technical vocabulary. Guidance must use plain steps.

Required behavior:

- Mobile widths from about 360 px and desktop layouts around 1280 px to 1440 px and above, with no required horizontal page scrolling on normal mobile views.
- Keyboard access for interactive controls, visible focus states, semantic form labels, readable text sizes, adequate contrast, and touch targets suitable for mobile use.
- No core action that depends only on hover. No meaning communicated by color alone. Map and chart color states always pair with labels or patterns.
- English and Tagalog must not break layout. Tagalog should read naturally, not as word-for-word translation.
