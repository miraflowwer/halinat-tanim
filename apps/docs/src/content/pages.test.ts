import { describe, expect, it } from "vitest";
import { navigation } from "./navigation";
import { notFoundCopy, pages } from "./pages";
import { reconciliationItems } from "./reconciliation";
import type { ContentBlock } from "./types";

function blockText(block: ContentBlock): string {
  if (block.kind === "text") return [block.heading, ...block.paragraphs].filter(Boolean).join(" ");
  if (block.kind === "list") return [block.heading, ...block.items].filter(Boolean).join(" ");
  if (block.kind === "callout") return `${block.title} ${block.text}`;
  if (block.kind === "definition") return `${block.term} ${block.text}`;
  if (block.kind === "formula") return `${block.heading} ${block.lines.join(" ")} ${block.explanation}`;
  if (block.kind === "example") {
    return [block.heading, ...block.values.flatMap((value) => [value.label, value.value]), block.calculation, block.result, block.note]
      .filter(Boolean).join(" ");
  }
  if (block.kind === "faq") return block.items.map((item) => `${item.question} ${item.answer}`).join(" ");
  return block.items.map((item) => `${item.name} ${item.category} ${item.use} ${item.terms}`).join(" ");
}

describe("documentation content", () => {
  it("has unique, stable routes with English and Tagalog metadata", () => {
    const routes = pages.map((page) => page.route);
    expect(new Set(routes).size).toBe(routes.length);
    for (const page of pages) {
      expect(page.route.startsWith("/")).toBe(true);
      expect(page.en.title.trim()).not.toBe("");
      expect(page.en.description.trim()).not.toBe("");
      expect(page.tl.title.trim()).not.toBe("");
      expect(page.tl.description.trim()).not.toBe("");
      expect(page.en.blocks.length).toBeGreaterThan(0);
      expect(page.tl.blocks.length).toBeGreaterThan(0);
    }
  });

  it("includes every required top-level documentation section", () => {
    const sections = new Set(navigation.map((group) => group.section));
    expect(sections).toEqual(new Set([
      "introduction", "getting-started", "farmer-guide", "cooperative-guide", "crop-information",
      "maps-weather", "engine", "data", "limitations", "help", "ethics-legal",
    ]));
  });

  it("has a page for every navigation route", () => {
    const routes = new Set(pages.map((page) => page.route));
    for (const group of navigation) {
      for (const item of group.items) expect(routes.has(item.route), item.route).toBe(true);
    }
  });

  it("has a page for every related link", () => {
    const routes = new Set(pages.map((page) => page.route));
    for (const page of pages) {
      for (const route of page.related) expect(routes.has(route), `${page.route} -> ${route}`).toBe(true);
    }
  });

  it("includes the core routes requested for the initial documentation", () => {
    const routes = new Set(pages.map((page) => page.route));
    for (const route of ["/", "/getting-started", "/engine", "/data", "/limitations", "/help/faq", "/legal/privacy"]) {
      expect(routes.has(route), route).toBe(true);
    }
  });

  it("includes localized not-found copy with a title and explanation", () => {
    expect(notFoundCopy.en.title).toBeTruthy();
    expect(notFoundCopy.en.blocks.length).toBeGreaterThan(0);
    expect(notFoundCopy.tl.title).toBeTruthy();
    expect(notFoundCopy.tl.blocks.length).toBeGreaterThan(0);
  });

  it("keeps the canonical engine formulas and thresholds in the guide", () => {
    const engineText = pages.find((page) => page.route === "/engine")?.en.blocks.map(blockText).join(" ") ?? "";
    const thresholds = pages.find((page) => page.route === "/engine/risk-levels")?.en.blocks.map(blockText).join(" ") ?? "";
    expect(engineText).toContain("Existing Relevant Planned Area + Proposed Area");
    expect(engineText).toContain("Projected Planned Area / Reference Area");
    expect(thresholds).toContain("below 0.90");
    expect(thresholds).toContain("from 0.90 through 1.10");
    expect(thresholds).toContain("above 1.10");
  });

  it("keeps the canonical Tomato and Eggplant figures", () => {
    const tomato = pages.find((page) => page.route === "/engine/example")?.en.blocks.map(blockText).join(" ") ?? "";
    expect(tomato).toContain("32 ha + 8 ha = 40 ha");
    expect(tomato).toContain("40 ha / 25 ha = 1.60");
    expect(tomato).toContain("12 ha / 18 ha = about 0.666667");
  });

  it("does not contain em dashes or Markdown bold syntax in user content", () => {
    const allContent = [
      ...pages.flatMap((page) => [page.en.title, page.en.description, ...page.en.blocks.map(blockText), page.tl.title, page.tl.description, ...page.tl.blocks.map(blockText)]),
      notFoundCopy.en.title,
      ...notFoundCopy.en.blocks.map(blockText),
      notFoundCopy.tl.title,
      ...notFoundCopy.tl.blocks.map(blockText),
    ].join("\n");
    expect(allContent).not.toContain("—");
    expect(allContent).not.toContain("**");
  });

  it("has no remaining phase reconciliation records after the product audit", () => {
    expect(reconciliationItems).toHaveLength(0);
  });
});
