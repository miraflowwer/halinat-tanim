import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { apiRequest } from "@tanim/api-client";
import { phase6Messages } from "@tanim/i18n/phase6";
import type { Language } from "@tanim/types";

export type FeatureLanguage = Language;

export function useApiData<T>(path: string | null, language: Language) {
  const copy = phase6Messages[language];
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(Boolean(path));
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!path) {
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }
    setLoading(true);
    setData(null);
    setError(null);
    try {
      setData(await apiRequest<T>(path));
    } catch {
      setData(null);
      setError(copy.common.error);
    } finally {
      setLoading(false);
    }
  }, [copy.common.error, path]);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, loading, error, retry: load };
}

export function FeaturePage({
  title,
  intro,
  children,
}: {
  title: string;
  intro?: string;
  children: ReactNode;
}) {
  return (
    <div className="phase6-page stack">
      <header className="phase6-page-heading stack">
        <h1>{title}</h1>
        {intro ? <p>{intro}</p> : null}
      </header>
      {children}
    </div>
  );
}

export function RequestState({
  loading,
  error,
  onRetry,
  language,
}: {
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  language: Language;
}) {
  const copy = phase6Messages[language];
  if (loading) {
    return <p className="phase6-status" aria-live="polite">{copy.common.loading}</p>;
  }
  if (error) {
    return (
      <div className="phase6-error stack" role="alert">
        <p>{error}</p>
        <button type="button" className="phase6-button" onClick={onRetry}>
          {copy.common.retry}
        </button>
      </div>
    );
  }
  return null;
}

export function localizedCategory(category: string, language: Language): string {
  const labels: Record<string, { en: string; tl: string }> = {
    fruit: { en: "Fruit", tl: "Prutas" },
    vegetable: { en: "Vegetable", tl: "Gulay" },
    root_crop: { en: "Root crop", tl: "Ugat na pananim" },
    legume: { en: "Legume", tl: "Legumbre" },
    herb: { en: "Herb", tl: "Damo at halamang-gamot" },
    spice: { en: "Spice", tl: "Pampalasa" },
  };
  return labels[category]?.[language] ?? category.replaceAll("_", " ");
}

export function useGeographySearch({
  level,
  language,
  initialQuery = "",
  limit = 30,
}: {
  level: "region" | "province" | "municipality_city";
  language: Language;
  initialQuery?: string;
  limit?: number;
}) {
  const [query, setQuery] = useState(initialQuery);
  const [items, setItems] = useState<
    Array<{ geography_id: string; name: string; level: string }>
  >([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const copy = phase6Messages[language];

  const search = useCallback(async () => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams({ level, limit: String(limit) });
    if (query.trim()) params.set("q", query.trim());
    try {
      const result = await apiRequest<{
        items: Array<{ geography_id: string; name: string; level: string }>;
      }>(`/geographies?${params.toString()}`);
      setItems(result.items);
    } catch {
      setItems([]);
      setError(copy.common.error);
    } finally {
      setLoading(false);
    }
  }, [copy.common.error, level, limit, query]);

  useEffect(() => {
    if (query.trim().length === 0) void search();
  }, [search, query]);

  return { query, setQuery, items, loading, error, search };
}

export function GeographyPicker({
  level,
  label,
  language,
  selectedId,
  onSelect,
  hint,
}: {
  level: "region" | "province" | "municipality_city";
  label: string;
  language: Language;
  selectedId: string;
  onSelect: (geographyId: string) => void;
  hint?: string;
}) {
  const copy = phase6Messages[language];
  const { query, setQuery, items, loading, error, search } = useGeographySearch({
    level,
    language,
    limit: 30,
  });
  const id = `phase6-location-${level}`;
  const resultsId = `${id}-results`;

  return (
    <div className="phase6-control stack">
      <label htmlFor={id}>{label}</label>
      <div className="phase6-search-row">
        <input
          id={id}
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              void search();
            }
          }}
          aria-describedby={hint ? `${id}-hint` : undefined}
        />
        <button className="phase6-button" type="button" onClick={() => void search()}>
          {copy.common.search}
        </button>
      </div>
      {hint ? <p id={`${id}-hint`} className="phase6-help">{hint}</p> : null}
      {loading ? <p aria-live="polite">{copy.common.loading}</p> : null}
      {error ? <p className="phase6-inline-error" role="alert">{error}</p> : null}
      {!loading && !error && items.length > 0 ? (
        <div className="phase6-control">
          <label htmlFor={resultsId}>{copy.common.choose}</label>
          <select
            id={resultsId}
            value={selectedId}
            onChange={(event) => onSelect(event.target.value)}
          >
            <option value="">{copy.common.choose}</option>
            {items.map((item) => (
              <option key={item.geography_id} value={item.geography_id}>
                {item.name}
              </option>
            ))}
          </select>
        </div>
      ) : null}
      {!loading && !error && query.trim().length >= 2 && items.length === 0 ? (
        <p className="phase6-help">{phase6Messages[language].suitability.noLocations}</p>
      ) : null}
    </div>
  );
}
