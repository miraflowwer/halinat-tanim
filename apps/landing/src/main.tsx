import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { frontendUrls } from "@tanim/config";
import { messages } from "@tanim/i18n";
import type { Language } from "@tanim/types";
import "@tanim/ui/style.css";

const LANGUAGE_STORAGE_KEY = "tanim-language";

function readLanguage(): Language {
  return window.localStorage.getItem(LANGUAGE_STORAGE_KEY) === "tl" ? "tl" : "en";
}

function LandingPage() {
  const [language, setLanguage] = useState<Language>(readLanguage);
  const copy = messages[language];

  useEffect(() => {
    document.documentElement.lang = language === "tl" ? "tl" : "en";
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  }, [language]);

  function go(url: string) {
    window.location.href = url;
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <span className="brand-link" aria-current="page">
          TANIM
        </span>
        <label className="language-control" htmlFor="language">
          <span>{copy.languageLabel}</span>
          <select
            id="language"
            value={language}
            onChange={(event) => setLanguage(event.target.value as Language)}
          >
            <option value="en">{copy.languageOptions.en}</option>
            <option value="tl">{copy.languageOptions.tl}</option>
          </select>
        </label>
      </header>
      <div className="content-column cover-column stack">
        <h1 className="cover-title">{copy.landing.tagline}</h1>
        <p className="cover-intro">{copy.landing.intro}</p>
        <ul className="ledger-list">
          <li>{copy.landing.ledgerWhat}</li>
          <li>{copy.landing.ledgerWhere}</li>
          <li>{copy.landing.ledgerDemo}</li>
        </ul>
        <div className="button-row">
          <button
            className="primary-button"
            type="button"
            onClick={() => go(`${frontendUrls.auth}/privacy`)}
          >
            {copy.auth.createAccount}
          </button>
          <button
            className="secondary-button"
            type="button"
            onClick={() => go(`${frontendUrls.auth}/login`)}
          >
            {copy.auth.loginButton}
          </button>
        </div>
        <p className="link-row">
          <a href={`${frontendUrls.docs}/`}>{copy.landing.docsLink}</a>
        </p>
        <footer className="muted-text">{copy.description}</footer>
      </div>
    </main>
  );
}

const root = document.getElementById("root");

if (!root) {
  throw new Error("The application root element is missing.");
}

createRoot(root).render(
  <StrictMode>
    <LandingPage />
  </StrictMode>,
);
