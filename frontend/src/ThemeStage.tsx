// frontend/src/ThemeStage.tsx
import { useState, ReactNode } from "react";

type Theme = "light" | "dark";

function initialTheme(): Theme {
  if (typeof window === "undefined") return "light";
  try {
    const saved = window.localStorage.getItem("sinopia-theme");
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    // Keep theme selection usable when storage is unavailable.
  }
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeStage({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    const initial = initialTheme();
    document.documentElement.dataset.theme = initial;
    return initial;
  });
  function toggleTheme() {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    document.documentElement.dataset.theme = next;
    try { window.localStorage.setItem("sinopia-theme", next); } catch {
      // Theme still updates for this page when storage is unavailable.
    }
  }

  return (
    <div className="theme-stage">
      <header className="app-nav">
        <a className="app-nav__brand" href="/" aria-label="Sinopia home"><span className="app-nav__mark">S</span><span>sinopia<span>.</span></span></a>
        <button
          type="button"
          className="theme-control"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
          aria-pressed={theme === "dark"}
        >
          {theme === "light" ? (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" aria-hidden="true">
              <circle cx="12" cy="12" r="4.2" />
              <path d="M12 2.5v2.4M12 19.1v2.4M4.6 4.6l1.7 1.7M17.7 17.7l1.7 1.7M2.5 12h2.4M19.1 12h2.4M4.6 19.4l1.7-1.7M17.7 6.3l1.7-1.7" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11Z" />
            </svg>
          )}
        </button>
      </header>
      <div className="theme-page">{children}</div>
      <button
        type="button"
        className="back-to-top-ball"
        aria-label="Back to top"
        title="Back to top"
        onClick={() => window.scrollTo({ top: 0, behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" })}
      >
        <svg viewBox="0 0 64 64" aria-hidden="true">
          <defs><radialGradient id="app-ball-shade" cx="28%" cy="22%" r="78%"><stop offset="0%" stopColor="#fff8ed" /><stop offset="48%" stopColor="#e8c6a6" /><stop offset="82%" stopColor="#b98563" /><stop offset="100%" stopColor="#754832" /></radialGradient></defs>
          <circle cx="32" cy="32" r="28" fill="url(#app-ball-shade)" stroke="#f9dfc7" strokeWidth="1.5" />
          <path d="m32 20 10 7-4 12H26l-4-12 10-7Zm0 0-1-9M22 27 12 24M26 39l-6 10M38 39l6 10M42 27l10-3" fill="none" stroke="#70452f" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
          <path d="M13 16A27 27 0 0 1 49 12" fill="none" stroke="#fffaf1" strokeWidth="2" strokeLinecap="round" opacity=".7" />
        </svg>
      </button>
    </div>
  );
}