import { useEffect, useMemo, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { ApiClientError, apiRequest } from "@tanim/api-client";
import { frontendUrls, privacyNoticeVersion } from "@tanim/config";
import { messages } from "@tanim/i18n";
import type { AuthenticatedResponse, Language, SessionResponse, UserRole } from "@tanim/types";

const LANGUAGE_STORAGE_KEY = "tanim-language";
const CONSENT_STORAGE_KEY = "tanim-registration-consent";

type RegistrationConsent = {
  accepted: boolean;
  optional: boolean;
  version: string;
};

function readLanguage(): Language {
  return window.localStorage.getItem(LANGUAGE_STORAGE_KEY) === "tl" ? "tl" : "en";
}

function storeLanguage(language: Language) {
  window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
}

function readConsent(): RegistrationConsent | null {
  try {
    const value = JSON.parse(window.sessionStorage.getItem(CONSENT_STORAGE_KEY) ?? "null") as
      | RegistrationConsent
      | null;
    return value?.accepted && value.version === privacyNoticeVersion ? value : null;
  } catch {
    return null;
  }
}

function navigate(path: string) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
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

function AuthShell({
  language,
  onLanguageChange,
  children,
}: {
  language: Language;
  onLanguageChange: (value: Language) => void;
  children: ReactNode;
}) {
  const copy = messages[language];
  return (
    <main className="app-shell auth-shell">
      <header className="app-header">
        <a className="brand-link" href={`${frontendUrls.landing}/`}>
          TANIM
        </a>
        <LanguageSelector language={language} onChange={onLanguageChange} />
      </header>
      <div className="content-column">{children}</div>
      <footer className="muted-text">{copy.description}</footer>
    </main>
  );
}

function ErrorMessage({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <p className="form-error" role="alert" aria-live="polite">
      {message}
    </p>
  );
}

function PrivacyPage({
  language,
  onLanguageChange,
}: {
  language: Language;
  onLanguageChange: (value: Language) => void;
}) {
  const copy = messages[language];
  const [required, setRequired] = useState(readConsent()?.accepted ?? false);
  const [optional, setOptional] = useState(readConsent()?.optional ?? false);
  const [error, setError] = useState<string | null>(null);

  function continueToRegister(event: FormEvent) {
    event.preventDefault();
    if (!required) {
      setError(copy.auth.privacyError);
      return;
    }
    window.sessionStorage.setItem(
      CONSENT_STORAGE_KEY,
      JSON.stringify({ accepted: true, optional, version: privacyNoticeVersion }),
    );
    navigate("/register");
  }

  return (
    <AuthShell language={language} onLanguageChange={onLanguageChange}>
      <section className="card stack" aria-labelledby="privacy-title">
        <p className="eyebrow">TANIM</p>
        <h1 id="privacy-title">{copy.auth.privacyTitle}</h1>
        <p>{copy.auth.privacyIntro}</p>
        <ul className="plain-list">
          <li>{copy.auth.privacyNeedsAccount}</li>
          <li>{copy.auth.privacyStoresPlans}</li>
        </ul>
        <details>
          <summary>{copy.auth.privacyNoticeLink}</summary>
          <p>{copy.auth.privacyNoticeBody}</p>
          <p className="muted-text">{privacyNoticeVersion}</p>
        </details>
        <form className="stack" onSubmit={continueToRegister}>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={required}
              onChange={(event) => setRequired(event.target.checked)}
            />
            <span>{copy.auth.privacyRequiredLabel}</span>
          </label>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={optional}
              onChange={(event) => setOptional(event.target.checked)}
            />
            <span>{copy.auth.privacyOptionalLabel}</span>
          </label>
          <ErrorMessage message={error} />
          <button className="primary-button" type="submit">
            {copy.auth.continueButton}
          </button>
        </form>
        <p className="link-row">
          {copy.auth.haveAccount} <a href="/login">{copy.auth.loginLink}</a>
        </p>
      </section>
    </AuthShell>
  );
}

function RegistrationPage({
  language,
  onLanguageChange,
}: {
  language: Language;
  onLanguageChange: (value: Language) => void;
}) {
  const copy = messages[language];
  const consent = readConsent();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("farmer");
  const [organizationName, setOrganizationName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!consent) {
      setError(copy.auth.privacyError);
      return;
    }
    setSubmitting(true);
    try {
      const result = await apiRequest<AuthenticatedResponse>("/auth/register", {
        method: "POST",
        body: {
          display_name: displayName,
          email,
          password,
          role,
          privacy_notice_version: consent.version,
          privacy_accepted: consent.accepted,
          optional_data_improvement_consent: consent.optional,
          preferred_language: language,
          organization_name: role === "cooperative" ? organizationName : undefined,
        },
      });
      storeLanguage(result.user.preferred_language);
      window.sessionStorage.removeItem(CONSENT_STORAGE_KEY);
      window.location.href = `${frontendUrls.platform}/demo`;
    } catch (caught) {
      setError(caught instanceof ApiClientError ? copy.errors[caught.code] ?? caught.message : copy.auth.formError);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell language={language} onLanguageChange={onLanguageChange}>
      <section className="card stack" aria-labelledby="register-title">
        <h1 id="register-title">{copy.auth.registerTitle}</h1>
        {!consent ? (
          <>
            <p className="form-error" role="alert">
              {copy.auth.privacyError}
            </p>
            <button className="secondary-button" type="button" onClick={() => navigate("/privacy")}>
              {copy.auth.continueButton}
            </button>
          </>
        ) : (
          <form className="stack" onSubmit={submit}>
            <label>
              <span>{copy.auth.nameLabel}</span>
              <input required value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
            </label>
            <label>
              <span>{copy.auth.emailLabel}</span>
              <input
                required
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
            <label>
              <span>{copy.auth.passwordLabel}</span>
              <input
                required
                minLength={8}
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
              <small>{copy.auth.passwordHint}</small>
            </label>
            <label>
              <span>{copy.auth.roleLabel}</span>
              <select value={role} onChange={(event) => setRole(event.target.value as UserRole)}>
                <option value="farmer">{copy.auth.farmerOption}</option>
                <option value="cooperative">{copy.auth.cooperativeOption}</option>
              </select>
            </label>
            {role === "cooperative" ? (
              <label>
                <span>{copy.auth.organizationLabel}</span>
                <input required value={organizationName} onChange={(event) => setOrganizationName(event.target.value)} />
                <small>{copy.auth.organizationHint}</small>
              </label>
            ) : null}
            <ErrorMessage message={error} />
            <button className="primary-button" disabled={submitting} type="submit">
              {submitting ? copy.platform.loading : copy.auth.createAccount}
            </button>
          </form>
        )}
        <p className="link-row">
          {copy.auth.haveAccount} <a href="/login">{copy.auth.loginLink}</a>
        </p>
      </section>
    </AuthShell>
  );
}

function LoginPage({
  language,
  onLanguageChange,
}: {
  language: Language;
  onLanguageChange: (value: Language) => void;
}) {
  const copy = messages[language];
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const result = await apiRequest<AuthenticatedResponse>("/auth/login", {
        method: "POST",
        body: { email, password },
      });
      storeLanguage(result.user.preferred_language);
      window.location.href = result.user.has_completed_demo
        ? `${frontendUrls.platform}/dashboard`
        : `${frontendUrls.platform}/demo`;
    } catch (caught) {
      setError(caught instanceof ApiClientError ? copy.errors[caught.code] ?? caught.message : copy.auth.formError);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell language={language} onLanguageChange={onLanguageChange}>
      <section className="card stack" aria-labelledby="login-title">
        <h1 id="login-title">{copy.auth.loginTitle}</h1>
        <form className="stack" onSubmit={submit}>
          <label>
            <span>{copy.auth.emailLabel}</span>
            <input
              required
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label>
            <span>{copy.auth.passwordLabel}</span>
            <input
              required
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          <ErrorMessage message={error} />
          <button className="primary-button" disabled={submitting} type="submit">
            {submitting ? copy.platform.loading : copy.auth.loginButton}
          </button>
        </form>
        <p className="link-row">
          {copy.auth.noAccount} <a href="/privacy">{copy.auth.registerLink}</a>
        </p>
      </section>
    </AuthShell>
  );
}

export function AuthApp() {
  const [language, setLanguage] = useState<Language>(readLanguage);
  const initialPath = window.location.pathname === "/" ? "/privacy" : window.location.pathname;
  const [path, setPath] = useState(initialPath || "/privacy");
  const copy = useMemo(() => messages[language], [language]);

  useEffect(() => {
    const onPopState = () =>
      setPath(window.location.pathname === "/" ? "/privacy" : window.location.pathname || "/privacy");
    window.addEventListener("popstate", onPopState);
    document.documentElement.lang = language === "tl" ? "tl" : "en";
    storeLanguage(language);
    return () => window.removeEventListener("popstate", onPopState);
  }, [language]);

  const onLanguageChange = (value: Language) => setLanguage(value);

  if (path === "/register") {
    return <RegistrationPage language={language} onLanguageChange={onLanguageChange} />;
  }
  if (path === "/login") {
    return <LoginPage language={language} onLanguageChange={onLanguageChange} />;
  }
  if (path !== "/privacy") {
    return (
      <AuthShell language={language} onLanguageChange={onLanguageChange}>
        <section className="card stack">
          <h1>{copy.auth.privacyTitle}</h1>
          <p>{copy.auth.formError}</p>
          <button className="secondary-button" type="button" onClick={() => navigate("/privacy")}>
            {copy.auth.goToTanim}
          </button>
        </section>
      </AuthShell>
    );
  }
  return <PrivacyPage language={language} onLanguageChange={onLanguageChange} />;
}
