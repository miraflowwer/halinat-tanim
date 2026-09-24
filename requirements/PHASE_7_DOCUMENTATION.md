# Phase 7 Documentation Website

## Scope

Replace the documentation placeholder with a local, responsive, bilingual TANIM documentation site at `http://127.0.0.1:3003`. It serves farmers, cooperative users, judges, and future developers. It describes behavior supported by the integrated Phase 1 to Phase 6 implementation and the Phase 8 audit fixes.

## Information architecture

The site has Introduction, Getting Started, Farmer Guide, Cooperative Guide, Crop Information, Maps and Weather, TANIM Engine, Data, Limitations, Help and FAQ, and Ethics and Legal sections. Pages use stable paths, page metadata, related links, local search, and a documentation-specific not-found view.

Routes are `/`, `/getting-started`, `/farmers`, `/cooperatives`, `/crops`, `/crops/prices`, `/crops/suitability`, `/maps`, `/maps/supply`, `/maps/weather`, `/engine`, `/engine/risk-levels`, `/engine/example`, `/data`, `/data/sources`, `/data/synthetic-data`, `/data/geography`, `/limitations`, `/help/faq`, `/legal/privacy`, `/legal/ethics`, `/legal/terms`, and `/legal/copyright`.

## Language and writing

Every page has English and Tagalog content. English targets CEFR ESL B1. Text uses short sentences, clear headings, direct explanations, and common words. Documentation prose has no em dash or Markdown bold syntax. The selected language persists locally and does not change the page route.

## Sources and accuracy

Product, architecture, data, Phase 3 engine, source, fixture, and license claims must be checked against the repository. Generated agricultural values are identified as TANIM synthetic demo data. External sources are described only for uses and terms recorded in `data/sources/SOURCES.md`. Missing project license or copyright facts are not guessed.

## Accessibility and mobile behavior

Pages use semantic landmarks, one article heading, descriptive links, visible focus, a skip link, keyboard-accessible navigation, and an accessible language selector. Desktop uses persistent left navigation. Mobile uses a collapsible navigation and must remain readable without page-level horizontal scroll at 360 px.

## Legal and ethics coverage

Documentation covers privacy status, practical ethics, prototype terms, copyright, licenses, and open-source notices. It does not invent retention periods, deletion promises, legal compliance, endorsement, or licenses.

## Parallel-work reconciliation

Phase 4 to Phase 6 behavior was checked against the integrated implementation during the Phase 8 audit. The documentation covers the verified registration, consent, demo, planting-plan, cooperative overview, crop, price, suitability, map, and weather flows. `apps/docs/src/content/reconciliation.ts` is empty because no phase reconciliation records remain.

## Non-goals

This phase does not redesign the other TANIM applications, change engine or product behavior, add a documentation framework or external search service, or add cloud deployment.
