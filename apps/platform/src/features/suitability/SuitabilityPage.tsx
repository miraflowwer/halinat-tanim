import { useEffect, useState } from "react";
import { phase6Messages } from "@tanim/i18n/phase6";
import type { Language } from "@tanim/types";
import type { CropListResponse, SuitabilityClass, SuitabilityResponse } from "@tanim/types/phase6";
import {
  FeaturePage,
  GeographyPicker,
  RequestState,
  useApiData,
} from "../phase6/shared";
import "../phase6/phase6.css";

function suitabilityLabel(value: SuitabilityClass, language: Language): string {
  const copy = phase6Messages[language].suitability;
  switch (value) {
    case "suitable": return copy.suitable;
    case "moderately_suitable": return copy.moderate;
    case "low_suitability": return copy.low;
    case "no_data": return copy.noData;
  }
}

export function SuitabilityPage({ language }: { language: Language }) {
  const copy = phase6Messages[language];
  const [cropId, setCropId] = useState(
    () => new URLSearchParams(window.location.search).get("crop_id") ?? "",
  );
  const [geographyId, setGeographyId] = useState("");
  const { data: cropData, loading: cropsLoading, error: cropsError, retry: retryCrops } =
    useApiData<CropListResponse>("/crops?limit=100", language);

  useEffect(() => {
    if (!cropId && cropData?.items[0]) setCropId(cropData.items[0].crop_id);
  }, [cropData, cropId]);

  const resultPath = cropId && geographyId
    ? `/suitability?crop_id=${encodeURIComponent(cropId)}&geography_id=${encodeURIComponent(geographyId)}`
    : null;
  const { data: result, loading, error, retry } = useApiData<SuitabilityResponse>(resultPath, language);

  return (
    <FeaturePage title={copy.suitability.title} intro={copy.suitability.intro}>
      <section className="phase6-filters">
        <div className="phase6-control">
          <label htmlFor="suitability-crop">{copy.suitability.cropLabel}</label>
          <select id="suitability-crop" value={cropId} onChange={(event) => setCropId(event.target.value)}>
            {(cropData?.items ?? []).map((crop) => (
              <option key={crop.crop_id} value={crop.crop_id}>
                {crop.canonical_name_en}{crop.canonical_name_tl ? ` / ${crop.canonical_name_tl}` : ""}
              </option>
            ))}
          </select>
        </div>
        <GeographyPicker
          level="municipality_city"
          label={copy.suitability.locationLabel}
          language={language}
          selectedId={geographyId}
          onSelect={setGeographyId}
          hint={copy.suitability.locationHint}
        />
      </section>

      <RequestState loading={cropsLoading} error={cropsError} onRetry={() => void retryCrops()} language={language} />
      <RequestState loading={loading} error={error} onRetry={() => void retry()} language={language} />
      {!loading && !error && result ? (
        <section className="phase6-card stack" aria-labelledby="suitability-result-title">
          <h2 id="suitability-result-title">{copy.suitability.result}</h2>
          <p className={`phase6-suitability phase6-level-${result.suitability_class}`}>
            {suitabilityLabel(result.suitability_class, language)}
          </p>
          <dl className="phase6-facts">
            <div><dt>{copy.suitability.locationLabel}</dt><dd>{result.geography_name}</dd></div>
            <div><dt>{copy.common.dataVersion}</dt><dd>{result.dataset_version}</dd></div>
            {result.method_note ? <div><dt>{copy.common.sources}</dt><dd>{result.method_note}</dd></div> : null}
          </dl>
          <p className="phase6-provenance">{copy.suitability.synthetic}</p>
          <p>{copy.suitability.separate}</p>
        </section>
      ) : null}
    </FeaturePage>
  );
}
