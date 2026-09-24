import { useEffect, useState } from "react";
import { ContentBlock } from "./components/ContentBlock";
import { DocLayout, routeCopy } from "./components/DocLayout";
import { getSectionLabel } from "./content/navigation";
import { notFoundCopy, pages } from "./content/pages";
import type { Language } from "./content/types";
import { findPage, getSavedLanguage, normalizePath, saveLanguage } from "./routing/routes";

function usePathname(): string {
  const [path, setPath] = useState(() => normalizePath(window.location.pathname));
  useEffect(() => {
    const updatePath = () => setPath(normalizePath(window.location.pathname));
    window.addEventListener("popstate", updatePath);
    return () => window.removeEventListener("popstate", updatePath);
  }, []);
  return path;
}

export function App() {
  const currentPath = usePathname();
  const [language, setLanguage] = useState<Language>(() => getSavedLanguage(window.localStorage));
  const page = findPage(currentPath, pages);
  const copy = page ? page[language] : notFoundCopy[language];

  useEffect(() => {
    document.documentElement.lang = language;
    document.title = `${copy.title} | TANIM Documentation`;
    const description = document.querySelector<HTMLMetaElement>('meta[name="description"]');
    if (description) description.content = copy.description;
  }, [copy.description, copy.title, language]);

  function changeLanguage(nextLanguage: Language) {
    setLanguage(nextLanguage);
    saveLanguage(window.localStorage, nextLanguage);
  }

  return (
    <DocLayout currentPath={page?.route ?? ""} language={language} onLanguageChange={changeLanguage}>
      <main id="main-content" className="article-layout" tabIndex={-1}>
        <article className="article" lang={language} data-route={page?.route ?? currentPath}>
          {page ? <p className="article-section">{getSectionLabel(page.section, language)}</p> : null}
          <h1>{copy.title}</h1>
          <p className="article-description">{copy.description}</p>
          {copy.blocks.map((block, index) => <ContentBlock key={`${block.kind}-${index}`} block={block} language={language} />)}
          {!page ? (
            <nav className="not-found-links" aria-label={language === "en" ? "Suggested pages" : "Mga mungkahing pahina"}>
              <a href="/">{routeCopy[language].intro}</a>
              <a href="/getting-started">{routeCopy[language].gettingStarted}</a>
            </nav>
          ) : null}
          {page?.related.length ? (
            <nav className="related-links" aria-label={routeCopy[language].related}>
              <h2>{routeCopy[language].related}</h2>
              <ul>
                {page.related.map((route) => {
                  const relatedPage = pages.find((candidate) => candidate.route === route);
                  return relatedPage ? <li key={route}><a href={route}>{relatedPage[language].title}</a></li> : null;
                })}
              </ul>
            </nav>
          ) : null}
        </article>
      </main>
    </DocLayout>
  );
}
