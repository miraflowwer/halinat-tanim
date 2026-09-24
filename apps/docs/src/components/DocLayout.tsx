import { useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { navigation, getSectionLabel } from "../content/navigation";
import { pages } from "../content/pages";
import type { DocumentPage, Language } from "../content/types";

const interfaceCopy: Record<Language, {
  searchLabel: string;
  searchPlaceholder: string;
  searchNoResults: string;
  menu: string;
  related: string;
  intro: string;
  gettingStarted: string;
  footerLabel: string;
  landing: string;
}> = {
  en: {
    searchLabel: "Search documentation",
    searchPlaceholder: "Search pages and topics",
    searchNoResults: "No pages match this search.",
    menu: "Browse documentation",
    related: "Related pages",
    intro: "Introduction",
    gettingStarted: "Getting Started",
    footerLabel: "Legal and project information",
    landing: "TANIM landing page",
  },
  tl: {
    searchLabel: "Maghanap sa dokumentasyon",
    searchPlaceholder: "Maghanap ng pahina o paksa",
    searchNoResults: "Walang pahinang tumutugma sa paghahanap na ito.",
    menu: "Tingnan ang dokumentasyon",
    related: "Mga kaugnay na pahina",
    intro: "Panimula",
    gettingStarted: "Pagsisimula",
    footerLabel: "Legal at impormasyon ng proyekto",
    landing: "TANIM landing page",
  },
};

function copyText(page: DocumentPage, language: Language): string {
  const copy = page[language];
  const blockText = copy.blocks.map((block) => {
    if (block.kind === "text") return [block.heading, ...block.paragraphs].filter(Boolean).join(" ");
    if (block.kind === "list") return [block.heading, ...block.items].filter(Boolean).join(" ");
    if (block.kind === "callout") return `${block.title} ${block.text}`;
    if (block.kind === "definition") return `${block.term} ${block.text}`;
    if (block.kind === "formula") return `${block.heading} ${block.lines.join(" ")} ${block.explanation}`;
    if (block.kind === "example") {
      return [block.heading, ...block.values.flatMap((item) => [item.label, item.value]), block.calculation, block.result, block.note]
        .filter(Boolean).join(" ");
    }
    if (block.kind === "faq") return block.items.map((item) => `${item.question} ${item.answer}`).join(" ");
    return block.items.map((item) => `${item.name} ${item.category} ${item.use} ${item.terms}`).join(" ");
  });
  return `${copy.title} ${copy.description} ${getSectionLabel(page.section, language)} ${blockText.join(" ")}`;
}

function DocumentationNavigation({ currentPath, language, onNavigate }: {
  currentPath: string;
  language: Language;
  onNavigate?: () => void;
}) {
  return (
    <nav aria-label={language === "en" ? "Documentation sections" : "Mga seksyon ng dokumentasyon"}>
      <ul className="nav-groups">
        {navigation.map((group) => (
          <li key={group.section}>
            <details open>
              <summary>{getSectionLabel(group.section, language)}</summary>
              <ul>
                {group.items.map((item) => (
                  <li key={item.route}>
                    <a href={item.route} aria-current={currentPath === item.route ? "page" : undefined} onClick={onNavigate}>
                      {item.label[language]}
                    </a>
                  </li>
                ))}
              </ul>
            </details>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export function DocLayout({ currentPath, language, onLanguageChange, children }: {
  currentPath: string;
  language: Language;
  onLanguageChange: (language: Language) => void;
  children: ReactNode;
}) {
  const copy = interfaceCopy[language];
  const [query, setQuery] = useState("");
  const mobileMenu = useRef<HTMLDetailsElement>(null);
  const results = useMemo(() => {
    const term = query.trim().toLocaleLowerCase(language === "tl" ? "tl-PH" : "en");
    if (!term) return [];
    return pages
      .filter((page) => copyText(page, language).toLocaleLowerCase(language === "tl" ? "tl-PH" : "en").includes(term))
      .slice(0, 7);
  }, [language, query]);

  return (
    <>
      <a className="skip-link" href="#main-content">
        {language === "en" ? "Skip to main content" : "Lumaktaw sa pangunahing nilalaman"}
      </a>
      <header className="site-header">
        <a className="site-name" href="/" aria-label="TANIM documentation home">TANIM <span>{language === "en" ? "Documentation" : "Dokumentasyon"}</span></a>
        <div className="header-tools">
          <div className="search-wrap">
            <label htmlFor="docs-search">{copy.searchLabel}</label>
            <input
              id="docs-search"
              type="search"
              value={query}
              placeholder={copy.searchPlaceholder}
              onChange={(event) => setQuery(event.target.value)}
              aria-controls="docs-search-results"
            />
            {query.trim() ? (
              <div className="search-results" id="docs-search-results">
                {results.length ? (
                  <ul aria-label={copy.searchLabel}>
                    {results.map((page) => (
                      <li key={page.route}>
                        <a href={page.route}>{page[language].title}</a>
                        <p>{page[language].description}</p>
                      </li>
                    ))}
                  </ul>
                ) : <p role="status">{copy.searchNoResults}</p>}
              </div>
            ) : null}
          </div>
          <div className="language-control">
            <label htmlFor="docs-language">{language === "en" ? "Language" : "Wika"}</label>
            <select id="docs-language" value={language} onChange={(event) => onLanguageChange(event.target.value as Language)}>
              <option value="en">English</option>
              <option value="tl">Tagalog</option>
            </select>
          </div>
          <details className="mobile-menu" ref={mobileMenu}>
            <summary>{copy.menu}</summary>
            <div className="mobile-menu-content">
              <DocumentationNavigation
                currentPath={currentPath}
                language={language}
                onNavigate={() => {
                  if (mobileMenu.current) mobileMenu.current.open = false;
                }}
              />
            </div>
          </details>
        </div>
      </header>
      <div className="site-layout">
        <aside className="desktop-sidebar" aria-label={language === "en" ? "Documentation navigation" : "Navigation ng dokumentasyon"}>
          <DocumentationNavigation currentPath={currentPath} language={language} />
        </aside>
        {children}
      </div>
      <footer className="site-footer">
        <div>
          <h2>{copy.footerLabel}</h2>
          <ul>
            <li><a href="/legal/privacy">Privacy</a></li>
            <li><a href="/legal/ethics">{language === "en" ? "Ethics" : "Etika"}</a></li>
            <li><a href="/legal/terms">{language === "en" ? "Terms" : "Mga Tuntunin"}</a></li>
            <li><a href="/legal/copyright">{language === "en" ? "Copyright and Licenses" : "Copyright at mga Lisensya"}</a></li>
          </ul>
        </div>
        <a href="http://127.0.0.1:3000">{copy.landing}</a>
      </footer>
    </>
  );
}

export const routeCopy = interfaceCopy;
