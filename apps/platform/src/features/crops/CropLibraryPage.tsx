import { useMemo, useState } from "react";
import { phase6Messages } from "@tanim/i18n/phase6";
import type { Language } from "@tanim/types";
import type { CropListResponse } from "@tanim/types/phase6";
import { FeaturePage, localizedCategory, RequestState, useApiData } from "../phase6/shared";
import "../phase6/phase6.css";

export function CropLibraryPage({ language }: { language: Language }) {
  const copy = phase6Messages[language];
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const path = useMemo(() => {
    const params = new URLSearchParams({ limit: "100" });
    if (search.trim()) params.set("q", search.trim());
    if (category) params.set("category", category);
    return `/crops?${params.toString()}`;
  }, [category, search]);
  const { data, loading, error, retry } = useApiData<CropListResponse>(path, language);

  return (
    <FeaturePage title={copy.crops.title} intro={copy.crops.intro}>
      <section className="phase6-filters" aria-label={copy.crops.title}>
        <div className="phase6-control">
          <label htmlFor="crop-search">{copy.crops.searchLabel}</label>
          <input
            id="crop-search"
            type="search"
            placeholder={copy.crops.searchPlaceholder}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
        <div className="phase6-control">
          <label htmlFor="crop-category">{copy.crops.categoryLabel}</label>
          <select
            id="crop-category"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          >
            <option value="">{copy.crops.allCategories}</option>
            {(data?.categories ?? []).map((item) => (
              <option key={item} value={item}>{localizedCategory(item, language)}</option>
            ))}
          </select>
        </div>
      </section>

      <RequestState loading={loading} error={error} onRetry={() => void retry()} language={language} />
      {!loading && !error && data?.items.length === 0 ? (
        <p className="phase6-empty" role="status">{copy.crops.noResults}</p>
      ) : null}
      {!loading && !error && data?.items.length ? (
        <ul className="phase6-crop-grid">
          {data.items.map((crop) => (
            <li className="phase6-crop-card" key={crop.crop_id}>
              <a href={`/crops/${encodeURIComponent(crop.crop_id)}`}>
                <h2>{crop.canonical_name_en}</h2>
                <p className="phase6-local-name">
                  {crop.canonical_name_tl || copy.common.noName}
                </p>
                <p>{localizedCategory(crop.category, language)}</p>
              </a>
            </li>
          ))}
        </ul>
      ) : null}
    </FeaturePage>
  );
}
