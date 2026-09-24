import type { SectionId } from "./types";

export const reconciliationItems: {
  marker: "TODO-PHASE-RECONCILE";
  phase: 4 | 5 | 6;
  routes: string[];
  section: SectionId;
  topics: string[];
}[] = [
  {
    marker: "TODO-PHASE-RECONCILE",
    phase: 4,
    section: "getting-started",
    routes: ["/getting-started", "/farmers", "/cooperatives", "/legal/privacy"],
    topics: ["registration", "login", "consent", "sessions", "first-time demo", "seeded demo accounts"],
  },
  {
    marker: "TODO-PHASE-RECONCILE",
    phase: 5,
    section: "farmer-guide",
    routes: ["/farmers", "/cooperatives", "/engine", "/engine/example"],
    topics: ["plan creation", "plan changes", "saved plans", "cooperative aggregation"],
  },
  {
    marker: "TODO-PHASE-RECONCILE",
    phase: 6,
    section: "maps-weather",
    routes: ["/crops", "/crops/prices", "/crops/suitability", "/maps", "/maps/supply", "/maps/weather"],
    topics: ["crop screens", "price history", "suitability", "map controls", "weather provider and retry flow"],
  },
];
