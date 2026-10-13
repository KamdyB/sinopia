// frontend/src/ThemeStage.tsx
// The theme switch is a genuine page turn: a clay cover sheet sweeps
// across the viewport, its front face carrying the outgoing exposure
// and its back face coming around carrying the incoming one. The
// document theme swaps under the sheet at the halfway point, so light
// mode is strictly the lighter sibling of the same clay palette.
import { useEffect, useRef, useState, ReactNode } from "react";

type Theme = "light" | "dark";

function systemPrefersDark(): boolean {
  return typeof window !== "undefined" && window.matchMedia
    ? window.matchMedia("(prefers-color-scheme: dark)").matches
    : false;
}

const TURN_LABEL: Record<Theme, string> = {
  light: "Clay wall",
  dark: "Deep clay",
};

export function ThemeStage({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    const initial: Theme = systemPrefersDark() ? "dark" : "light";
    document.documentElement.dataset.theme = initial;
    return initial;
  });
  const [turning, setTurning] = useState(false);
  const [flipping, setFlipping] = useState(false); // overlay mounted and animating
  const timers = useRef<number[]>([]);

  const nextTheme: Theme = theme === "light" ? "dark" : "light";

  useEffect(() => () => { timers.current.forEach((t) => window.clearTimeout(t)); }, []);

  function toggleTheme() {
    if (turning) return;
    setTurning(true);
    setFlipping(true);
    // Halfway through the sweep: commit the theme under the sheet.
    timers.current.push(window.setTimeout(() => {
      document.documentElement.dataset.theme = nextTheme;
      setTheme(nextTheme);
    }, 520));
    // Overlay lifts once the sheet has fully turned.
    timers.current.push(window.setTimeout(() => {
      setFlipping(false);
      setTurning(false);
    }, 1150));
  }

  return (
    <div className="stage">
      {children}

      {flipping && (
        <div className="page-flip is-turning" aria-hidden="true">
          <div className="page-flip__card">
            <div className="page-flip__face" data-theme={theme}>
              <span className="page-flip__seam">{TURN_LABEL[theme]}</span>
            </div>
            <div className="page-flip__face page-flip__face--back" data-theme={nextTheme}>
              <span className="page-flip__seam">{TURN_LABEL[nextTheme]}</span>
            </div>
          </div>
        </div>
      )}

      <button
        type="button"
        className="theme-control"
        onClick={toggleTheme}
        aria-label={`Switch to the ${nextTheme} exposure`}
        aria-pressed={theme === "dark"}
        disabled={turning}
      >
        {theme === "light" ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
            <circle cx="12" cy="12" r="4.2" />
            <path d="M12 2.5v2.4M12 19.1v2.4M4.6 4.6l1.7 1.7M17.7 17.7l1.7 1.7M2.5 12h2.4M19.1 12h2.4M4.6 19.4l1.7-1.7M17.7 6.3l1.7-1.7" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11Z" />
          </svg>
        )}
      </button>
      <span className="theme-team-label" aria-hidden="true">
        Sinopia
      </span>
    </div>
  );
}
