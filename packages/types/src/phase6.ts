export type CropListItem = {
  crop_id: string;
  canonical_name_en: string;
  canonical_name_tl: string | null;
  scientific_name: string | null;
  category: string;
  aliases_en: string[];
  aliases_tl: string[];
  data_kind: string;
  dataset_version: string;
};

export type CropListResponse = {
  items: CropListItem[];
  total: number;
  categories: string[];
  dataset_version: string;
};

export type CropDetail = CropListItem & {
  summary_en: string;
  summary_tl: string;
  growing_conditions_en: string;
  growing_conditions_tl: string;
  soil_notes_en: string;
  soil_notes_tl: string;
  reference_sources: string | null;
  source_ids: string[];
  method_note: string | null;
  dataset_provenance: Record<string, unknown>;
  links: {
    prices: string;
    supply: string;
    suitability: string;
  };
};

export type Geography = {
  geography_id: string;
  name: string;
  level: "region" | "province" | "municipality_city";
  code: string | null;
  parent_geography_id: string | null;
  parent_name: string | null;
};

export type GeographyListResponse = {
  items: Geography[];
  dataset_version: string;
};

export type PriceRecord = {
  date: string;
  price_php_per_kg: number;
  currency: "PHP";
  price_unit: "PHP/kg";
  data_kind: string;
  dataset_version: string;
  reference_sources: string | null;
  geography_id: string;
  geography_name: string;
};

export type PriceHistoryResponse = {
  crop_id: string;
  geography_id: string | null;
  range: "1m" | "3m" | "1y" | "all";
  start_date: string | null;
  end_date: string | null;
  currency: "PHP";
  unit: "PHP/kg";
  dataset_version: string;
  data_kind: string;
  provenance: Record<string, unknown>;
  records: PriceRecord[];
};

export type SuitabilityClass =
  | "suitable"
  | "moderately_suitable"
  | "low_suitability"
  | "no_data";

export type SuitabilityResponse = {
  crop_id: string;
  geography_id: string;
  geography_name: string;
  suitability_class: SuitabilityClass;
  dataset_version: string;
  data_kind: string | null;
  source_ids: string[];
  reference_sources?: string | null;
  method_note: string | null;
};

export type MapPeriod = {
  period_start: string;
  period_end: string;
  period_kind: "current_supply" | "future_planning";
};

export type SupplyMapLevel = "low" | "moderate" | "high" | "no_data";

export type SupplyMapRecord = {
  geography_id: string;
  name: string;
  geography_level: "region";
  period_start: string;
  period_end: string;
  period_kind: MapPeriod["period_kind"];
  planned_context_area_ha: number | null;
  reference_context_area_ha: number | null;
  ratio: number | null;
  level: SupplyMapLevel;
  data_status: "available" | "no_data";
  data_kind: "derived" | null;
  source_data_kind: "synthetic_demo" | null;
  dataset_version: string;
  source_note: string;
};

export type SupplyMapResponse = {
  crop_id: string;
  period: MapPeriod;
  available_periods: MapPeriod[];
  geography_level: "region";
  data_kind: "derived";
  source_data_kind: "synthetic_demo";
  dataset_version: string;
  source_note: string;
  items: SupplyMapRecord[];
};

export type MapPosition = [number, number];

export type MapPolygonGeometry = {
  type: "Polygon";
  coordinates: MapPosition[][];
};

export type MapMultiPolygonGeometry = {
  type: "MultiPolygon";
  coordinates: MapPosition[][][];
};

export type LuzonRegionFeature = {
  type: "Feature";
  properties: {
    geography_id: string;
    name: string;
    shapeName: string;
    shapeISO: string;
  };
  geometry: MapPolygonGeometry | MapMultiPolygonGeometry;
};

export type LuzonRegionGeometry = {
  type: "FeatureCollection";
  name: string;
  metadata: Record<string, string>;
  features: LuzonRegionFeature[];
};

export type WeatherForecastDay = {
  date: string;
  weather_code: number;
  condition: string;
  temperature_min_c: number;
  temperature_max_c: number;
  rain_mm: number;
};

export type WeatherResponse = {
  status: "available";
  provider: string;
  data_kind: "live_external";
  geography_id: string;
  location: string;
  latitude: number;
  longitude: number;
  observed_at: string;
  retrieved_at: string;
  current: {
    temperature_c: number;
    precipitation_mm: number;
    rain_mm: number;
    weather_code: number;
    condition: string;
  };
  forecast: WeatherForecastDay[];
  attribution: string;
};

export type WeatherStatusResponse = {
  status: "available";
  provider: string;
};
