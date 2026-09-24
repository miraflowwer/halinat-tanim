import { phase6Messages } from "@tanim/i18n/phase6";
import type { Language } from "@tanim/types";
import type { CropDetail } from "@tanim/types/phase6";
import { FeaturePage, localizedCategory, RequestState, useApiData } from "../phase6/shared";
import "../phase6/phase6.css";

export function CropDetailPage({
  cropId,
  language,
}: {
  cropId: string;
  language: Language;
}) {
  const copy = phase6Messages[language];
  const { data, loading, error, retry } = useApiData<CropDetail>(
    `/crops/${encodeURIComponent(cropId)}`,
    language,
  );
  const english = language === "en";

  return (
    <FeaturePage title={data?.canonical_name_en ?? copy.crops.title}>
      <p className="phase6-local-name">
        {data?.canonical_name_tl || copy.common.noName}
      </p>
      <RequestState loading={loading} error={error} onRetry={() => void retry()} language={language} />
      {!loading && !error && data ? (
        <div className="phase6-sections">
          <section className="phase6-card stack" aria-labelledby="crop-overview">
            <h2 id="crop-overview">{copy.crops.overview}</h2>
            <p>{english ? data.summary_en : data.summary_tl}</p>
            <dl className="phase6-facts">
              <div><dt>{copy.crops.scientificName}</dt><dd>{data.scientific_name || "—"}</dd></div>
              <div><dt>{copy.crops.categoryLabel}</dt><dd>{localizedCategory(data.category, language)}</dd></div>
            </dl>
            <p className="phase6-help">{copy.crops.notAdvice}</p>
          </section>

          <section className="phase6-card stack" aria-labelledby="crop-supply">
            <h2 id="crop-supply">{copy.crops.supply}</h2>
            <p>{copy.supplyMap.source}</p>
            <a href={`/map?crop_id=${encodeURIComponent(data.crop_id)}`}>{copy.crops.supplyLink}</a>
          </section>

          <section className="phase6-card stack" aria-labelledby="crop-prices">
            <h2 id="crop-prices">{copy.crops.prices}</h2>
            <p>{copy.prices.synthetic}</p>
            <a href={`/prices?crop_id=${encodeURIComponent(data.crop_id)}`}>{copy.crops.priceLink}</a>
          </section>

          <section className="phase6-card stack" aria-labelledby="crop-suitability">
            <h2 id="crop-suitability">{copy.crops.suitability}</h2>
            <p>{copy.suitability.separate}</p>
            <a href={`/suitability?crop_id=${encodeURIComponent(data.crop_id)}`}>{copy.crops.suitabilityLink}</a>
          </section>

          <section className="phase6-card stack" aria-labelledby="crop-growing">
            <h2 id="crop-growing">{copy.crops.growing}</h2>
            <p>{english ? data.growing_conditions_en : data.growing_conditions_tl}</p>
            <p>{english ? data.soil_notes_en : data.soil_notes_tl}</p>
          </section>

          <section className="phase6-card stack" aria-labelledby="crop-weather">
            <h2 id="crop-weather">{copy.crops.weather}</h2>
            <p>{copy.weather.contextOnly}</p>
            <a href="/weather">{copy.crops.weatherLink}</a>
          </section>

          <section className="phase6-card stack" aria-labelledby="crop-sources">
            <h2 id="crop-sources">{copy.common.sources}</h2>
            <p>{copy.crops.sourceNote}</p>
            <dl className="phase6-facts">
              <div><dt>{copy.common.dataVersion}</dt><dd>{data.dataset_version}</dd></div>
              <div><dt>{copy.common.sources}</dt><dd>{data.source_ids.join(", ") || "—"}</dd></div>
            </dl>
            {data.method_note ? <p>{data.method_note}</p> : null}
          </section>
        </div>
      ) : null}
    </FeaturePage>
  );
}
