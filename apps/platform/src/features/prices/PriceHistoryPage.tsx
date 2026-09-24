import { useEffect, useMemo, useState } from "react";
import { phase6Messages } from "@tanim/i18n/phase6";
import type { Language } from "@tanim/types";
import type {
  CropListResponse,
  GeographyListResponse,
  PriceHistoryResponse,
  PriceRecord,
} from "@tanim/types/phase6";
import { FeaturePage, RequestState, useApiData } from "../phase6/shared";
import "../phase6/phase6.css";

const chartWidth = 760;
const chartHeight = 270;
const chartPadding = 38;

function PriceChart({
  records,
  language,
}: {
  records: PriceRecord[];
  language: Language;
}) {
  const copy = phase6Messages[language];
  const [selectedIndex, setSelectedIndex] = useState(Math.max(0, records.length - 1));
  const values = records.map((record) => record.price_php_per_kg);
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const valueRange = maximum - minimum || Math.max(maximum * 0.1, 1);
  const innerWidth = chartWidth - chartPadding * 2;
  const innerHeight = chartHeight - chartPadding * 2;
  const points = records.map((record, index) => ({
    record,
    x: chartPadding + (records.length < 2 ? innerWidth / 2 : (index / (records.length - 1)) * innerWidth),
    y: chartPadding + innerHeight - ((record.price_php_per_kg - minimum) / valueRange) * innerHeight,
  }));
  const line = points.map((point) => `${point.x},${point.y}`).join(" ");
  const selected = records[Math.min(selectedIndex, records.length - 1)];
  const formatPrice = (value: number) => `₱${value.toFixed(2)} ${copy.prices.unit}`;

  return (
    <section className="phase6-card stack" aria-labelledby="price-chart-title">
      <h2 id="price-chart-title">{copy.prices.chartLabel}</h2>
      <p className="phase6-unit">{copy.prices.unit}</p>
      <div className="phase6-chart-wrap">
        <svg
          className="phase6-price-chart"
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          role="group"
          aria-label={copy.prices.chartLabel}
        >
          <line
            x1={chartPadding}
            y1={chartPadding + innerHeight}
            x2={chartWidth - chartPadding}
            y2={chartPadding + innerHeight}
            className="phase6-chart-axis"
          />
          <line
            x1={chartPadding}
            y1={chartPadding}
            x2={chartPadding}
            y2={chartPadding + innerHeight}
            className="phase6-chart-axis"
          />
          {points.length > 1 ? <polyline points={line} className="phase6-chart-line" /> : null}
          {points.map((point, index) => (
            <circle
              key={`${point.record.date}-${point.record.geography_id}`}
              cx={point.x}
              cy={point.y}
              r={index === selectedIndex ? 7 : 5}
              className="phase6-chart-point"
              role="img"
              tabIndex={0}
              aria-label={`${point.record.date}: ${formatPrice(point.record.price_php_per_kg)}; ${point.record.geography_name}`}
              onFocus={() => setSelectedIndex(index)}
              onMouseEnter={() => setSelectedIndex(index)}
            />
          ))}
        </svg>
      </div>
      {selected ? (
        <p className="phase6-selected-value" aria-live="polite">
          {copy.prices.selectedPoint}: {selected.date}, {formatPrice(selected.price_php_per_kg)}
        </p>
      ) : null}
      <details className="phase6-table-fallback">
        <summary>{copy.prices.table}</summary>
        <div className="phase6-table-scroll">
          <table>
            <thead>
              <tr><th scope="col">{copy.prices.date}</th><th scope="col">{copy.prices.locationLabel}</th><th scope="col">{copy.prices.value} ({copy.prices.unit})</th></tr>
            </thead>
            <tbody>
              {records.map((record) => (
                <tr key={`${record.date}-${record.geography_id}`}>
                  <td>{record.date}</td>
                  <td>{record.geography_name}</td>
                  <td>₱{record.price_php_per_kg.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  );
}

export function PriceHistoryPage({ language }: { language: Language }) {
  const copy = phase6Messages[language];
  const [cropId, setCropId] = useState(
    () => new URLSearchParams(window.location.search).get("crop_id") ?? "",
  );
  const [geographyId, setGeographyId] = useState("");
  const [timeRange, setTimeRange] = useState<"1m" | "3m" | "1y" | "all">("1y");
  const { data: cropData, loading: cropsLoading, error: cropsError, retry: retryCrops } =
    useApiData<CropListResponse>("/crops?limit=100", language);
  const geographyPath = cropId
    ? `/geographies?for_prices=true&crop_id=${encodeURIComponent(cropId)}&limit=1000`
    : null;
  const {
    data: geographyData,
    loading: geographiesLoading,
    error: geographiesError,
    retry: retryGeographies,
  } = useApiData<GeographyListResponse>(geographyPath, language);

  useEffect(() => {
    if (!cropId && cropData?.items[0]) setCropId(cropData.items[0].crop_id);
  }, [cropData, cropId]);
  useEffect(() => {
    if (geographyData?.items.length && !geographyData.items.some((item) => item.geography_id === geographyId)) {
      setGeographyId(geographyData.items[0].geography_id);
    }
  }, [geographyData, geographyId]);

  const pricePath = useMemo(() => {
    if (!cropId || !geographyId) return null;
    const params = new URLSearchParams({
      crop_id: cropId,
      geography_id: geographyId,
      range: timeRange,
    });
    return `/prices?${params.toString()}`;
  }, [cropId, geographyId, timeRange]);
  const { data: prices, loading, error, retry } = useApiData<PriceHistoryResponse>(pricePath, language);

  return (
    <FeaturePage title={copy.prices.title} intro={copy.prices.intro}>
      <section className="phase6-filters">
        <div className="phase6-control">
          <label htmlFor="price-crop">{copy.prices.cropLabel}</label>
          <select id="price-crop" value={cropId} onChange={(event) => setCropId(event.target.value)}>
            {(cropData?.items ?? []).map((crop) => (
              <option key={crop.crop_id} value={crop.crop_id}>
                {crop.canonical_name_en}{crop.canonical_name_tl ? ` / ${crop.canonical_name_tl}` : ""}
              </option>
            ))}
          </select>
        </div>
        <div className="phase6-control">
          <label htmlFor="price-location">{copy.prices.locationLabel}</label>
          <select
            id="price-location"
            value={geographyId}
            onChange={(event) => setGeographyId(event.target.value)}
          >
            {(geographyData?.items ?? []).map((place) => (
              <option key={place.geography_id} value={place.geography_id}>{place.name}</option>
            ))}
          </select>
        </div>
        <div className="phase6-control">
          <label htmlFor="price-range">{copy.prices.rangeLabel}</label>
          <select
            id="price-range"
            value={timeRange}
            onChange={(event) => setTimeRange(event.target.value as typeof timeRange)}
          >
            <option value="1m">{copy.prices.oneMonth}</option>
            <option value="3m">{copy.prices.threeMonths}</option>
            <option value="1y">{copy.prices.oneYear}</option>
            <option value="all">{copy.prices.allTime}</option>
          </select>
        </div>
      </section>

      <RequestState loading={cropsLoading || geographiesLoading} error={cropsError || geographiesError} onRetry={() => {
        void (cropsError ? retryCrops() : retryGeographies());
      }} language={language} />
      <RequestState loading={loading} error={error} onRetry={() => void retry()} language={language} />
      {!cropsLoading && !geographiesLoading && !cropsError && !geographiesError && !geographyData?.items.length ? (
        <p className="phase6-empty" role="status">{copy.prices.empty}</p>
      ) : null}
      {!loading && !error && prices && prices.records.length === 0 ? (
        <p className="phase6-empty" role="status">{copy.prices.empty}</p>
      ) : null}
      {!loading && !error && prices?.records.length ? (
        <>
          <PriceChart records={prices.records} language={language} />
          <p className="phase6-provenance">{copy.prices.synthetic} <span>{prices.dataset_version}</span></p>
        </>
      ) : null}
    </FeaturePage>
  );
}
