import { useState } from "react";
import { messages } from "@tanim/i18n";
import type { AppSurface, Language } from "@tanim/types";

type PlaceholderPageProps = {
  surface: AppSurface;
};

export function PlaceholderPage({ surface }: PlaceholderPageProps) {
  const [language, setLanguage] = useState<Language>("en");
  const copy = messages[language];

  return (
    <main>
      <h1>{copy.titles[surface]}</h1>
      <p>{copy.description}</p>
      <label htmlFor="language">{copy.languageLabel}</label>
      <select
        id="language"
        name="language"
        value={language}
        onChange={(event) => setLanguage(event.target.value as Language)}
      >
        <option value="en">English</option>
        <option value="tl">Tagalog</option>
      </select>
    </main>
  );
}
