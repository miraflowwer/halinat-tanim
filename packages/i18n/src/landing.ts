import type { Language } from "@tanim/types";

export const landingMessages: Record<Language, {
  title: string;
  tagline: string;
  intro: string;
  problemTitle: string;
  problem: string;
  solutionTitle: string;
  solution: string;
  howTitle: string;
  steps: string[];
  featuresTitle: string;
  features: string[];
  scopeTitle: string;
  scope: string;
  farmerTitle: string;
  farmer: string;
  cooperativeTitle: string;
  cooperative: string;
  login: string;
  register: string;
  docs: string;
  language: string;
}> = {
  en: {
    title: "TANIM",
    tagline: "Timely Agricultural Network for Informed Market",
    intro: "Plan crops with better community context before planting.",
    problemTitle: "The problem",
    problem: "Farmers may plant the same crop for the same harvest period. This can create too much planned supply.",
    solutionTitle: "The TANIM solution",
    solution: "TANIM compares planned crop area with a reference level and explains the supply pressure in simple terms.",
    howTitle: "How TANIM works",
    steps: [
      "Choose a crop, place, farm area, and harvest period.",
      "Check the explainable Glut Risk before you save the plan.",
      "Compare crops and view community, price, soil, map, and weather context.",
    ],
    featuresTitle: "Core features",
    features: ["Planting plans", "Explainable Glut Risk", "Cooperative planning", "Crop, price, soil, map, and weather context"],
    scopeTitle: "Built for Luzon",
    scope: "TANIM currently supports Luzon, Philippines. Planning supports regions, provinces, and municipalities or cities. Barangay-level planning is not included.",
    farmerTitle: "For Farmers",
    farmer: "Check a crop plan, save your own plans, and join one cooperative with a join code.",
    cooperativeTitle: "For Cooperatives",
    cooperative: "See a private aggregate of active plans linked to your cooperative and share your join code with members.",
    login: "Log in",
    register: "Register",
    docs: "Documentation",
    language: "Language / Wika",
  },
  tl: {
    title: "TANIM",
    tagline: "Timely Agricultural Network for Informed Market",
    intro: "Magplano ng pananim gamit ang mas malinaw na kalagayan ng komunidad bago magtanim.",
    problemTitle: "Ang problema",
    problem: "Maaaring parehong pananim at parehong panahon ng ani ang piliin ng mga magsasaka. Maaari itong magdulot ng sobrang nakaplanong supply.",
    solutionTitle: "Solusyon ng TANIM",
    solution: "Inihahambing ng TANIM ang nakaplanong lawak ng pananim sa batayang antas at ipinapaliwanag ang pressure ng supply.",
    howTitle: "Paano gumagana ang TANIM",
    steps: [
      "Pumili ng pananim, lugar, lawak ng sakahan, at panahon ng ani.",
      "Tingnan ang malinaw na Glut Risk bago i-save ang plano.",
      "Ihambing ang pananim at tingnan ang context sa komunidad, presyo, lupa, mapa, at panahon.",
    ],
    featuresTitle: "Mga pangunahing feature",
    features: ["Mga planting plan", "Malinaw na Glut Risk", "Pagpaplano ng kooperatiba", "Context sa pananim, presyo, lupa, mapa, at panahon"],
    scopeTitle: "Para sa Luzon",
    scope: "Luzon, Pilipinas ang kasalukuyang sakop ng TANIM. Kasama sa pagpaplano ang rehiyon, lalawigan, at bayan o lungsod. Hindi kasama ang barangay.",
    farmerTitle: "Para sa mga Magsasaka",
    farmer: "Suriin ang crop plan, i-save ang sariling plano, at sumali sa isang kooperatiba gamit ang join code.",
    cooperativeTitle: "Para sa mga Kooperatiba",
    cooperative: "Tingnan ang pribadong kabuuan ng mga aktibong planong kaugnay ng kooperatiba at ibahagi ang join code sa mga kasapi.",
    login: "Mag-login",
    register: "Magparehistro",
    docs: "Dokumentasyon",
    language: "Wika / Language",
  },
};
