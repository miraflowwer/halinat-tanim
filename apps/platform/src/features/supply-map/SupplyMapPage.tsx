import { useEffect, useMemo, useState } from "react";
import type { KeyboardEvent } from "react";
import { phase6Messages } from "@tanim/i18n/phase6";
import type {
  CropListResponse,
  LuzonRegionFeature,
  LuzonRegionGeometry,
  MapPolygonGeometry,
  SupplyMapLevel,
  SupplyMapRecord,
  SupplyMapResponse,
} from "@tanim/types/phase6";
import type { Language } from "@tanim/types";
import { InternalLink } from "../../PlatformShell";
import { FeaturePage, RequestState, useApiData } from "../phase6/shared";
import "../phase6/phase6.css";

const mapWidth = 820;
const mapHeight = 580;
const mapPadding = 16;

function positionsFor(geometry: LuzonRegionFeature["geometry"]): Array<[number, number]> {
  if (geometry.type === "Polygon") return geometry.coordinates.flat();
  return geometry.coordinates.flat(2);
}

function pathFor(geometry: LuzonRegionFeature["geometry"], project: (point: [number, number]) => [number, number]) {
  const polygons: MapPolygonGeometry["coordinates"][] =
    geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates;
  return polygons
    .map((polygon) =>
      polygon
        .map((ring) => {
          const commands = ring.map((position, index) => {
            const [x, y] = project(position);
            return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
          });
          return `${commands.join(" ")} Z`;
        })
        .join(" "),
    )
    .join(" ");
}

function levelLabel(level: SupplyMapLevel, language: Language) {
  const copy = phase6Messages[language].supplyMap;
  switch (level) {
    case "low": return copy.low;
    case "moderate": return copy.moderate;
    case "high": return copy.high;
    case "no_data": return copy.noData;
  }
}

function formatArea(value: number | null, language: Language) {
  return value === null
    ? phase6Messages[language].supplyMap.noAreaData
    : `${value.toLocaleString(language === "tl" ? "fil-PH" : "en-PH", { maximumFractionDigits: 2 })} ha`;
}

function formatPeriod(response: SupplyMapResponse, language: Language) {
  const label = response.period.period_kind === "current_supply"
    ? phase6Messages[language].supplyMap.currentPeriod
    : phase6Messages[language].supplyMap.futurePeriod;
  return `${label}: ${response.period.period_start} to ${response.period.period_end}`;
}

function LuzonMap({
  geometry,
  records,
  selectedId,
  onSelect,
  language,
}: {
  geometry: LuzonRegionGeometry;
  records: SupplyMapRecord[];
  selectedId: string;
  onSelect: (id: string) => void;
  language: Language;
}) {
  const recordById = new Map(records.map((record) => [record.geography_id, record]));
  const allPositions = geometry.features.flatMap((feature) => positionsFor(feature.geometry));
  const longitudeMin = Math.min(...allPositions.map(([longitude]) => longitude));
  const longitudeMax = Math.max(...allPositions.map(([longitude]) => longitude));
  const latitudeMin = Math.min(...allPositions.map(([, latitude]) => latitude));
  const latitudeMax = Math.max(...allPositions.map(([, latitude]) => latitude));
  const longitudeSpan = Math.max(longitudeMax - longitudeMin, 0.001);
  const latitudeSpan = Math.max(latitudeMax - latitudeMin, 0.001);
  const scale = Math.min(
    (mapWidth - mapPadding * 2) / longitudeSpan,
    (mapHeight - mapPadding * 2) / latitudeSpan,
  );
  const drawnWidth = longitudeSpan * scale;
  const drawnHeight = latitudeSpan * scale;
  const offsetX = (mapWidth - drawnWidth) / 2;
  const offsetY = (mapHeight - drawnHeight) / 2;
  const project = (point: [number, number]): [number, number] => [
    offsetX + (point[0] - longitudeMin) * scale,
    offsetY + (latitudeMax - point[1]) * scale,
  ];
  const copy = phase6Messages[language];

  function selectWithKeyboard(event: KeyboardEvent<SVGPathElement>, geographyId: string) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect(geographyId);
    }
  }

  return (
    <svg
      className="phase6-supply-map"
      viewBox={`0 0 ${mapWidth} ${mapHeight}`}
      role="group"
      aria-label={copy.supplyMap.mapLabel}
      aria-describedby="supply-map-regions"
    >
      {geometry.features.map((feature) => {
        const id = feature.properties.geography_id;
        const record = recordById.get(id);
        const level = record?.level ?? "no_data";
        const accessibleLabel = `${feature.properties.name}. ${levelLabel(level, language)}`;
        return (
          <path
            key={id}
            d={pathFor(feature.geometry, project)}
            className={`phase6-region phase6-level-${level}${selectedId === id ? " is-selected" : ""}`}
            role="button"
            tabIndex={0}
            aria-label={accessibleLabel}
            aria-pressed={selectedId === id}
            onClick={() => onSelect(id)}
            onKeyDown={(event) => selectWithKeyboard(event, id)}
          />
        );
      })}
    </svg>
  );
}

export function SupplyMapPage({ language }: { language: Language }) {
  const copy = phase6Messages[language];
  const [cropId, setCropId] = useState(
    () => new URLSearchParams(window.location.search).get("crop_id") ?? "",
  );
  const [period, setPeriod] = useState("current");
  const [levelFilter, setLevelFilter] = useState<SupplyMapLevel | "all">("all");
  const [selectedId, setSelectedId] = useState("");
  const { data: cropData, loading: cropsLoading, error: cropsError, retry: retryCrops } =
    useApiData<CropListResponse>("/crops?limit=100", language);
  useEffect(() => {
    if (!cropId && cropData?.items[0]) setCropId(cropData.items[0].crop_id);
  }, [cropData, cropId]);

  const mapPath = cropId
    ? `/supply-map?crop_id=${encodeURIComponent(cropId)}&period=${encodeURIComponent(period)}`
    : null;
  const geometryPath = "/map-geometry";
  const { data: mapData, loading, error, retry } = useApiData<SupplyMapResponse>(mapPath, language);
  const {
    data: geometry,
    loading: geometryLoading,
    error: geometryError,
    retry: retryGeometry,
  } = useApiData<LuzonRegionGeometry>(geometryPath, language);
  const filteredRecords = useMemo(
    () => (mapData?.items ?? []).filter((item) => levelFilter === "all" || item.level === levelFilter),
    [levelFilter, mapData],
  );
  const selected = filteredRecords.find((item) => item.geography_id === selectedId)
    ?? filteredRecords[0]
    ?? null;

  useEffect(() => {
    if (filteredRecords.length && !filteredRecords.some((item) => item.geography_id === selectedId)) {
      setSelectedId(filteredRecords[0].geography_id);
    }
  }, [filteredRecords, selectedId]);

  const orderedRecords = useMemo(
    () => [...filteredRecords].sort((left, right) => left.name.localeCompare(right.name)),
    [filteredRecords],
  );

  return (
    <FeaturePage title={copy.supplyMap.title} intro={copy.supplyMap.intro}>
      <section className="phase6-filters">
        <div className="phase6-control">
          <label htmlFor="supply-crop">{copy.supplyMap.cropLabel}</label>
          <select id="supply-crop" value={cropId} onChange={(event) => setCropId(event.target.value)}>
            {(cropData?.items ?? []).map((crop) => (
              <option key={crop.crop_id} value={crop.crop_id}>
                {crop.canonical_name_en}{crop.canonical_name_tl ? ` / ${crop.canonical_name_tl}` : ""}
              </option>
            ))}
          </select>
        </div>
        <div className="phase6-control">
          <label htmlFor="supply-level">{copy.supplyMap.levelLabel}</label>
          <select
            id="supply-level"
            value={levelFilter}
            onChange={(event) => setLevelFilter(event.target.value as SupplyMapLevel | "all")}
          >
            <option value="all">{copy.supplyMap.allLevels}</option>
            <option value="low">{copy.supplyMap.low}</option>
            <option value="moderate">{copy.supplyMap.moderate}</option>
            <option value="high">{copy.supplyMap.high}</option>
            <option value="no_data">{copy.supplyMap.noData}</option>
          </select>
        </div>
        <div className="phase6-control">
          <label htmlFor="supply-period">{copy.supplyMap.periodLabel}</label>
          <select id="supply-period" value={period} onChange={(event) => setPeriod(event.target.value)}>
            {(mapData?.available_periods ?? []).map((option) => (
              <option
                key={option.period_start}
                value={option.period_kind === "current_supply" ? "current" : option.period_start}
              >
                {option.period_kind === "current_supply" ? copy.supplyMap.currentPeriod : copy.supplyMap.futurePeriod}
                {` (${option.period_start} – ${option.period_end})`}
              </option>
            ))}
            {!mapData ? <option value="current">{copy.supplyMap.currentPeriod}</option> : null}
          </select>
        </div>
      </section>

      <RequestState loading={cropsLoading || loading} error={cropsError || error} onRetry={() => {
        void (cropsError ? retryCrops() : retry());
      }} language={language} />
      <RequestState loading={geometryLoading} error={geometryError} onRetry={() => void retryGeometry()} language={language} />
      {!loading && !error && mapData ? (
        <>
          <p className="phase6-provenance">{mapData.source_note} <span>{mapData.dataset_version}</span></p>
          <p className="phase6-help">{copy.supplyMap.source}</p>
          <div className="phase6-legend" aria-label={copy.supplyMap.title}>
            {(["low", "moderate", "high", "no_data"] as SupplyMapLevel[]).map((level) => (
              <span key={level} className={`phase6-legend-item phase6-level-${level}`}>
                <span aria-hidden="true" className="phase6-legend-mark" />
                {levelLabel(level, language)}
              </span>
            ))}
          </div>
          {geometry ? (
            <section className="phase6-card stack" aria-label={copy.supplyMap.mapLabel}>
              <LuzonMap
                geometry={geometry}
                records={filteredRecords}
                selectedId={selectedId}
                onSelect={setSelectedId}
                language={language}
              />
            </section>
          ) : null}
          {selected ? (
            <section className="phase6-card stack" aria-labelledby="selected-region-title">
              <h2 id="selected-region-title">{copy.supplyMap.selected}: {selected.name}</h2>
              {selected.data_status === "no_data" ? <p role="status">{copy.supplyMap.noAreaData}</p> : null}
              <dl className="phase6-facts">
                <div><dt>{copy.supplyMap.planned}</dt><dd>{formatArea(selected.planned_context_area_ha, language)}</dd></div>
                <div><dt>{copy.supplyMap.reference}</dt><dd>{formatArea(selected.reference_context_area_ha, language)}</dd></div>
                <div><dt>{copy.supplyMap.ratio}</dt><dd>{selected.ratio === null ? copy.supplyMap.noData : selected.ratio.toFixed(2)}</dd></div>
                <div><dt>{copy.supplyMap.status}</dt><dd>{levelLabel(selected.level, language)}</dd></div>
                <div><dt>{copy.supplyMap.period}</dt><dd>{formatPeriod(mapData, language)}</dd></div>
              </dl>
              <div className="button-row">
                <InternalLink className="phase6-button" href={`/crops/${encodeURIComponent(mapData.crop_id)}`}>
                  {copy.supplyMap.viewCrop}
                </InternalLink>
                <InternalLink className="phase6-button" href={`/prices?crop_id=${encodeURIComponent(mapData.crop_id)}&geography_id=${encodeURIComponent(selected.geography_id)}`}>
                  {copy.supplyMap.viewPrices}
                </InternalLink>
              </div>
            </section>
          ) : null}
          <section id="supply-map-regions" className="phase6-card stack" aria-labelledby="supply-region-list-title">
            <h2 id="supply-region-list-title">{copy.supplyMap.textual}</h2>
            <ul className="phase6-region-list">
              {orderedRecords.map((record) => (
                <li key={record.geography_id}>
                  <button
                    type="button"
                    className={`phase6-region-option phase6-level-${record.level}${selectedId === record.geography_id ? " is-selected" : ""}`}
                    aria-pressed={selectedId === record.geography_id}
                    onClick={() => setSelectedId(record.geography_id)}
                  >
                    <span>{record.name}</span>
                    <span>{levelLabel(record.level, language)}</span>
                    <span>{record.ratio === null ? copy.supplyMap.noData : record.ratio.toFixed(2)}</span>
                  </button>
                </li>
              ))}
            </ul>
            {orderedRecords.length === 0 ? <p role="status">{copy.supplyMap.noData}</p> : null}
          </section>
        </>
      ) : null}
    </FeaturePage>
  );
}
