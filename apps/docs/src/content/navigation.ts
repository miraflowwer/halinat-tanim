import type { NavigationGroup, SectionId } from "./types";

export const sectionLabels: Record<SectionId, Record<"en" | "tl", string>> = {
  introduction: { en: "Introduction", tl: "Panimula" },
  "getting-started": { en: "Getting Started", tl: "Pagsisimula" },
  "farmer-guide": { en: "Farmer Guide", tl: "Gabay para sa Magsasaka" },
  "cooperative-guide": { en: "Cooperative Guide", tl: "Gabay para sa Kooperatiba" },
  "crop-information": { en: "Crop Information", tl: "Impormasyon sa Pananim" },
  "maps-weather": { en: "Maps and Weather", tl: "Mapa at Panahon" },
  engine: { en: "TANIM Engine", tl: "TANIM Engine" },
  data: { en: "Data", tl: "Datos" },
  limitations: { en: "Limitations", tl: "Mga Limitasyon" },
  help: { en: "Help and FAQ", tl: "Tulong at mga FAQ" },
  "ethics-legal": { en: "Ethics and Legal", tl: "Etika at Legal" },
};

export const navigation: NavigationGroup[] = [
  { section: "introduction", items: [{ route: "/", label: { en: "Introduction", tl: "Panimula" } }] },
  {
    section: "getting-started",
    items: [{ route: "/getting-started", label: { en: "Getting Started", tl: "Pagsisimula" } }],
  },
  {
    section: "farmer-guide",
    items: [{ route: "/farmers", label: { en: "Farmer Guide", tl: "Gabay para sa Magsasaka" } }],
  },
  {
    section: "cooperative-guide",
    items: [{ route: "/cooperatives", label: { en: "Cooperative Guide", tl: "Gabay para sa Kooperatiba" } }],
  },
  {
    section: "crop-information",
    items: [
      { route: "/crops", label: { en: "Crop Library", tl: "Crop Library" } },
      { route: "/crops/prices", label: { en: "Price History", tl: "Kasaysayan ng Presyo" } },
      { route: "/crops/suitability", label: { en: "Soil Suitability", tl: "Kaangkupan ng Lupa" } },
    ],
  },
  {
    section: "maps-weather",
    items: [
      { route: "/maps", label: { en: "Maps and Weather", tl: "Mapa at Panahon" } },
      { route: "/maps/supply", label: { en: "Supply Map", tl: "Supply Map" } },
      { route: "/maps/weather", label: { en: "Weather", tl: "Panahon" } },
    ],
  },
  {
    section: "engine",
    items: [
      { route: "/engine", label: { en: "How Glut Risk Works", tl: "Paano Gumagana ang Glut Risk" } },
      { route: "/engine/risk-levels", label: { en: "Risk Levels", tl: "Mga Antas ng Panganib" } },
      { route: "/engine/example", label: { en: "Engine Example", tl: "Halimbawa ng Engine" } },
    ],
  },
  {
    section: "data",
    items: [
      { route: "/data", label: { en: "Data Overview", tl: "Pangkalahatang-ideya ng Datos" } },
      { route: "/data/sources", label: { en: "Data Sources", tl: "Mga Pinagmulan ng Datos" } },
      { route: "/data/synthetic-data", label: { en: "Synthetic Data", tl: "Synthetic na Datos" } },
      { route: "/data/geography", label: { en: "Geographic Coverage", tl: "Saklaw na Heograpiya" } },
    ],
  },
  { section: "limitations", items: [{ route: "/limitations", label: { en: "Limitations", tl: "Mga Limitasyon" } }] },
  { section: "help", items: [{ route: "/help/faq", label: { en: "FAQ", tl: "Mga FAQ" } }] },
  {
    section: "ethics-legal",
    items: [
      { route: "/legal/privacy", label: { en: "Privacy", tl: "Privacy" } },
      { route: "/legal/ethics", label: { en: "Ethics", tl: "Etika" } },
      { route: "/legal/terms", label: { en: "Terms", tl: "Mga Tuntunin" } },
      { route: "/legal/copyright", label: { en: "Copyright and Licenses", tl: "Copyright at mga Lisensya" } },
    ],
  },
];

export function getSectionLabel(section: SectionId, language: "en" | "tl"): string {
  return sectionLabels[section][language];
}
