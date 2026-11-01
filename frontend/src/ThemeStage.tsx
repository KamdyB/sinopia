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
        className="silo-companion"
        aria-label="Silo, Sinopia’s football companion. Back to top"
        title="I’m Silo. Tap to head back up."
        onClick={() => window.scrollTo({ top: 0, behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" })}
      >
        <svg viewBox="0 0 100 100" aria-hidden="true">
          <defs><radialGradient id="silo-app-shell" cx="28%" cy="20%" r="80%"><stop offset="0" stopColor="#fffdf5"/><stop offset=".46" stopColor="#f2e6d4"/><stop offset=".8" stopColor="#d4bca4"/><stop offset="1" stopColor="#9e8069"/></radialGradient></defs>
          <circle cx="50" cy="50" r="45" fill="url(#silo-app-shell)" stroke="#fff5e7" strokeWidth="2"/>
          <path d="m50 32 13 9-5 15H42l-5-15 13-9Zm0 0-1-17M37 41 22 36M42 56l-8 16M58 56l8 16M63 41l15-5M34 72l-9 8M66 72l9 8" fill="#30231d" stroke="#6f4d38" strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round"/>
          <ellipse cx="43" cy="48" rx="3.4" ry="5" fill="#30231d"/><ellipse cx="57" cy="48" rx="3.4" ry="5" fill="#30231d"/><path d="M43 63q7 7 14 0" fill="none" stroke="#9a6048" strokeWidth="2.5" strokeLinecap="round"/>
          <path d="M20 24A39 39 0 0 1 56 12" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" opacity=".8"/>
        </svg>
        <span className="silo-companion__name">Silo</span>
      </button>
    </div>
  );
}