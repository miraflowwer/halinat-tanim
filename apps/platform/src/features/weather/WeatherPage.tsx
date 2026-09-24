import { useEffect, useState } from "react";
import { apiRequest } from "@tanim/api-client";
import { phase6Messages } from "@tanim/i18n/phase6";
import type { Language } from "@tanim/types";
import type {
  GeographyListResponse,
  WeatherResponse,
  WeatherStatusResponse,
} from "@tanim/types/phase6";
import { FeaturePage, useApiData } from "../phase6/shared";
import "../phase6/phase6.css";

type WeatherStep = "consent" | "checking" | "loading" | "ready" | "error";

function conditionLabel(code: number, language: Language) {
  const conditions = phase6Messages[language].weather.conditions;
  return conditions[code] ?? (language === "tl" ? "Hindi alam ang kalagayan" : "Condition not available");
}

export function WeatherPage({ language }: { language: Language }) {
  const copy = phase6Messages[language];
  const [geographyId, setGeographyId] = useState("");
  const [hasConsent, setHasConsent] = useState(false);
  const [step, setStep] = useState<WeatherStep>("consent");
  const [weather, setWeather] = useState<WeatherResponse | null>(null);
  const [provider, setProvider] = useState("Open-Meteo");
  const {
    data: geographyData,
    loading: locationsLoading,
    error: locationsError,
    retry: retryLocations,
  } = useApiData<GeographyListResponse>("/geographies?level=region&limit=20", language);

  useEffect(() => {
    if (!geographyId && geographyData?.items[0]) {
      setGeographyId(geographyData.items[0].geography_id);
    }
  }, [geographyData, geographyId]);

  async function loadWeather() {
    if (!geographyId) return;
    setHasConsent(true);
    setWeather(null);
    try {
      setStep("checking");
      const status = await apiRequest<WeatherStatusResponse>("/weather/status?consent=true");
      setProvider(status.provider);
      setStep("loading");
      const result = await apiRequest<WeatherResponse>(
        `/weather?geography_id=${encodeURIComponent(geographyId)}&consent=true`,
      );
      setWeather(result);
      setProvider(result.provider);
      setStep("ready");
    } catch {
      setStep("error");
    }
  }

  const liveStatus = step === "checking" || step === "loading";
  const message = step === "checking"
    ? copy.weather.checking
    : step === "loading"
      ? copy.weather.loading
      : copy.weather.unavailable;

  return (
    <FeaturePage title={copy.weather.title} intro={copy.weather.intro}>
      <section className="phase6-card stack">
        <div className="phase6-control">
          <label htmlFor="weather-region">{copy.weather.locationLabel}</label>
          <select
            id="weather-region"
            value={geographyId}
            onChange={(event) => {
              setGeographyId(event.target.value);
              setHasConsent(false);
              setWeather(null);
              setStep("consent");
            }}
            disabled={locationsLoading || !geographyData?.items.length}
          >
            <option value="">{copy.common.choose}</option>
            {(geographyData?.items ?? []).map((place) => (
              <option key={place.geography_id} value={place.geography_id}>{place.name}</option>
            ))}
          </select>
          {geographyData?.items.length === 0 ? <p className="phase6-help">{copy.weather.locationHint}</p> : null}
        </div>
        {locationsLoading ? <p aria-live="polite">{copy.common.loading}</p> : null}
        {locationsError ? (
          <div className="phase6-error stack" role="alert">
            <p>{locationsError}</p>
            <button type="button" className="phase6-button" onClick={() => void retryLocations()}>
              {copy.common.retry}
            </button>
          </div>
        ) : null}

        {!hasConsent ? (
          <div className="phase6-weather-consent stack">
            <p>{copy.weather.connectionNotice}</p>
            <button
              type="button"
              className="phase6-button phase6-button-primary"
              disabled={!geographyId || locationsLoading}
              onClick={() => void loadWeather()}
            >
              {copy.weather.continue}
            </button>
          </div>
        ) : null}

        {liveStatus ? <p className="phase6-status" aria-live="polite">{message}</p> : null}
        {step === "error" ? (
          <div className="phase6-error stack" role="alert">
            <p>{message}</p>
            <button type="button" className="phase6-button" onClick={() => void loadWeather()}>
              {copy.weather.retry}
            </button>
          </div>
        ) : null}
      </section>

      {weather && step === "ready" ? (
        <>
          <section className="phase6-card stack" aria-labelledby="weather-current-title">
            <h2 id="weather-current-title">{copy.weather.current}: {weather.location}</h2>
            <dl className="phase6-facts">
              <div><dt>{copy.weather.temperature}</dt><dd>{weather.current.temperature_c} °C</dd></div>
              <div><dt>{copy.weather.rain}</dt><dd>{weather.current.rain_mm} mm</dd></div>
              <div><dt>{copy.weather.condition}</dt><dd>{conditionLabel(weather.current.weather_code, language)}</dd></div>
              <div><dt>{copy.supplyMap.period}</dt><dd>{weather.observed_at}</dd></div>
            </dl>
            <button type="button" className="phase6-button" onClick={() => void loadWeather()}>
              {copy.weather.retry}
            </button>
          </section>
          <section className="phase6-card stack" aria-labelledby="weather-forecast-title">
            <h2 id="weather-forecast-title">{copy.weather.forecast}</h2>
            <ul className="phase6-forecast-list">
              {weather.forecast.map((day) => (
                <li key={day.date} className="phase6-forecast-card">
                  <h3>{day.date}</h3>
                  <p>{conditionLabel(day.weather_code, language)}</p>
                  <p>{copy.weather.minMax}: {day.temperature_min_c} / {day.temperature_max_c} °C</p>
                  <p>{copy.weather.rain}: {day.rain_mm} mm</p>
                </li>
              ))}
            </ul>
            <p className="phase6-help">
              {copy.weather.attribution}: <a href="https://open-meteo.com/" target="_blank" rel="noreferrer">{weather.attribution}</a>
            </p>
          </section>
          <p className="phase6-provenance">{copy.weather.contextOnly}</p>
        </>
      ) : null}
    </FeaturePage>
  );
}
