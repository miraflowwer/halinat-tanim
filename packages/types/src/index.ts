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
