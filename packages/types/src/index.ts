export type Language = "en" | "tl";

export type AppSurface = "landing" | "auth" | "platform" | "docs";

export type UserRole = "farmer" | "cooperative";

export type RiskLevel = "low" | "moderate" | "high";

export type AuthUser = {
  user_id: number;
  display_name: string;
  email: string;
  role: UserRole;
  preferred_language: Language;
  has_completed_demo: boolean;
};

export type AuthenticatedResponse = {
  authenticated: true;
  user: AuthUser;
  csrf_token: string;
};

export type UnauthenticatedResponse = {
  authenticated: false;
  user: null;
  code?: string;
};

export type SessionResponse = AuthenticatedResponse | UnauthenticatedResponse;

export type DemoScenario = {
  scenario_id: string;
  crop_id: string;
  crop_name_en: string;
  crop_name_tl: string | null;
  geography_id: string;
  geography_name: string;
  period_start: string;
  period_end: string;
  existing_planned_area_ha: number;
  proposed_area_ha: number;
  projected_area_ha: number;
  reference_area_ha: number;
  ratio: number;
  risk: RiskLevel;
  explanation?: string | null;
};

export type DemoComparison = {
  scenario_id: string;
  crop_id: string;
  crop_name_en: string;
  crop_name_tl: string | null;
  geography_id: string;
  geography_name: string;
  period_start: string;
  period_end: string;
  existing_planned_area_ha: number;
  proposed_area_ha: number;
  reference_area_ha: number;
  current_ratio: number;
  current_risk: RiskLevel;
  projected_ratio_if_same_area: number;
  projected_risk_if_same_area: RiskLevel;
};

export type DemoResponse = {
  dataset_version: string;
  data_kind: "synthetic_demo";
  primary: DemoScenario;
  comparison: DemoComparison;
};

export type CropLookup = {
  crop_id: string;
  canonical_name_en: string;
  canonical_name_tl: string | null;
  scientific_name: string | null;
  category: string;
};

export type GeographyLevel = "region" | "province" | "municipality_city";

export type GeographyLookup = {
  geography_id: string;
  name: string;
  level: GeographyLevel;
  parent_geography_id: string | null;
};

export type PlanningPeriod = {
  period_start: string;
  period_end: string;
};

export type PlanStatus = "active" | "cancelled" | "completed";

export type PlantingPlan = {
  plan_id: number;
  crop_id: string;
  crop_name_en: string;
  crop_name_tl: string | null;
  geography_id: string;
  geography_name: string;
  area_ha: number;
  planting_date: string;
  harvest_start: string;
  harvest_end: string;
  status: PlanStatus;
};

export type PlantingPlanInput = {
  crop_id: string;
  geography_id: string;
  area_ha: number;
  planting_date: string;
  harvest_start: string;
  harvest_end: string;
};

export type RiskComparison = {
  crop_id: string;
  existing_planned_area_ha: number;
  reference_area_ha: number | null;
  current_ratio: number | null;
  current_risk: RiskLevel | null;
  projected_ratio_if_same_area: number | null;
  projected_risk_if_same_area: RiskLevel | null;
};

export type RiskCheckResponse = {
  status: "available" | "unavailable";
  crop_id: string;
  geography_id: string;
  requested_harvest_start: string;
  requested_harvest_end: string;
  planning_period_start: string;
  planning_period_end: string;
  existing_planned_area_ha: number;
  proposed_area_ha: number;
  projected_planned_area_ha: number;
  reference_area_ha: number | null;
  ratio: number | null;
  risk: RiskLevel | null;
  contributing_plan_count: number;
  assumption_version: string;
  dataset_version: string;
  explanation: string;
  comparisons: RiskComparison[];
};

export type CooperativeRiskContext = {
  status: "available" | "unavailable";
  risk: RiskLevel | null;
  planned_area_ha: number;
  reference_area_ha: number | null;
  ratio: number | null;
  contributing_plan_count: number;
  assumption_version: string;
  dataset_version: string;
  explanation: string;
};

export type CooperativeAggregate = {
  crop_id: string;
  crop_name_en: string;
  crop_name_tl: string | null;
  geography_id: string;
  geography_name: string;
  period_start: string;
  period_end: string;
  plan_count: number;
  planned_area_ha: number;
  community_risk: CooperativeRiskContext;
};

export type CooperativeOverview = {
  organization_name: string;
  total_active_plan_count: number;
  total_planned_area_ha: number;
  aggregates: CooperativeAggregate[];
};
