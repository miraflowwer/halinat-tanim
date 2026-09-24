import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { frontendUrls } from "@tanim/config";
import { landingMessages, messages } from "@tanim/i18n";
import type { Language } from "@tanim/types";
import "@tanim/ui/style.css";
import "./landing.css";

const LANGUAGE_STORAGE_KEY = "tanim-language";

function LandingApp() {
  const [language, setLanguage] = useState<Language>(() =>
    window.localStorage.getItem(LANGUAGE_STORAGE_KEY) === "tl" ? "tl" : "en",
  );
  const copy = landingMessages[language];

  useEffect(() => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
    document.documentElement.lang = language;
  }, [language]);

  return (
    <div className="landing-page">
      <header className="landing-header">
        <a className="landing-brand" href="/">{copy.title}</a>
        <nav aria-label="Main navigation" className="landing-nav">
          <a href={`${frontendUrls.auth}/login`}>{copy.login}</a>
          <a href={`${frontendUrls.auth}/privacy`}>{copy.register}</a>
          <a href={frontendUrls.docs} target="_blank" rel="noreferrer">{copy.docs}</a>
          <label className="landing-language" htmlFor="landing-language">
            <span>{copy.language}</span>
            <select
              id="landing-language"
              value={language}
              onChange={(event) => setLanguage(event.target.value as Language)}
            >
              <option value="en">{messages[language].languageOptions.en}</option>
              <option value="tl">{messages[language].languageOptions.tl}</option>
            </select>
          </label>
        </nav>
      </header>

      <main>
        <section className="landing-hero" aria-labelledby="landing-title">
          <p className="landing-eyebrow">{copy.title}</p>
          <h1 id="landing-title">{copy.tagline}</h1>
          <p className="landing-lead">{copy.intro}</p>
          <div className="landing-actions">
            <a className="landing-button landing-button-primary" href={`${frontendUrls.auth}/privacy`}>{copy.register}</a>
            <a className="landing-button landing-button-secondary" href={`${frontendUrls.auth}/login`}>{copy.login}</a>
          </div>
        </section>

        <section className="landing-grid" aria-label={copy.solutionTitle}>
          <article className="landing-card"><h2>{copy.problemTitle}</h2><p>{copy.problem}</p></article>
          <article className="landing-card"><h2>{copy.solutionTitle}</h2><p>{copy.solution}</p></article>
        </section>

        <section className="landing-section" aria-labelledby="how-title">
          <h2 id="how-title">{copy.howTitle}</h2>
          <ol className="landing-steps">{copy.steps.map((step) => <li key={step}>{step}</li>)}</ol>
        </section>

        <section className="landing-section" aria-labelledby="features-title">
          <h2 id="features-title">{copy.featuresTitle}</h2>
          <ul className="landing-feature-list">{copy.features.map((feature) => <li key={feature}>{feature}</li>)}</ul>
        </section>

        <section className="landing-section landing-scope" aria-labelledby="scope-title">
          <h2 id="scope-title">{copy.scopeTitle}</h2>
          <p>{copy.scope}</p>
        </section>

        <section className="landing-grid" aria-label={copy.farmerTitle}>
          <article className="landing-card"><h2>{copy.farmerTitle}</h2><p>{copy.farmer}</p></article>
          <article className="landing-card"><h2>{copy.cooperativeTitle}</h2><p>{copy.cooperative}</p></article>
        </section>
      </main>

      <footer className="landing-footer"><span>{copy.title}</span><a href={frontendUrls.docs} target="_blank" rel="noreferrer">{copy.docs}</a></footer>
    </div>
  );
}

const root = document.getElementById("root");
if (!root) throw new Error("The application root element is missing.");
createRoot(root).render(<StrictMode><LandingApp /></StrictMode>);
