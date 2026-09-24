import type { ContentBlock as ContentBlockData, Language } from "../content/types";

const calloutLabels: Record<Language, Record<"note" | "important" | "data" | "limitation", string>> = {
  en: { note: "Note", important: "Important", data: "Data note", limitation: "Limitation" },
  tl: { note: "Tandaan", important: "Mahalaga", data: "Tala sa datos", limitation: "Limitasyon" },
};

type Props = { block: ContentBlockData; language: Language };

export function ContentBlock({ block, language }: Props) {
  if (block.kind === "text") {
    return (
      <section className="content-section">
        {block.heading ? <h2>{block.heading}</h2> : null}
        {block.paragraphs.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
      </section>
    );
  }

  if (block.kind === "list") {
    return (
      <section className="content-section">
        {block.heading ? <h2>{block.heading}</h2> : null}
        <ul className="content-list">
          {block.items.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </section>
    );
  }

  if (block.kind === "callout") {
    return (
      <aside className={`callout callout-${block.calloutKind}`} aria-label={calloutLabels[language][block.calloutKind]}>
        <p className="callout-label">{calloutLabels[language][block.calloutKind]}</p>
        <h2>{block.title}</h2>
        <p>{block.text}</p>
      </aside>
    );
  }

  if (block.kind === "definition") {
    return (
      <dl className="definition">
        <dt>{block.term}</dt>
        <dd>{block.text}</dd>
      </dl>
    );
  }

  if (block.kind === "formula") {
    return (
      <figure className="formula">
        <figcaption>{block.heading}</figcaption>
        <div className="formula-lines" aria-label={block.lines.join(". ")}>
          {block.lines.map((line) => <p key={line}>{line}</p>)}
        </div>
        <p>{block.explanation}</p>
      </figure>
    );
  }

  if (block.kind === "example") {
    return (
      <section className="example">
        <h2>{block.heading}</h2>
        <dl>
          {block.values.map(({ label, value }) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
        <p>{block.calculation}</p>
        <p className="example-result">{block.result}</p>
        {block.note ? <p>{block.note}</p> : null}
      </section>
    );
  }

  if (block.kind === "faq") {
    return (
      <div className="faq-list">
        {block.items.map(({ question, answer }) => (
          <details className="faq-item" key={question}>
            <summary>{question}</summary>
            <p>{answer}</p>
          </details>
        ))}
      </div>
    );
  }

  return (
    <section className="content-section source-list">
      <h2>{language === "en" ? "Recorded sources" : "Mga naitalang source"}</h2>
      {block.items.map((item) => (
        <article className="source-item" key={item.name}>
          <h3>{item.name}</h3>
          <p className="source-category">{item.category}</p>
          <p>{item.use}</p>
          <p>
            <a href={item.url} target="_blank" rel="noreferrer">
              {language === "en" ? "Open source page" : "Buksan ang pahina ng source"}
              <span className="visually-hidden">: {item.name}</span>
            </a>
          </p>
          <p>{item.terms}</p>
        </article>
      ))}
    </section>
  );
}
