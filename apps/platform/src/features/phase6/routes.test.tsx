import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CropDetailPage } from "../crops/CropDetailPage";
import { CropLibraryPage } from "../crops/CropLibraryPage";
import { PriceHistoryPage } from "../prices/PriceHistoryPage";
import { Phase6UtilityRoutes } from "./routes";
import { SuitabilityPage } from "../suitability/SuitabilityPage";
import { SupplyMapPage } from "../supply-map/SupplyMapPage";
import { WeatherPage } from "../weather/WeatherPage";

const { apiRequestMock } = vi.hoisted(() => ({ apiRequestMock: vi.fn() }));
vi.mock("@tanim/api-client", () => ({ apiRequest: apiRequestMock }));

const datasetVersion = "demo-2026-09-v4";
const cropList = {
  items: [{
    crop_id: "rice",
    canonical_name_en: "Rice",
    canonical_name_tl: "Palay",
    scientific_name: "Oryza sativa",
    category: "grain",
    aliases_en: ["paddy"],
    aliases_tl: ["palay"],
    data_kind: "synthetic_demo",
    dataset_version: datasetVersion,
  }],
  total: 1,
  categories: ["grain"],
  dataset_version: datasetVersion,
};
const cropDetail = {
  ...cropList.items[0],
  summary_en: "Rice is a staple crop.",
  summary_tl: "Pangunahing pagkain ang palay.",
  growing_conditions_en: "Warm conditions.",
  growing_conditions_tl: "Mainit na panahon.",
  soil_notes_en: "Moist soil.",
  soil_notes_tl: "Mamasa-masang lupa.",
  reference_sources: "PSA crop list structure",
  source_ids: ["SRC-1"],
  method_note: null,
  dataset_provenance: { data_kind: "synthetic_demo" },
  links: { prices: "/prices", supply: "/map", suitability: "/suitability" },
};
const geographyList = {
  items: [{
    geography_id: "PH-040000000",
    name: "CALABARZON",
    level: "region",
    code: "04",
    parent_geography_id: null,
    parent_name: null,
  }, {
    geography_id: "PH-050000000",
    name: "Bicol Region",
    level: "region",
    code: "05",
    parent_geography_id: null,
    parent_name: null,
  }],
  dataset_version: datasetVersion,
};
const municipalityList = {
  items: [{
    geography_id: "PH-040210000",
    name: "Lipa City",
    level: "municipality_city",
    code: "042106000",
    parent_geography_id: "PH-040000000",
    parent_name: "CALABARZON",
  }],
  dataset_version: datasetVersion,
};
const priceHistory = {
  crop_id: "rice",
  geography_id: "PH-040000000",
  range: "1y",
  start_date: "2026-01-01",
  end_date: "2026-09-01",
  currency: "PHP",
  unit: "PHP/kg",
  dataset_version: datasetVersion,
  data_kind: "synthetic_demo",
  provenance: { data_kind: "synthetic_demo" },
  records: [
    {
      date: "2026-08-01",
      price_php_per_kg: 42.5,
      currency: "PHP",
      price_unit: "PHP/kg",
      data_kind: "synthetic_demo",
      dataset_version: datasetVersion,
      reference_sources: "PSA series shape only",
      geography_id: "PH-040000000",
      geography_name: "CALABARZON",
    },
    {
      date: "2026-09-01",
      price_php_per_kg: 44,
      currency: "PHP",
      price_unit: "PHP/kg",
      data_kind: "synthetic_demo",
      dataset_version: datasetVersion,
      reference_sources: "PSA series shape only",
      geography_id: "PH-040000000",
      geography_name: "CALABARZON",
    },
  ],
};
const suitability = {
  crop_id: "rice",
  geography_id: "PH-040210000",
  geography_name: "Lipa City",
  suitability_class: "no_data",
  dataset_version: datasetVersion,
  data_kind: null,
  source_ids: [],
  method_note: null,
};
const mapGeometry = {
  type: "FeatureCollection",
  name: "TANIM Luzon regions",
  metadata: { source: "geoBoundaries" },
  features: [
    {
      type: "Feature",
      properties: { geography_id: "PH-040000000", name: "CALABARZON", shapeName: "CALABARZON", shapeISO: "PH-04" },
      geometry: { type: "Polygon", coordinates: [[[120.5, 13.8], [122, 13.8], [122, 14.8], [120.5, 14.8], [120.5, 13.8]]] },
    },
    {
      type: "Feature",
      properties: { geography_id: "PH-050000000", name: "Bicol Region", shapeName: "Bicol Region", shapeISO: "PH-05" },
      geometry: { type: "Polygon", coordinates: [[[122, 12.7], [124, 12.7], [124, 14], [122, 14], [122, 12.7]]] },
    },
  ],
};
const supplyMap = {
  crop_id: "rice",
  period: { period_start: "2026-09-01", period_end: "2026-09-30", period_kind: "current_supply" },
  available_periods: [{ period_start: "2026-09-01", period_end: "2026-09-30", period_kind: "current_supply" }],
  geography_level: "region",
  data_kind: "derived",
  source_data_kind: "synthetic_demo",
  dataset_version: datasetVersion,
  source_note: "Snapshot context only.",
  items: [
    {
      geography_id: "PH-040000000",
      name: "CALABARZON",
      geography_level: "region",
      period_start: "2026-09-01",
      period_end: "2026-09-30",
      period_kind: "current_supply",
      planned_context_area_ha: 120,
      reference_context_area_ha: 100,
      ratio: 1.2,
      level: "high",
      data_status: "available",
      data_kind: "derived",
      source_data_kind: "synthetic_demo",
      dataset_version: datasetVersion,
      source_note: "Snapshot context only.",
    },
    {
      geography_id: "PH-050000000",
      name: "Bicol Region",
      geography_level: "region",
      period_start: "2026-09-01",
      period_end: "2026-09-30",
      period_kind: "current_supply",
      planned_context_area_ha: null,
      reference_context_area_ha: null,
      ratio: null,
      level: "no_data",
      data_status: "no_data",
      data_kind: null,
      source_data_kind: null,
      dataset_version: datasetVersion,
      source_note: "Snapshot context only.",
    },
  ],
};
const weatherResponse = {
  status: "available",
  provider: "Open-Meteo",
  data_kind: "live_external",
  geography_id: "PH-040000000",
  location: "CALABARZON",
  latitude: 14.1,
  longitude: 121.3,
  observed_at: "2026-09-24T08:00",
  retrieved_at: "2026-09-24T08:01:00Z",
  current: { temperature_c: 30, precipitation_mm: 0, rain_mm: 0, weather_code: 1, condition: "Mainly clear" },
  forecast: [{ date: "2026-09-25", weather_code: 3, condition: "Overcast", temperature_min_c: 24, temperature_max_c: 31, rain_mm: 1 }],
  attribution: "Open-Meteo",
};

function defaultResponse(path: string) {
  if (path.startsWith("/crops?")) return cropList;
  if (path === "/crops/rice") return cropDetail;
  if (path.startsWith("/geographies?for_prices=true")) return geographyList;
  if (path.startsWith("/geographies?level=municipality_city")) return municipalityList;
  if (path.startsWith("/geographies?level=region")) return geographyList;
  if (path.startsWith("/prices?")) return priceHistory;
  if (path.startsWith("/suitability?")) return suitability;
  if (path.startsWith("/supply-map?")) return supplyMap;
  if (path === "/map-geometry") return mapGeometry;
  if (path === "/weather/status?consent=true") return { status: "available", provider: "Open-Meteo" };
  if (path.startsWith("/weather?")) return weatherResponse;
  throw new Error(`Unexpected API request: ${path}`);
}

function requestPaths() {
  return apiRequestMock.mock.calls.map((call: unknown[]) => String(call[0]));
}

function setPageUrl(url: string) {
  window.history.replaceState({}, "", url);
}

beforeEach(() => {
  setPageUrl("/");
  apiRequestMock.mockImplementation((path: string) => Promise.resolve(defaultResponse(path)));
});

afterEach(() => {
  cleanup();
  apiRequestMock.mockReset();
});

describe("Phase 6 crop and context pages", () => {
  it("searches the crop library and shows a clear empty result", async () => {
    const user = userEvent.setup();
    apiRequestMock.mockImplementation((path: string) => {
      if (path.includes("q=Missing")) return Promise.resolve({ ...cropList, items: [], total: 0 });
      return Promise.resolve(defaultResponse(path));
    });
    render(<CropLibraryPage language="en" />);

    expect(await screen.findByRole("link", { name: /Rice/ })).toBeTruthy();
    await user.clear(screen.getByRole("searchbox", { name: "Search crops" }));
    await user.type(screen.getByRole("searchbox", { name: "Search crops" }), "Missing");

    expect((await screen.findByRole("status")).textContent).toContain("No crops match this search.");
    expect(requestPaths().some((path) => path.includes("q=Missing"))).toBe(true);
  });

  it("lets a user retry a failed crop list request", async () => {
    const user = userEvent.setup();
    let failed = false;
    apiRequestMock.mockImplementation((path: string) => {
      if (path.startsWith("/crops?") && !failed) {
        failed = true;
        return Promise.reject(new Error("local API unavailable"));
      }
      return Promise.resolve(defaultResponse(path));
    });
    render(<CropLibraryPage language="tl" />);

    expect(await screen.findByRole("alert")).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Subukan muli" }));
    expect(await screen.findByRole("link", { name: /Rice/ })).toBeTruthy();
  });

  it("shows bilingual crop detail and links to related context", async () => {
    render(<CropDetailPage cropId="rice" language="tl" />);

    expect(await screen.findByText("Pangunahing pagkain ang palay.")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Tingnan ang mapa ng supply" }).getAttribute("href")).toBe("/map?crop_id=rice");
    expect(screen.getByRole("link", { name: "Tingnan ang presyo" }).getAttribute("href")).toBe("/prices?crop_id=rice");
    expect(screen.getByRole("link", { name: "Suriin ang angkop na lupa" }).getAttribute("href")).toBe("/suitability?crop_id=rice");
    expect(screen.getByText("Palay")).toBeTruthy();
  });

  it("filters prices and provides a keyboard-friendly table alternative", async () => {
    const user = userEvent.setup();
    setPageUrl("/prices?crop_id=rice");
    render(<PriceHistoryPage language="en" />);

    expect(await screen.findByRole("group", { name: "Price history chart" })).toBeTruthy();
    expect(screen.getByText(/Selected price: 2026-09-01, ₱44.00/)).toBeTruthy();
    await user.click(screen.getByText("View values in a table"));
    expect(screen.getByRole("table")).toBeTruthy();
    expect(within(screen.getByRole("table")).getAllByText("CALABARZON")).toHaveLength(2);

    await user.selectOptions(screen.getByLabelText("Time range"), "3m");
    await waitFor(() => expect(requestPaths().some((path) => path.includes("range=3m"))).toBe(true));
  });

  it("shows missing soil context without treating it as supply risk", async () => {
    const user = userEvent.setup();
    setPageUrl("/suitability?crop_id=rice");
    render(<SuitabilityPage language="tl" />);

    await user.selectOptions(await screen.findByLabelText("Pumili"), "PH-040210000");
    expect(await screen.findByText("Walang Datos")).toBeTruthy();
    expect(screen.getByText(/Iba ang angkop na lupa sa pressure ng supply/)).toBeTruthy();
  });

  it("keeps the map's region list usable as a text alternative", async () => {
    const user = userEvent.setup();
    setPageUrl("/map?crop_id=rice");
    render(<SupplyMapPage language="en" />);

    const map = await screen.findByRole("group", { name: /Luzon supply context map/ });
    expect(within(map).getAllByRole("button")).toHaveLength(2);
    expect(screen.getByRole("heading", { name: "Region list" })).toBeTruthy();
    const regionList = screen.getByRole("region", { name: "Region list" });
    await user.click(within(regionList).getByRole("button", { name: /Bicol Region/ }));
    expect(await screen.findByRole("heading", { name: "Selected region: Bicol Region" })).toBeTruthy();
    expect(screen.getByRole("status").textContent).toContain("No supply data is available for this region and period.");
    expect(screen.getByText(/does not show registered farmer planting plans/)).toBeTruthy();
  });

  it("asks before using live weather and checks service reachability before loading it", async () => {
    const user = userEvent.setup();
    render(<WeatherPage language="en" />);

    expect(await screen.findByRole("button", { name: "Continue" })).toBeTruthy();
    expect(requestPaths().some((path) => path.startsWith("/weather"))).toBe(false);

    await user.click(screen.getByRole("button", { name: "Continue" }));
    expect(await screen.findByText("Current weather: CALABARZON")).toBeTruthy();
    expect(requestPaths().filter((path) => path.startsWith("/weather"))).toEqual([
      "/weather/status?consent=true",
      "/weather?geography_id=PH-040000000&consent=true",
    ]);
    expect(screen.getByText(/Weather is context only/)).toBeTruthy();
  });

  it("clears weather and asks again when the selected region changes", async () => {
    const user = userEvent.setup();
    render(<WeatherPage language="en" />);
    await user.click(await screen.findByRole("button", { name: "Continue" }));
    expect(await screen.findByText("Current weather: CALABARZON")).toBeTruthy();

    await user.selectOptions(screen.getByLabelText("Region"), "PH-050000000");
    expect(screen.queryByText("Current weather: CALABARZON")).toBeNull();
    expect(await screen.findByRole("button", { name: "Continue" })).toBeTruthy();
    expect(requestPaths().filter((path) => path.startsWith("/weather"))).toEqual([
      "/weather/status?consent=true",
      "/weather?geography_id=PH-040000000&consent=true",
    ]);
  });

  it("explains weather failure and retries reachability before requesting data", async () => {
    const user = userEvent.setup();
    let statusChecks = 0;
    apiRequestMock.mockImplementation((path: string) => {
      if (path === "/weather/status?consent=true" && statusChecks++ === 0) {
        return Promise.reject(new Error("service unavailable"));
      }
      return Promise.resolve(defaultResponse(path));
    });
    render(<WeatherPage language="tl" />);

    await user.click(await screen.findByRole("button", { name: "Magpatuloy" }));
    expect(await screen.findByText(/Hindi makakonekta ang TANIM sa weather service/)).toBeTruthy();
    expect(requestPaths().filter((path) => path.startsWith("/weather"))).toEqual([
      "/weather/status?consent=true",
    ]);
    await user.click(screen.getByRole("button", { name: "Subukan muli" }));
    expect(await screen.findByText(/Kasalukuyang panahon: CALABARZON/)).toBeTruthy();
    expect(requestPaths().filter((path) => path.startsWith("/weather"))).toEqual([
      "/weather/status?consent=true",
      "/weather/status?consent=true",
      "/weather?geography_id=PH-040000000&consent=true",
    ]);
  });

  it("routes Phase 6 paths without changing the Phase 4 shell", async () => {
    render(<Phase6UtilityRoutes path="/crops/rice" language="en" />);
    expect(await screen.findByText("Rice is a staple crop.")).toBeTruthy();
    expect(Phase6UtilityRoutes({ path: "/home", language: "en" })).toBeNull();
  });
});
