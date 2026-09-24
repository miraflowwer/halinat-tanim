# TANIM Product Requirements

## 1. Purpose

This document is the authoritative product scope for the TANIM MVP.

TANIM helps farmers and cooperatives coordinate crop plans before harvest periods overlap. It combines registered planting plans with a reference level and shows an explainable Glut Risk.

The product is based on the submitted TANIM concept note for the NextGen Agri Hackathon. The concept note describes farmer-entered crop plans, expected harvest timing, collective planning, market and demand comparison, a Glut Risk indicator, crop alternatives, agricultural datasets, and weather information.

## 2. Product goals

TANIM must:

1. help a farmer check a crop plan before planting;
2. show how registered community plans affect expected supply;
3. compare expected planned supply with a reference level;
4. return an explainable Low, Moderate, or High Glut Risk;
5. allow crop comparison;
6. give cooperatives a collective planning view;
7. provide crop, price, suitability, supply-map, and weather context;
8. remain understandable on mobile and desktop;
9. support English and Tagalog;
10. run locally for the hackathon MVP.

## 3. Current scope

### 3.1 Geography

Current supported area:

- Luzon, Philippines

Supported geographic hierarchy:

- Region
- Province
- Municipality or City

Barangay detail is out of scope.

Visayas and Mindanao are future expansion areas.

### 3.2 Crop scope

The product uses one authoritative TANIM Crop Registry.

The registry covers crops relevant to agricultural production and market coordination in Luzon. It may include fruits, vegetables, root crops, legumes, herbs, spices, and other commonly marketed horticultural produce.

The current MVP excludes livestock, fisheries, ornamental plants, and broad staple or plantation categories unless the user later adds them to the registry scope.

A crop is not considered supported until all required TANIM datasets and product views can handle it.

### 3.3 Platforms

Required:

- desktop web;
- mobile web;
- Windows localhost development.

Cloud hosting is out of scope.

## 4. User groups

### 4.1 Farmer

A farmer can:

- register and log in;
- provide required privacy consent;
- complete the first-time demo;
- create a planting plan;
- check Glut Risk;
- read the explanation;
- compare crops;
- save, edit, and remove their own plans;
- browse crop information;
- view supply, price, suitability, and weather information.

### 4.2 Cooperative

A cooperative user can:

- log in;
- complete the first-time demo when applicable;
- view aggregated crop plans for the cooperative;
- view crop supply pressure by period;
- inspect relevant crop and geographic context;
- use the same crop, map, price, suitability, and weather utilities.

The MVP does not require advanced organization administration.

## 5. Product surfaces

TANIM uses four local web applications.

### 5.1 Public landing website

Required content:

- TANIM identity;
- short explanation of the problem and solution;
- how TANIM works;
- Luzon coverage;
- core features;
- links to Login, Register, and Documentation.

The landing page is the page opened by `TANIM.bat`.

### 5.2 Authentication website

Required:

- privacy consent step;
- registration;
- login;
- logout/session behavior;
- clear validation and error messages.

Not required:

- password reset;
- email verification;
- OTP;
- social login;
- 2FA.

### 5.3 Farmer and cooperative platform

Required main areas:

- Dashboard
- Plans
- Crop Library
- Supply Map
- Price History
- Soil Suitability
- Weather
- Account or Settings
- Help or Documentation link

### 5.4 Documentation website

Required documentation areas:

1. Introduction
2. Getting Started
3. Farmer Guide
4. Cooperative Guide
5. Crop Information
6. Maps and Weather
7. TANIM Engine
8. Data
9. Limitations
10. Help and FAQ
11. Ethics and Legal

Legal and ethics content must include, as applicable:

- ethics;
- privacy;
- data privacy;
- terms of service;
- copyright;
- licensing;
- third-party data and services;
- open-source software notices.

## 6. Core planting-plan flow

The required core flow is:

1. user chooses or confirms a supported Luzon location;
2. user chooses a crop;
3. user enters farm area;
4. user enters planting date;
5. user enters or confirms expected harvest period;
6. TANIM retrieves relevant registered plans;
7. TANIM retrieves the applicable reference level;
8. TANIM calculates supply pressure;
9. TANIM returns a risk level and explanation;
10. TANIM offers relevant crop comparison;
11. user saves, changes, or cancels the plan.

The engine result must not be presented as a guaranteed market outcome.

## 7. Explainable Glut Risk

The MVP uses a deterministic, explainable calculation.

Baseline concept:

`Supply Pressure Ratio = Projected Planned Supply / Reference Requirement`

Initial prototype thresholds may use:

- Low: ratio below 0.90
- Moderate: ratio from 0.90 through 1.10
- High: ratio above 1.10

These thresholds are prototype assumptions. They must be configurable and documented.

Every result must return enough information to explain:

- crop;
- geography;
- harvest period;
- planned supply;
- reference level;
- ratio;
- risk level;
- contributing plans or aggregate count where appropriate;
- data version;
- assumptions;
- explanation.

Missing or invalid reference data must not produce a fake risk score.

## 8. First-time demo

Every normally registered user must receive a first-time interactive demo.

The demo must:

1. explain the purpose of TANIM;
2. show a sample planting plan;
3. show how community plans contribute to the result;
4. show an example Glut Risk;
5. show a crop comparison;
6. show the cooperative or collective view;
7. end with a clear action to start using TANIM.

After the demo:

- normal user data starts from the real default state;
- temporary demo state must not contaminate normal user records;
- the account records that the first-time demo was completed.

A replay action should be available from Help or Settings.

## 9. Demo accounts

The local project must include seeded demo accounts for reliable judging and testing.

At minimum:

- one farmer account;
- one cooperative account.

Seeded credentials must be development-only and documented in local development material, not embedded into production-facing UI.

## 10. Localization

Required interface languages:

- English
- Tagalog

Requirements:

- language switching must not require logout;
- selected language should persist for the user when possible;
- important units and numeric meaning must remain consistent across languages;
- layouts must tolerate longer translated strings;
- user-facing English should target CEFR ESL A2;
- Tagalog should be natural and not a word-for-word translation.

## 11. Responsive and accessibility requirements

TANIM must support:

- mobile widths from about 360 px;
- desktop layouts around 1280 px to 1440 px and above;
- keyboard access for interactive controls;
- visible focus states;
- semantic form labels;
- readable text sizes;
- adequate contrast;
- touch targets suitable for mobile use;
- no core action that depends only on hover;
- no meaning communicated by color alone;
- no required horizontal page scrolling on normal mobile views.

Maps and charts may use horizontal interaction inside their own bounded component when necessary.

## 12. Crop Library

The Crop Library must allow users to search and open supported crops.

Each supported crop should be able to expose:

- English name;
- Tagalog or common name where available;
- scientific name where available;
- crop category;
- overview;
- price history;
- supply context;
- soil suitability;
- growing-condition context;
- weather context;
- data/source metadata.

## 13. Supply heatmap

The supply map is limited to supported Luzon geography.

Users must be able to filter by:

- crop;
- period;
- supply level or risk context.

The map must distinguish:

- Low
- Moderate or Balanced
- High
- No Data

Color must not be the only indicator.

A selected area should expose readable numeric context and a path to details.

The current Supply Map visualization is Region level. It does not replace
Municipality or City geography used by crop planning and risk checks.

## 14. Price history

Price history must support:

- crop selection;
- location selection where data supports it;
- clear unit display;
- time-series chart;
- accessible value inspection;
- source/data metadata.

Synthetic prototype price records must be deterministic.

## 15. Soil suitability

Suitability categories should include:

- Suitable
- Moderately Suitable
- Low Suitability
- No Data

Suitability must not be treated as the same concept as supply pressure.

A crop can be highly suitable for a location while still having High Glut Risk.

## 16. Weather

Weather may use a live API.

Before requesting live weather:

1. the interface explains that an internet connection is required;
2. the user chooses to continue;
3. TANIM checks whether the weather service is reachable;
4. weather loads only when the request succeeds.

When it fails, show a direct message such as:

"TANIM cannot connect to the weather service. Check your internet connection and try again."

Provide a Retry action.

Weather failure must not block the rest of TANIM.

The weather provider must not be part of the main local health-check requirement.

## 17. Data privacy consent

Registration must present the privacy notice before account creation completes.

Required service consent and optional data-improvement consent must be separate.

A user must not be forced to consent to unrelated secondary data use in order to access the required service.

The database must record:

- privacy notice version;
- acceptance timestamp;
- optional data-improvement choice when present.

## 18. Synthetic demo data

Because agricultural data access is limited, TANIM may use realistic deterministic synthetic data for:

- prices;
- planned and reference supply;
- suitability;
- crop context;
- other non-live MVP datasets.

Requirements:

- synthetic values are generated once for a dataset version;
- the same dataset version produces the same values;
- generated values are not randomly changed at application startup;
- public sources may be credited as references for structure, crop naming, geographic coverage, ranges, or trends;
- generated numeric values must not be falsely presented as exact values published by those institutions;
- metadata must preserve the dataset type and version.

The product does not require a large warning banner on every screen.

## 19. Documentation writing rules

User documentation must:

- use CEFR ESL B1;
- use clear headings and subheadings;
- use short paragraphs;
- use direct instructions;
- avoid em dashes;
- avoid bold Markdown syntax;
- use descriptive links to related documentation;
- remain usable on mobile.

Desktop documentation should use a left navigation area with the main article content using the remaining width.

## 20. Out of scope

Unless the user changes the requirements, do not add:

- Visayas support;
- Mindanao support;
- barangay-level workflows;
- native mobile apps;
- password reset;
- email verification;
- OTP;
- social login;
- 2FA;
- payment processing;
- marketplace transactions;
- logistics;
- messaging or chat;
- AI chatbot;
- machine-learning core risk scoring;
- automated production ingestion from every government data source;
- advanced LGU administration;
- cloud deployment.

## 21. MVP acceptance criteria

The MVP is functionally acceptable when:

- all four local web applications start;
- the API is healthy;
- PostgreSQL-backed registration and login work;
- privacy consent is recorded;
- first-time demo works for new registrations;
- seeded demo accounts work;
- planting plans persist;
- Glut Risk is deterministic and explainable;
- crop comparison works;
- the cooperative aggregate view works;
- Crop Library works for every active registry crop;
- supply heatmap works for supported Luzon geography;
- price history works;
- soil suitability works;
- weather handles both reachable and unreachable states;
- English and Tagalog work;
- mobile and desktop core flows work;
- documentation is navigable;
- `TANIM.bat` starts TANIM and opens the landing page only after local health checks pass;
- `STOP_TANIM.bat` stops TANIM-owned processes cleanly.
