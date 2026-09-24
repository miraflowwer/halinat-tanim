# Phase 5 Farmer and Cooperative Platform

## Scope

Phase 5 replaces the signed-in home placeholder with a working Farmer and Cooperative platform. It includes the platform shell, dashboards, planting plans, risk preview, and basic account settings. Crop Library, Supply Map, Price History, Soil Suitability, Weather, and final visual design are outside this phase.

The platform supports Luzon regions, provinces, and municipalities or cities. Barangay planning is not supported.

## Farmer workflow

A Farmer chooses a location and crop, enters the planned area, planting date, and expected harvest dates, then checks Glut Risk. The risk check uses `POST /risk/check`. TANIM shows the returned risk, explanation, reference, and any crop comparisons. Checking risk does not save a plan.

The Farmer can save after checking risk. The platform clears the result when a risk input changes and requires another check before saving. The API validates the plan again when it is saved. A saved plan is not a promise about future risk. Other plans can change the result later.

The Farmer dashboard shows active plans, upcoming harvests, and links to plan actions. The plan list shows the crop, location, area, dates, and status. Users can open, edit, or cancel their own plans.

## Plan lifecycle and ownership

New plans use the existing `planting_plans` table and start with `active` status. An edit updates the row and its `updated_at` value. An edit to risk inputs requires a fresh preview in the normal interface. The API still validates each change independently.

Cancel changes the status to `cancelled`; it does not delete the row. The Phase 3 risk engine uses active plans, so a cancelled plan no longer contributes to risk. Completed plans cannot be cancelled or edited.

Plan reads and changes use the signed-in user ID from the session. Farmers can access only their own plans. The browser cannot set a plan owner or organization. State-changing plan requests require the current session's CSRF token.

## Cooperative overview

Cooperative users can view active plans linked to their organization. The overview groups plans by crop, municipality or city, and configured planning period. It shows plan counts, area totals, and risk context returned by the Phase 3 engine.

The organization comes from the signed-in user's membership. The overview does not return Farmer names, email addresses, or user IDs. Plans from another organization are not included. The Cooperative role does not give access to Farmers' personal plan pages.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/crops` | List active crop choices |
| `GET` | `/geographies` | List active Luzon geography choices |
| `GET` | `/planning-periods` | List periods supported by the Phase 3 engine |
| `GET` | `/plans` | List the signed-in user's plans |
| `POST` | `/plans` | Create a validated plan |
| `GET` | `/plans/{plan_id}` | Read one plan owned by the signed-in user |
| `PATCH` | `/plans/{plan_id}` | Change one active plan owned by the signed-in user |
| `DELETE` | `/plans/{plan_id}` | Cancel a plan owned by the signed-in user |
| `GET` | `/cooperative/overview` | Read organization plan totals and risk context |
| `POST` | `/risk/check` | Preview risk and crop comparisons without saving |

The plan endpoints reject inactive crops, unsupported locations, invalid areas or dates, and harvest periods that the engine does not support. Responses use safe error messages and do not expose SQL details.

## Routes and language

The authenticated platform uses `/dashboard`, `/plans`, `/plans/new`, `/plans/{id}`, `/plans/{id}/edit`, `/settings`, and `/demo`. Cooperative accounts use `/cooperative`. The old `/home` route sends the user to the role-appropriate dashboard.

New platform text is available in English and Tagalog through the shared localization package. English copy uses short, simple sentences. Desktop navigation prepares links for later utilities. Crops, Map, and Weather remain unavailable in Phase 5. Mobile navigation includes Dashboard, Plans, Add Plan, Explore, and Menu.

## Non-goals

Phase 5 does not build exploration utilities, weather, documentation content, advanced Cooperative administration, financial forecasts, a new risk formula, or final visual design. The Phase 3 engine remains the only source for risk results.
