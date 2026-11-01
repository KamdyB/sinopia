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
    </div>
  );
}