import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type {
  AuthUser,
  CooperativeOverview,
  CropLookup,
  GeographyLookup,
  PlantingPlan,
  PlanningPeriod,
  RiskCheckResponse,
} from "@tanim/types";
import { setCsrfToken } from "@tanim/api-client";
import { PlatformPage } from "./PlatformPages";
import { resolveProtectedRoute } from "./navigation";

const farmer: AuthUser = {
  user_id: 1,
  display_name: "Mila Santos",
  email: "mila@example.test",
  role: "farmer",
  preferred_language: "en",
  has_completed_demo: true,
};

const cooperative: AuthUser = {
  ...farmer,
  user_id: 2,
  display_name: "Central Luzon Cooperative",
  email: "coop@example.test",
  role: "cooperative",
};

const crops: CropLookup[] = [
  {
    crop_id: "tomato",
    canonical_name_en: "Tomato",
    canonical_name_tl: "Kamatis",
    scientific_name: null,
    category: "vegetable",
  },
  {
    crop_id: "eggplant",
    canonical_name_en: "Eggplant",
    canonical_name_tl: "Talong",
    scientific_name: null,
    category: "vegetable",
  },
];

const geographies: GeographyLookup[] = [
  { geography_id: "region_iii", name: "Central Luzon", level: "region", parent_geography_id: null },
  { geography_id: "province_ne", name: "Nueva Ecija", level: "province", parent_geography_id: "region_iii" },
  { geography_id: "mun_cabanatuan", name: "Cabanatuan City", level: "municipality_city", parent_geography_id: "province_ne" },
];

const period: PlanningPeriod = { period_start: "2027-01-01", period_end: "2027-03-31" };

const plan: PlantingPlan = {
  plan_id: 7,
  crop_id: "tomato",
  crop_name_en: "Tomato",
  crop_name_tl: "Kamatis",
  geography_id: "mun_cabanatuan",
  geography_name: "Cabanatuan City, Nueva Ecija, Central Luzon",
  area_ha: 8,
  planting_date: "2026-10-01",
  harvest_start: period.period_start,
  harvest_end: period.period_end,
  status: "active",
};

const riskResult: RiskCheckResponse = {
  status: "available",
  crop_id: "tomato",
  geography_id: "mun_cabanatuan",
  requested_harvest_start: period.period_start,
  requested_harvest_end: period.period_end,
  planning_period_start: period.period_start,
  planning_period_end: period.period_end,
  existing_planned_area_ha: 12,
  proposed_area_ha: 8,
  projected_planned_area_ha: 20,
  reference_area_ha: 25,
  ratio: 0.8,
  risk: "low",
  contributing_plan_count: 2,
  assumption_version: "grci-v1",
  dataset_version: "demo-2026-09-v4",
  explanation: "Registered Tomato plans total 12 ha. Adding 8 ha gives 20 ha against 25 ha.",
  comparisons: [
    {
      crop_id: "eggplant",
      existing_planned_area_ha: 5,
      reference_area_ha: 25,
      current_ratio: 0.2,
      current_risk: "low",
      projected_ratio_if_same_area: 0.52,
      projected_risk_if_same_area: "low",
    },
  ],
};

function installApi(
  handler: (path: string, method: string, body: unknown) => unknown,
) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = new URL(String(input)).pathname;
    const body = init?.body ? JSON.parse(String(init.body)) as unknown : null;
    const payload = handler(path, init?.method ?? "GET", body);
    return new Response(JSON.stringify(payload), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function commonProps(user: AuthUser = farmer, language: "en" | "tl" = "en") {
  return {
    user,
    language,
    onLanguageChange: vi.fn(),
    onLogout: vi.fn(),
  };
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setCsrfToken(null);
  window.history.replaceState({}, "", "/dashboard");
});

describe("authenticated platform pages", () => {
  it("shows the Farmer dashboard and active plan count", async () => {
    installApi((path) => path === "/plans" ? [plan] : {});
    render(<PlatformPage path="/dashboard" {...commonProps()} />);

    expect(await screen.findByRole("heading", { name: "Welcome back, Mila Santos" })).toBeTruthy();
    expect(screen.getByText("Active plans")).toBeTruthy();
    expect(screen.getByText("Add a plan")).toBeTruthy();
    expect(screen.getAllByText("Tomato").length).toBeGreaterThan(0);
  });

  it("shows only the Cooperative aggregate overview", async () => {
    const overview: CooperativeOverview = {
      organization_name: "Central Luzon Cooperative",
      total_active_plan_count: 1,
      total_planned_area_ha: 8,
      aggregates: [
        {
          crop_id: "tomato",
          crop_name_en: "Tomato",
          crop_name_tl: "Kamatis",
          geography_id: "mun_cabanatuan",
          geography_name: plan.geography_name,
          period_start: period.period_start,
          period_end: period.period_end,
          plan_count: 1,
          planned_area_ha: 8,
          community_risk: {
            status: "available",
            risk: "low",
            planned_area_ha: 20,
            reference_area_ha: 25,
            ratio: 0.8,
            contributing_plan_count: 3,
            assumption_version: "grci-v1",
            dataset_version: "demo-2026-09-v4",
            explanation: "Registered Tomato plans total 20 ha against a 25 ha reference.",
          },
        },
      ],
    };
    installApi((path) => path === "/cooperative/overview" ? overview : {});
    const user = userEvent.setup();
    render(<PlatformPage path="/dashboard" {...commonProps(cooperative)} />);

    expect(await screen.findByRole("heading", { name: /Central Luzon Cooperative/ })).toBeTruthy();
    expect(screen.getByText("Active plans in your cooperative")).toBeTruthy();
    expect(screen.getByText("Low (0.8)")).toBeTruthy();
    await user.click(screen.getByText("Risk details"));
    expect(screen.getByText("Registered Tomato plans total 20 ha against a 25 ha reference.")).toBeTruthy();
    expect(screen.getByText(/Plans in this check: 3/)).toBeTruthy();
  });

  it("shows the Plans empty state in English and Tagalog", async () => {
    installApi((path) => path === "/plans" ? [] : {});
    const view = render(<PlatformPage path="/plans" {...commonProps()} />);
    expect(await screen.findByRole("heading", { name: "No plans yet" })).toBeTruthy();
    view.rerender(<PlatformPage path="/plans" {...commonProps(farmer, "tl")} />);
    expect(await screen.findByRole("heading", { name: "Wala pang plano" })).toBeTruthy();
  });

  it("shows working context links in Explore", () => {
    render(<PlatformPage path="/explore" {...commonProps()} />);
    const explore = screen.getByRole("main");

    expect(explore.querySelector('a[href="/crops"]')).toBeTruthy();
    expect(explore.querySelector('a[href="/prices"]')).toBeTruthy();
    expect(explore.querySelector('a[href="/suitability"]')).toBeTruthy();
    expect(explore.querySelector('a[href="/map"]')).toBeTruthy();
    expect(explore.querySelector('a[href="/weather"]')).toBeTruthy();
  });

  it("checks risk before saving and clears a preview when form inputs change", async () => {
    const requests: Array<{ path: string; method: string; body: unknown }> = [];
    installApi((path, method, body) => {
      requests.push({ path, method, body });
      if (path === "/crops") return { items: crops, total: crops.length, categories: ["vegetable"], dataset_version: "demo-2026-09-v4" };
      if (path === "/geographies") return { items: geographies, dataset_version: "demo-2026-09-v4" };
      if (path === "/planning-periods") return [period];
      if (path === "/risk/check") return riskResult;
      if (path === "/plans" && method === "POST") {
        return { ...plan, ...(body as Record<string, unknown>), plan_id: 8 };
      }
      return [];
    });
    const user = userEvent.setup();
    const view = render(<PlatformPage path="/plans/new" {...commonProps()} />);

    await screen.findByLabelText("Crop");
    await user.selectOptions(screen.getByLabelText("Crop"), "tomato");
    await user.selectOptions(screen.getByLabelText("Region"), "region_iii");
    await user.selectOptions(screen.getByLabelText("Province"), "province_ne");
    await user.selectOptions(screen.getByLabelText("Municipality or city"), "mun_cabanatuan");
    await user.type(screen.getByLabelText("Farm area (ha)"), "8");
    await user.type(screen.getByLabelText("Planting date"), "2026-10-01");
    await user.selectOptions(
      screen.getByLabelText("Harvest period"),
      `${period.period_start}|${period.period_end}`,
    );
    await user.click(screen.getByLabelText("Eggplant"));

    const save = screen.getByRole("button", { name: "Save plan" });
    expect((save as HTMLButtonElement).disabled).toBe(true);
    await user.click(screen.getByRole("button", { name: "Check Glut Risk" }));
    expect(await screen.findByRole("heading", { name: "Risk preview" })).toBeTruthy();
    expect(screen.getByText("Low")).toBeTruthy();
    expect(screen.getAllByText("Eggplant").length).toBeGreaterThan(0);

    await user.clear(screen.getByLabelText("Farm area (ha)"));
    await user.type(screen.getByLabelText("Farm area (ha)"), "9");
    expect(screen.queryByRole("heading", { name: "Risk preview" })).toBeNull();
    expect(screen.getByText(/Your plan changed/)).toBeTruthy();
    expect((screen.getByRole("button", { name: "Save plan" }) as HTMLButtonElement).disabled).toBe(true);

    await user.click(screen.getByRole("button", { name: "Check Glut Risk" }));
    await screen.findByRole("heading", { name: "Risk preview" });
    await user.click(screen.getByRole("button", { name: "Save plan" }));
    await waitFor(() => expect(requests.some((item) => item.path === "/plans" && item.method === "POST")).toBe(true));
    const savedPayload = requests.find((item) => item.path === "/plans" && item.method === "POST")?.body as Record<string, unknown>;
    expect(savedPayload.area_ha).toBe(9);
    expect(requests.filter((item) => item.path === "/plans" && item.method === "POST")).toHaveLength(1);

    view.rerender(<PlatformPage path="/plans/new" {...commonProps(farmer, "tl")} />);
    expect(await screen.findByText(/Ang nakaplanong Kamatis/)).toBeTruthy();
  });

  it("requires a fresh risk preview for a changed edit", async () => {
    const requests: Array<{ path: string; method: string }> = [];
    installApi((path, method) => {
      requests.push({ path, method });
      if (path === "/crops") return { items: crops, total: crops.length, categories: ["vegetable"], dataset_version: "demo-2026-09-v4" };
      if (path === "/geographies") return { items: geographies, dataset_version: "demo-2026-09-v4" };
      if (path === "/planning-periods") return [period];
      if (path === "/plans/7") return plan;
      if (path === "/risk/check") return riskResult;
      return plan;
    });
    const user = userEvent.setup();
    render(<PlatformPage path="/plans/7/edit" {...commonProps()} />);

    const area = await screen.findByLabelText("Farm area (ha)");
    await user.clear(area);
    await user.type(area, "10");
    expect((screen.getByRole("button", { name: "Save plan" }) as HTMLButtonElement).disabled).toBe(true);
    await user.click(screen.getByRole("button", { name: "Check Glut Risk" }));
    await screen.findByRole("heading", { name: "Risk preview" });
    await user.click(screen.getByRole("button", { name: "Save plan" }));
    await waitFor(() => expect(requests.some((item) => item.path === "/plans/7" && item.method === "PATCH")).toBe(true));
  });
});

describe("protected platform routing", () => {
  it("keeps the first-time demo required and allows demo replay", () => {
    expect(resolveProtectedRoute("/settings", {
      authenticated: true,
      user: { ...farmer, has_completed_demo: false },
      csrf_token: "token",
    }, false)).toEqual({ kind: "redirect", path: "/demo" });
    expect(resolveProtectedRoute("/demo", { authenticated: true, user: farmer, csrf_token: "token" }, false))
      .toEqual({ kind: "redirect", path: "/dashboard" });
    expect(resolveProtectedRoute("/demo", { authenticated: true, user: farmer, csrf_token: "token" }, true))
      .toEqual({ kind: "render" });
    expect(resolveProtectedRoute("/plans", { authenticated: false, user: null }, false))
      .toEqual({ kind: "auth" });
  });
});
