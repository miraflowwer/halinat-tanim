import type { DocumentPage, Language } from "../content/types";

export function normalizePath(path: string): string {
  if (path === "/") return path;
  return `/${path.split("/").filter(Boolean).join("/")}`;
}

export function findPage(path: string, pages: DocumentPage[]): DocumentPage | undefined {
  const normalized = normalizePath(path);
  return pages.find((page) => page.route === normalized);
}

export function getSavedLanguage(storage: Pick<Storage, "getItem">): Language {
  return storage.getItem("tanim-docs-language") === "tl" ? "tl" : "en";
}

export function saveLanguage(storage: Pick<Storage, "setItem">, language: Language): void {
  storage.setItem("tanim-docs-language", language);
}
