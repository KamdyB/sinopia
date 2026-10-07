// frontend/src/Glossary.tsx
import { useState } from "react";

const TERMS: { term: string; definition: string }[] = [
  {
    term: "Level",
    definition:
      "Where the athlete stands today: OK, Watch, Act, or Refer. Computed by transparent, rules-based statistics on her own logged numbers, not a diagnosis.",
  },
  {
    term: "RPE",
    definition:
      "Rate of perceived exertion, 0 to 10. How hard the session felt to the athlete, not a device measurement.",
  },
  {
    term: "Session load",
    definition:
      "Minutes played times RPE. The standard session-RPE method for expressing how heavy a session was.",
  },
  {
    term: "Weekly load",
    definition: "Total load across the last 7 days.",
  },
  {
    term: "Baseline",
    definition:
      "Her own recent weekly loads averaged. Every comparison uses her own numbers, never other athletes.",
  },
  {
    term: "Building baseline",
    definition:
      "Fewer than three weeks of history, so there is nothing to compare against yet. No load flag is raised during this period.",
  },
];

export function Glossary() {
  const [openTerm, setOpenTerm] = useState<string | null>(null);
  return (
    <div className="glossary">
      <p className="section-title">What these terms mean</p>
      {TERMS.map(({ term, definition }) => {
        const isOpen = openTerm === term;
        return (
          <div className="glossary-item" key={term}>
            <button
              type="button"
              className="glossary-item__trigger"
              onClick={() => setOpenTerm(isOpen ? null : term)}
              aria-expanded={isOpen}
            >
              <span>{term}</span>
              <span
                className={`glossary-item__chevron ${isOpen ? "is-open" : ""}`}
                aria-hidden="true"
              >
                &#8250;
              </span>
            </button>
            <div className={`glossary-item__body ${isOpen ? "is-open" : ""}`}>
              <div className="glossary-item__inner">
                <p>{definition}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
