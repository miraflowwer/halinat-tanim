import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { ApiClientError, apiRequest, setCsrfToken } from "@tanim/api-client";
import { frontendUrls } from "@tanim/config";
import { messages } from "@tanim/i18n";
import type { AuthUser, DemoResponse, Language, SessionResponse, RiskLevel } from "@tanim/types";

const LANGUAGE_STORAGE_KEY = "tanim-language";
const DEMO_STEP_COUNT = 7;

function readLanguage(): Language {
  return window.localStorage.getItem(LANGUAGE_STORAGE_KEY) === "tl" ? "tl" : "en";
}

function storeLanguage(language: Language) {
  window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
}

function go(path: string) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

function formatArea(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}

function formatRatio(value: number, digits = 2) {
  return value.toFixed(digits);
}

function formatPeriod(start: string, end: string, separator: string) {
  return `${start} ${separator} ${end}`;
}

function localizedCropName(language: Language, english: string, tagalog: string | null) {
  return language === "tl" && tagalog ? tagalog : english;
}

function LanguageSelector({ language, onChange }: { language: Language; onChange: (value: Language) => void }) {
  const copy = messages[language];
  return (
    <label className="language-control" htmlFor="language">
      <span>{copy.languageLabel}</span>
      <select
        id="language"
        value={language}
        onChange={(event) => onChange(event.target.value as Language)}
      >
        <option value="en">{copy.languageOptions.en}</option>
        <option value="tl">{copy.languageOptions.tl}</option>
      </select>
    </label>
  );
}

function PlatformShell({
  language,
  onLanguageChange,
  user,
  onLogout,
  children,
}: {
  language: Language;
  onLanguageChange: (value: Language) => void;
  user: AuthUser;
  onLogout: () => void;
  children: ReactNode;
}) {
  const copy = messages[language];
  return (
    <main className="app-shell platform-shell">
      <header className="app-header">
        <a className="brand-link" href="/home">
          TANIM
        </a>
        <div className="header-actions">
          <span className="user-badge">{user.display_name}</span>
          <LanguageSelector language={language} onChange={onLanguageChange} />
          <button className="quiet-button" type="button" onClick={onLogout}>
            {copy.platform.logoutButton}
          </button>
        </div>
      </header>
      <div className="content-column">{children}</div>
    </main>
  );
}

function MetricList({
  items,
}: {
  items: Array<{ label: string; value: string }>;
}) {
  return (
    <dl className="metric-list">
      {items.map((item) => (
        <div key={item.label}>
          <dt>{item.label}</dt>
          <dd>{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}

function riskLabel(copy: (typeof messages)[Language], risk: RiskLevel) {
  return copy.riskLabels[risk];
}

function DemoView({
  language,
  user,
  onLanguageChange,
  onLogout,
  onComplete,
}: {
  language: Language;
  user: AuthUser;
  onLanguageChange: (value: Language) => void;
  onLogout: () => void;
  onComplete: () => Promise<void>;
}) {
  const copy = messages[language];
  const [scenario, setScenario] = useState<DemoResponse | null>(null);
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [completing, setCompleting] = useState(false);

  async function loadScenario() {
    setLoading(true);
    setError(null);
    try {
      setScenario(await apiRequest<DemoResponse>("/demo/scenario"));
    } catch (caught) {
      setError(caught instanceof ApiClientError ? copy.errors[caught.code] ?? caught.message : copy.platform.demoError);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadScenario();
  }, []);

  async function finish() {
    setCompleting(true);
    setError(null);
    try {
      await onComplete();
    } catch (caught) {
      setError(caught instanceof ApiClientError ? copy.errors[caught.code] ?? caught.message : copy.platform.demoError);
    } finally {
      setCompleting(false);
    }
  }

  const primary = scenario?.primary;
  const comparison = scenario?.comparison;
  let content: ReactNode = null;
  if (primary && comparison) {
    const period = formatPeriod(primary.period_start, primary.period_end, copy.platform.periodSeparator);
    const stepContent: ReactNode[] = [
      <section className="stack" aria-labelledby="demo-step-title" key="welcome">
        <h2 id="demo-step-title">{copy.platform.welcomeTitle}</h2>
        <p>{copy.platform.welcomeBody}</p>
      </section>,
      <section className="stack" aria-labelledby="demo-step-title" key="sample">
        <h2 id="demo-step-title">{copy.platform.sampleTitle}</h2>
        <p>{copy.platform.sampleBody}</p>
        <MetricList
          items={[
            { label: copy.platform.locationLabel, value: primary.geography_name },
            { label: copy.platform.periodLabel, value: period },
            { label: copy.platform.proposedLabel, value: `${formatArea(primary.proposed_area_ha)} ${copy.platform.areaUnit}` },
          ]}
        />
      </section>,
      <section className="stack" aria-labelledby="demo-step-title" key="community">
        <h2 id="demo-step-title">{copy.platform.communityTitle}</h2>
        <MetricList
          items={[
            { label: copy.platform.existingLabel, value: `${formatArea(primary.existing_planned_area_ha)} ${copy.platform.areaUnit}` },
            { label: copy.platform.proposedLabel, value: `${formatArea(primary.proposed_area_ha)} ${copy.platform.areaUnit}` },
            { label: copy.platform.projectedLabel, value: `${formatArea(primary.projected_area_ha)} ${copy.platform.areaUnit}` },
            { label: copy.platform.referenceLabel, value: `${formatArea(primary.reference_area_ha)} ${copy.platform.areaUnit}` },
          ]}
        />
      </section>,
      <section className="stack" aria-labelledby="demo-step-title" key="risk">
        <h2 id="demo-step-title">{copy.platform.riskTitle}</h2>
        <MetricList
          items={[
            { label: copy.platform.ratioLabel, value: formatRatio(primary.ratio) },
            { label: copy.platform.riskTitle, value: riskLabel(copy, primary.risk) },
          ]}
        />
        <p>
          {copy.platform.explanation(
            localizedCropName(language, primary.crop_name_en, primary.crop_name_tl),
            formatArea(primary.existing_planned_area_ha),
            formatArea(primary.proposed_area_ha),
            formatArea(primary.projected_area_ha),
            formatArea(primary.reference_area_ha),
            formatRatio(primary.ratio),
            riskLabel(copy, primary.risk),
          )}
        </p>
      </section>,
      <section className="stack" aria-labelledby="demo-step-title" key="comparison">
        <h2 id="demo-step-title">{copy.platform.comparisonTitle}</h2>
        <p>{comparison.crop_name_en}</p>
        <MetricList
          items={[
            { label: copy.platform.existingLabel, value: `${formatArea(comparison.existing_planned_area_ha)} ${copy.platform.areaUnit}` },
            { label: copy.platform.referenceLabel, value: `${formatArea(comparison.reference_area_ha)} ${copy.platform.areaUnit}` },
            { label: copy.platform.currentPressureLabel, value: `${formatRatio(comparison.current_ratio, 6)} · ${riskLabel(copy, comparison.current_risk)}` },
            { label: copy.platform.hypotheticalPressureLabel, value: `${formatRatio(comparison.projected_ratio_if_same_area, 6)} · ${riskLabel(copy, comparison.projected_risk_if_same_area)}` },
          ]}
        />
      </section>,
      <section className="stack" aria-labelledby="demo-step-title" key="collective">
        <h2 id="demo-step-title">{copy.platform.collectiveTitle}</h2>
        <p>{copy.platform.collectiveBody}</p>
      </section>,
      <section className="stack" aria-labelledby="demo-step-title" key="finish">
        <h2 id="demo-step-title">{copy.platform.finishTitle}</h2>
        <p>{copy.platform.finishBody}</p>
        <button className="primary-button" disabled={completing} type="button" onClick={() => void finish()}>
          {completing ? copy.platform.loading : copy.platform.startButton}
        </button>
      </section>,
    ];
    content = stepContent[step];
  }

  return (
    <PlatformShell
      language={language}
      onLanguageChange={onLanguageChange}
      user={user}
      onLogout={onLogout}
    >
      <section className="card stack" aria-labelledby="demo-title">
        <div className="split-heading">
          <div>
            <p className="eyebrow">{copy.platform.demoTitle}</p>
            <h1 id="demo-title">
              {primary
                ? localizedCropName(language, primary.crop_name_en, primary.crop_name_tl)
                : copy.platform.demoTitle}
            </h1>
          </div>
          <p className="step-count" aria-live="polite">
            {copy.platform.stepLabel} {step + 1} / {DEMO_STEP_COUNT}
          </p>
        </div>
        {loading ? <p aria-live="polite">{copy.platform.loading}</p> : null}
        {error ? (
          <div className="stack" role="alert">
            <p className="form-error">{error}</p>
            <button className="secondary-button" type="button" onClick={() => void loadScenario()}>
              {copy.platform.retryButton}
            </button>
          </div>
        ) : null}
        {!loading && !error ? content : null}
        {!loading && !error && primary && step < DEMO_STEP_COUNT - 1 ? (
          <div className="button-row">
            <button
              className="secondary-button"
              disabled={step === 0}
              type="button"
              onClick={() => setStep((current) => Math.max(0, current - 1))}
            >
              {copy.platform.backButton}
            </button>
            <button className="primary-button" type="button" onClick={() => setStep((current) => current + 1)}>
              {copy.platform.nextButton}
            </button>
          </div>
        ) : null}
      </section>
    </PlatformShell>
  );
}

function HomeView({
  language,
  user,
  onLanguageChange,
  onLogout,
}: {
  language: Language;
  user: AuthUser;
  onLanguageChange: (value: Language) => void;
  onLogout: () => void;
}) {
  const copy = messages[language];
  return (
    <PlatformShell
      language={language}
      onLanguageChange={onLanguageChange}
      user={user}
      onLogout={onLogout}
    >
      <section className="card stack" aria-labelledby="home-title">
        <p className="eyebrow">{copy.platform.homeTitle}</p>
        <h1 id="home-title">{copy.platform.homeTitle}</h1>
        <p>{copy.platform.homeBody}</p>
        <div className="button-row">
          <button className="secondary-button" type="button" onClick={() => go("/demo?replay=1")}>
            {copy.platform.replayButton}
          </button>
        </div>
      </section>
    </PlatformShell>
  );
}

export function PlatformApp() {
  const [language, setLanguage] = useState<Language>(readLanguage);
  const [path, setPath] = useState(window.location.pathname || "/home");
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const copy = useMemo(() => messages[language], [language]);
  const replay = new URLSearchParams(window.location.search).get("replay") === "1";

  useEffect(() => {
    const onPopState = () => setPath(window.location.pathname || "/home");
    window.addEventListener("popstate", onPopState);
    document.documentElement.lang = language === "tl" ? "tl" : "en";
    storeLanguage(language);
    return () => window.removeEventListener("popstate", onPopState);
  }, [language]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    void apiRequest<SessionResponse>("/auth/session")
      .then((result) => {
        if (!active) return;
        setSession(result);
        if (!result.authenticated) {
          window.location.href = `${frontendUrls.auth}/login`;
          return;
        }
        if (path === "/home" && !result.user.has_completed_demo) {
          go("/demo");
          return;
        }
        if (path === "/demo" && result.user.has_completed_demo && !replay) {
          go("/home");
        }
      })
      .catch((caught) => {
        if (!active) return;
        setError(caught instanceof ApiClientError ? copy.errors[caught.code] ?? caught.message : copy.platform.demoError);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [path, replay]);

  async function completeDemo() {
    await apiRequest<{ has_completed_demo: boolean }>("/demo/complete", { method: "POST" });
    setSession((current) =>
      current?.authenticated
        ? { ...current, user: { ...current.user, has_completed_demo: true } }
        : current,
    );
    go("/home");
  }

  async function logout() {
    try {
      await apiRequest<{ authenticated: false }>("/auth/logout", { method: "POST" });
    } finally {
      setCsrfToken(null);
      window.location.href = `${frontendUrls.auth}/login`;
    }
  }

  const onLanguageChange = (value: Language) => setLanguage(value);
  if (loading) {
    return <main className="app-shell"><p aria-live="polite">{copy.platform.loading}</p></main>;
  }
  if (error) {
    return <main className="app-shell"><p className="form-error" role="alert">{error}</p></main>;
  }
  if (!session?.authenticated) return null;
  if (path === "/demo") {
    return (
      <DemoView
        language={language}
        user={session.user}
        onLanguageChange={onLanguageChange}
        onLogout={() => void logout()}
        onComplete={completeDemo}
      />
    );
  }
  return (
    <HomeView
      language={language}
      user={session.user}
      onLanguageChange={onLanguageChange}
      onLogout={() => void logout()}
    />
  );
}
