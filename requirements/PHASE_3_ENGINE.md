# Phase 3 Explainable Glut Risk Engine

## Purpose

Phase 3 adds a deterministic preview for a proposed planting plan. It uses active registered planting plans and a configured future reference level. A preview does not save a planting plan.

## Formula and assumptions

```text
Projected Planned Area = Existing Relevant Planned Area + Proposed Area
Supply Pressure Ratio = Projected Planned Area / Reference Area
```

The engine assumption version is `grci-v1`. The thresholds are Low below 0.90, Moderate from 0.90 through 1.10, and High above 1.10. Decimal arithmetic is used and the ratio is not rounded before classification. These engine thresholds are conceptually separate from the Phase 2 snapshot labels.

## Harvest periods

The engine reads the future quarterly periods from `data/dataset_config.json`. A request whose start and end dates are inside one configured quarter returns that normalized quarter. A request that crosses quarters returns a clear validation error. Dates outside the configured horizon are unsupported.

## Data used

Existing area comes only from active `planting_plans` rows for the same active crop and supported municipality or city. A plan is included when its expected harvest overlaps the normalized period. Cancelled, completed, other-crop, other-location, and non-overlapping plans are excluded.

The denominator comes from one `crop_references` row for the active configured dataset version, crop, municipality or city, normalized period, and `period_kind = future_planning`. A missing or non-positive reference returns `status: unavailable`, with null ratio and risk. The engine never uses `supply_snapshots` as registered plans.

## API contract

`POST /risk/check` accepts:

```json
{
  "crop_id": "tomato",
  "geography_id": "mun_0304903000",
  "proposed_area_ha": 8,
  "harvest_start": "2027-01-15",
  "harvest_end": "2027-03-15",
  "comparison_crop_ids": ["eggplant"]
}
```

An available response includes the requested dates, normalized planning period, existing area, proposed area, projected area, reference area, ratio, risk, contributing plan count, assumption version, dataset version, a deterministic explanation, and comparisons.

Comparisons are informational. Each comparison reports current pressure and the hypothetical pressure if the same proposed area were added. Missing comparison references remain unavailable. Comparisons are sorted by projected ratio when available and are not agronomic, profit, or guaranteed market recommendations.

## Non-goals

Phase 3 does not add authentication, planting-plan CRUD, dashboards, maps, weather, frontend pages, soil-based ranking, machine learning, or market guarantees.
