// landing/src/App.tsx  — LANDING PAGE (imports LiveDemo, nothing from the coach tool)
import { useEffect, useState } from "react";
import { LiveDemo } from "./LiveDemo";
import { LegalPage } from "./LegalPage";

// Dev: the coach tool runs on 5173. In production, deploy the landing page at
// "/" and the coach tool under "/app/", then set this to "/app/".
const COACH_APP_URL = (import.meta.env.VITE_COACH_APP_URL ?? (import.meta.env.PROD ? "" : "http://localhost:5173")).replace(/\/+$/, "");
const SIGN_IN_URL = `${COACH_APP_URL}/sign-in`;
const SIGN_UP_URL = `${COACH_APP_URL}/sign-up`;
// Contact placeholder — replace with the real inbox before shipping.
const CONTACT_EMAIL = import.meta.env.VITE_CONTACT_EMAIL as string | undefined;

const SOURCES: { text: string; url: string | null }[] = [
  {
    text: "van Loggerenberg, C., Ramagole, D. A., Jansen van Rensburg, A., Janse van Rensburg, D. C., & Boer, P. (2025). Sports-related injuries and illnesses amongst adolescent athletes in an urban sports medicine practice setting. South African Journal of Sports Medicine, 37(1).",
    url: "https://scielo.org.za/scielo.php?script=sci_arttext&pid=S1015-51632025000100021",
  },
  {
    text: "Cowley, E. S., Olenick, A. A., McNulty, K. L., & Ross, E. Z. (2021). \u201cInvisible Sportswomen\u201d: The Sex Data Gap in Sport and Exercise Science Research. Women in Sport and Physical Activity Journal, 29(2), 146\u2013151.",
    url: "https://journals.humankinetics.com/view/journals/wspaj/29/2/article-p146.xml",
  },
  {
    text: "Nigerian Journal of Human Movement, Wellness, Leisure, and Sports (2025). Grassroots football development in Nigeria: professional development rated low (weighted mean 1.77); 72.2% of respondents on the age-grade structure.",
    url: null,
  },
  {
    text: "2024 Women\u2019s Africa Cup of Nations (played July 2025, Morocco): Nigeria beat Morocco 3\u20132 in the final in Rabat, a record-extending tenth title.",
    url: "https://en.wikipedia.org/wiki/2024_Women%27s_Africa_Cup_of_Nations",
  },
  {
    text: "Foster, C., et al. (2001). A new approach to monitoring exercise training. Journal of Strength and Conditioning Research, 15(1), 109\u2013114.",
    url: null,
  },
  {
    text: "Gabbett, T. J. (2016). The training\u2013injury prevention paradox: should athletes be training smarter and harder? British Journal of Sports Medicine, 50(5), 273\u2013280.",
    url: "https://bjsm.bmj.com/content/50/5/273",
  },
  {
    text: "Impellizzeri, F. M., et al. (2020). Acute:Chronic Workload Ratio: conceptual issues and fundamental pitfalls. International Journal of Sports Physiology and Performance.",
    url: null,
  },
];

export default function App() {
  const [theme, setTheme] = useState<"light" | "dark">(() =>
    window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
  );

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  if (window.location.pathname === "/privacy") return <LegalPage kind="privacy" />;
  if (window.location.pathname === "/terms") return <LegalPage kind="terms" />;
  if (window.location.pathname === "/delete-account") return <LegalPage kind="delete-account" />;

  return (
    <div className="landing">
      <header className="nav">
        <span className="nav__wordmark">Sinopia</span>
        <div className="nav__actions">
          <button
            type="button"
            className="btn theme-toggle"
            aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
            aria-pressed={theme === "dark"}
            onClick={() => setTheme((current) => current === "dark" ? "light" : "dark")}
          >
            {theme === "dark" ? "Light mode" : "Dark mode"}
          </button>
          <a className="btn nav__cta" href={SIGN_IN_URL}>Sign in</a>
        </div>
      </header>

      <section className="hero">
        <h1>A clearer training picture, for coaches and athletes.</h1>
        <p className="hero-sub">Keep session notes and athlete check-ins together. A simple tool for your team, on one phone.</p>
        <div className="hero-cta">
          <a className="btn btn--primary btn--lg" href={SIGN_UP_URL}>Get started</a>
          <a className="btn btn--lg" href="#how">See how it works</a>
        </div>
        <p className="hero-stat">
          Built for grassroots teams that need a straightforward way to keep training records and check in with athletes.
        </p>
      </section>

      <section id="how" className="section">
        <h2>How it works</h2>
        <ol className="steps">
          <li><span className="steps__n">1</span><div><h3>Add your players</h3><p>Once, at the start of the season.</p></div></li>
          <li><span className="steps__n">2</span><div><h3>Log the session</h3><p>One duration for the squad, one effort score per player.</p></div></li>
          <li><span className="steps__n">3</span><div><h3>Review the picture</h3><p>See the recorded status and training history, then use it to guide a conversation.</p></div></li>
        </ol>
        <LiveDemo />
      </section>

      <section className="section split">
        <div className="card">
          <h3>Athlete?</h3>
          <p>Open the check-in link your coach sent you. No account or download needed.</p>
        </div>
        <div className="card card--flag">
          <h3>Honest limits</h3>
          <p>Thresholds are provisional and not yet validated against season outcomes. Treat a band as a prompt for a conversation, never a diagnosis.</p>
        </div>
      </section>

      <footer className="footer">
        <div className="footer__top">
          <span className="nav__wordmark">Sinopia</span>
          <a className="btn btn--primary" href={SIGN_UP_URL}>Get started</a>
        </div>
        <details className="sources-box">
          <summary>Sources</summary>
          <ol className="sources">
            {SOURCES.map((s, i) => (
              <li key={i}>
                {s.text}{" "}
                {s.url && <a href={s.url} target="_blank" rel="noreferrer">Link</a>}
              </li>
            ))}
          </ol>
        </details>
        <nav className="nav__links">
          <a href="/privacy">Privacy</a>
          <a href="/terms">Terms</a>
          <a href="/delete-account">Delete account</a>
        </nav>
        <div className="footer__bottom">
          <span>&copy; 2026 Sinopia</span>
          {CONTACT_EMAIL && <a href={"mailto:" + CONTACT_EMAIL}>{CONTACT_EMAIL}</a>}
        </div>
      </footer>
    </div>
  );
}
