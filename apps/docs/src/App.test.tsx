import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "./App";
import { pages } from "./content/pages";

function setPath(path: string) {
  window.history.replaceState({}, "", path);
}

beforeEach(() => {
  window.localStorage.clear();
  setPath("/");
  document.title = "";
  document.documentElement.lang = "en";
  let description = document.querySelector<HTMLMetaElement>('meta[name="description"]');
  if (!description) {
    description = document.createElement("meta");
    description.name = "description";
    document.head.append(description);
  }
});

afterEach(() => cleanup());

describe("documentation routes", () => {
  it.each(pages.map((page) => [page.route, page.en.title] as const))("renders %s", (route, title) => {
    setPath(route);
    render(<App />);
    expect(screen.getByRole("heading", { level: 1, name: title })).toBeTruthy();
    expect(document.title).toBe(`${title} | TANIM Documentation`);
  });

  it("shows an English not-found page with links to Introduction and Getting Started", () => {
    setPath("/missing-page");
    render(<App />);
    expect(screen.getByRole("heading", { level: 1, name: "Page not found" })).toBeTruthy();
    const suggested = screen.getByRole("navigation", { name: "Suggested pages" });
    expect(within(suggested).getByRole("link", { name: "Introduction" })).toBeTruthy();
    expect(within(suggested).getByRole("link", { name: "Getting Started" })).toBeTruthy();
  });

  it("shows the not-found page in Tagalog", () => {
    window.localStorage.setItem("tanim-docs-language", "tl");
    setPath("/missing-page");
    render(<App />);
    expect(screen.getByRole("heading", { level: 1, name: "Hindi makita ang pahina" })).toBeTruthy();
    const suggested = screen.getByRole("navigation", { name: "Mga mungkahing pahina" });
    expect(within(suggested).getByRole("link", { name: "Panimula" })).toBeTruthy();
    expect(document.documentElement.lang).toBe("tl");
  });
});

describe("navigation and language", () => {
  it("marks the current page in the desktop navigation", () => {
    setPath("/engine");
    render(<App />);
    const current = screen.getAllByRole("link", { name: "How Glut Risk Works" })
      .find((link) => link.getAttribute("aria-current") === "page");
    expect(current).toBeTruthy();
  });

  it("opens mobile navigation and shows the same page links", async () => {
    const user = userEvent.setup();
    render(<App />);
    const menuSummary = screen.getByText("Browse documentation");
    const menu = menuSummary.closest("details");
    expect(menu?.hasAttribute("open")).toBe(false);
    await user.click(menuSummary);
    expect(menu?.hasAttribute("open")).toBe(true);
    const menuNav = menu?.querySelector("nav");
    expect(menuNav).toBeTruthy();
    expect(within(menuNav as HTMLElement).getByRole("link", { name: "Getting Started" })).toBeTruthy();
  });

  it("switches language on the same route and persists the choice", async () => {
    const user = userEvent.setup();
    setPath("/engine/example");
    const view = render(<App />);
    await user.selectOptions(screen.getByRole("combobox", { name: "Language" }), "tl");
    expect(window.location.pathname).toBe("/engine/example");
    expect(window.localStorage.getItem("tanim-docs-language")).toBe("tl");
    expect(document.documentElement.lang).toBe("tl");
    expect(screen.getByRole("heading", { level: 1, name: "Halimbawa ng Engine" })).toBeTruthy();
    view.unmount();
    render(<App />);
    expect(screen.getByRole("heading", { level: 1, name: "Halimbawa ng Engine" })).toBeTruthy();
  });

  it("provides a skip link and one article heading", () => {
    setPath("/data");
    render(<App />);
    expect(screen.getByRole("link", { name: "Skip to main content" }).getAttribute("href")).toBe("#main-content");
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  });

  it("places the skip link first in keyboard focus order", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.tab();
    expect(document.activeElement).toBe(screen.getByRole("link", { name: "Skip to main content" }));
    await user.tab();
    expect(document.activeElement).toBe(screen.getByRole("link", { name: "TANIM documentation home" }));
  });

  it("searches page titles and topic text locally", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.type(screen.getByRole("searchbox", { name: "Search documentation" }), "Eggplant");
    expect(within(screen.getByRole("list", { name: "Search documentation" })).getByRole("link", { name: "Engine Example" })).toBeTruthy();
  });

  it("has valid internal links on all rendered pages", () => {
    const routeSet = new Set(pages.map((page) => page.route));
    for (const page of pages) {
      cleanup();
      setPath(page.route);
      const { container } = render(<App />);
      const internalLinks = Array.from(container.querySelectorAll<HTMLAnchorElement>('a[href^="/"]'));
      for (const link of internalLinks) {
        expect(routeSet.has(link.pathname), `${page.route} -> ${link.pathname}`).toBe(true);
      }
    }
  });

  it("updates the page description when the language changes", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.selectOptions(screen.getByRole("combobox", { name: "Language" }), "tl");
    expect(document.querySelector('meta[name="description"]')?.getAttribute("content")).toBe(
      "Alamin kung ano ang ginagawa ng TANIM, para kanino ito, at saan ito magagamit ngayon.",
    );
  });
});
