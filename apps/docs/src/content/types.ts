export type Language = "en" | "tl";

export type SectionId =
  | "introduction"
  | "getting-started"
  | "farmer-guide"
  | "cooperative-guide"
  | "crop-information"
  | "maps-weather"
  | "engine"
  | "data"
  | "limitations"
  | "help"
  | "ethics-legal";

export type CalloutKind = "note" | "important" | "data" | "limitation";

export type ContentBlock =
  | { kind: "text"; heading?: string; paragraphs: string[] }
  | { kind: "list"; heading?: string; items: string[] }
  | {
      kind: "callout";
      calloutKind: CalloutKind;
      title: string;
      text: string;
    }
  | { kind: "definition"; term: string; text: string }
  | {
      kind: "formula";
      heading: string;
      lines: string[];
      explanation: string;
    }
  | {
      kind: "example";
      heading: string;
      values: { label: string; value: string }[];
      calculation: string;
      result: string;
      note?: string;
    }
  | {
      kind: "faq";
      items: { question: string; answer: string }[];
    }
  | {
      kind: "sources";
      items: {
        name: string;
        category: string;
        use: string;
        url: string;
        terms: string;
      }[];
    };

export type PageCopy = {
  title: string;
  description: string;
  blocks: ContentBlock[];
};

export type DocumentPage = {
  route: string;
  section: SectionId;
  en: PageCopy;
  tl: PageCopy;
  related: string[];
};

export type NavigationGroup = {
  section: SectionId;
  items: { route: string; label: Record<Language, string> }[];
};
