import type { AppSurface, Language } from "@tanim/types";

type Messages = {
  titles: Record<AppSurface, string>;
  description: string;
  languageLabel: string;
};

export const messages: Record<Language, Messages> = {
  en: {
    titles: {
      landing: "TANIM landing page",
      auth: "TANIM sign in and registration",
      platform: "TANIM workspace",
      docs: "TANIM help and documentation",
    },
    description: "TANIM helps farmers plan crops with their community. This is a starter page.",
    languageLabel: "Language / Wika",
  },
  tl: {
    titles: {
      landing: "Panimulang pahina ng TANIM",
      auth: "Pag-login at pagpaparehistro sa TANIM",
      platform: "Lugar ng trabaho sa TANIM",
      docs: "Tulong at gabay sa TANIM",
    },
    description:
      "Tinutulungan ng TANIM ang mga magsasaka na magplano ng pananim kasama ang komunidad. Panimulang pahina ito.",
    languageLabel: "Wika / Language",
  },
};
