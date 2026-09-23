# TANIM Product Context

## Product

TANIM

Timely Agricultural Network for Informed Market

## Purpose

TANIM helps farmers and cooperatives see expected crop supply before planting decisions are finalized.

The product focuses on collective crop planning. It shows what other registered plans may contribute to the same crop and harvest period.

## Primary users

- Farmers
- Farmer cooperatives and agricultural associations

## Current geography

Luzon, Philippines.

Supported detail:

- Region
- Province
- Municipality or City

Barangay-level behavior is not part of the current product.

## Platforms

- Mobile web
- Desktop web
- Localhost only for the current MVP

## Languages

- English
- Tagalog

User-facing English should be simple and target CEFR ESL A2.

## Core value

A farmer should be able to ask:

"Before I plant this crop, is too much supply already planned for the same harvest period?"

TANIM should answer with an explainable result.

## Core flow

1. The farmer creates a planting plan.
2. TANIM combines relevant registered plans.
3. TANIM compares planned supply with a reference level.
4. TANIM shows a Low, Moderate, or High Glut Risk.
5. TANIM explains the result.
6. TANIM lets the user compare another crop.
7. The farmer can save or change the plan.
8. Cooperatives can view the collective crop picture.

## Supporting product areas

- Crop Library
- Luzon supply heatmap
- Price history
- Soil suitability
- Weather map
- Cooperative overview
- User documentation

## Data position

TANIM uses deterministic synthetic demo data where real agricultural data access is limited.

Source institutions and public datasets may be credited as references for structure, range, crop naming, geography, or trend inspiration. TANIM-generated numbers must remain identifiable as generated data in metadata.

Weather may use live API data.

## Product boundaries

The current MVP does not include:

- Visayas or Mindanao coverage
- password reset
- email verification
- OTP
- social login
- 2FA
- payments
- marketplace functions
- logistics
- chat
- AI chatbot
- machine-learning-based core risk scoring
- cloud deployment

## Design phase

Functional correctness comes first.

Impeccable will be used after the functional product is complete to define and refine the final visual system. The design phase must preserve product behavior, accessibility, responsive behavior, and data meaning.
