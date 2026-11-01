import { useEffect, useState } from "react";
import { LiveDemo } from "./LiveDemo";
import { LegalPage } from "./LegalPage";

const COACH_APP_URL = (import.meta.env.VITE_COACH_APP_URL ?? (import.meta.env.PROD ? "" : "http://localhost:5173")).replace(/\/+$/, "");
const SIGN_IN_URL = `${COACH_APP_URL}/sign-in`;
const SIGN_UP_URL = `${COACH_APP_URL}/sign-up`;
const CONTACT_EMAIL = import.meta.env.VITE_CONTACT_EMAIL as string | undefined;

const SOURCES: { text: string; url: string | null }[] = [
  { text: "van Loggerenberg, C., Ramagole, D. A., Jansen van Rensburg, A., Janse van Rensburg, D. C., & Boer, P. (2025). Sports-related injuries and illnesses amongst adolescent athletes in an urban sports medicine practice setting. South African Journal of Sports Medicine, 37(1).", url: "https://scielo.org.za/scielo.php?script=sci_arttext&pid=S1015-51632025000100021" },
  { text: "Cowley, E. S., Olenick, A. A., McNulty, K. L., & Ross, E. Z. (2021). “Invisible Sportswomen”: The Sex Data Gap in Sport and Exercise Science Research. Women in Sport and Physical Activity Journal, 29(2), 146–151.", url: "https://journals.humankinetics.com/view/journals/wspaj/29/2/article-p146.xml" },
  { text: "Nigerian Journal of Human Movement, Wellness, Leisure, and Sports (2025). Grassroots football development in Nigeria: professional development rated low (weighted mean 1.77); 72.2% of respondents on the age-grade structure.", url: null },
  { text: "2024 Women’s Africa Cup of Nations (played July 2025, Morocco): Nigeria beat Morocco 3–2 in the final in Rabat, a record-extending tenth title.", url: "https://en.wikipedia.org/wiki/2024_Women%27s_Africa_Cup_of_Nations" },
  { text: "Foster, C., et al. (2001). A new approach to monitoring exercise training. Journal of Strength and Conditioning Research, 15(1), 109–114.", url: null },
  { text: "Gabbett, T. J. (2016). The training–injury prevention paradox: should athletes be training smarter and harder? British Journal of Sports Medicine, 50(5), 273–280.", url: "https://bjsm.bmj.com/content/50/5/273" },
  { text: "Impellizzeri, F. M., et al. (2020). Acute:Chronic Workload Ratio: conceptual issues and fundamental pitfalls. International Journal of Sports Physiology and Performance.", url: null },
];

function PitchMark() {
  return <svg className="pitch-mark" viewBox="0 0 360 250" fill="none" aria-hidden="true">
    <rect x="18" y="18" width="324" height="214" rx="5" />
    <path d="M180 18V232M18 125H342" />
    <circle cx="180" cy="125" r="38" />
    <rect x="18" y="73" width="50" height="104" /><rect x="292" y="73" width="50" height="104" />
    <rect x="18" y="96" width="22" height="58" /><rect x="320" y="96" width="22" height="58" />
    <circle cx="180" cy="125" r="2" fill="currentColor" />
  </svg>;
}

export default function App() {
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    try {
      const saved = window.localStorage.getItem("sinopia-theme");
      if (saved === "light" || saved === "dark") return saved;
    } catch { /* Use system preference if storage is unavailable. */ }
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { window.localStorage.setItem("sinopia-theme", theme); } catch { /* Theme still works for this visit. */ }
  }, [theme]);

  useEffect(() => {
    const targets = Array.from(document.querySelectorAll<HTMLElement>(".section-heading, .purpose__statement, .workflow-card, .demo, .impact__art, .impact__copy, .trust__items article"));
    if (!("IntersectionObserver" in window) || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    targets.forEach((target) => target.classList.add("reveal-ready"));
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    targets.forEach((target) => observer.observe(target));
    return () => observer.disconnect();
  }, []);

  if (window.location.pathname === "/privacy") return <LegalPage kind="privacy" />;
  if (window.location.pathname === "/terms") return <LegalPage kind="terms" />;
  if (window.location.pathname === "/delete-account") return <LegalPage kind="delete-account" />;

  return (
    <div className="landing">
      <header className="nav nav--sticky">
        <a className="brand" href="#" aria-label="Sinopia home"><span className="brand__mark">S</span><span>sinopia<span className="brand__period">.</span></span></a>
        <nav className="nav__actions" aria-label="Main navigation">
          <a className="nav__text-link" href="#how">How it works</a>
          <button type="button" className="btn theme-toggle" aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"} title={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"} aria-pressed={theme === "dark"} onClick={() => setTheme((current) => current === "dark" ? "light" : "dark")}>
            {theme === "light" ? <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2" /><path d="M12 2.5v2.4M12 19.1v2.4M4.6 4.6l1.7 1.7M17.7 17.7l1.7 1.7M2.5 12h2.4M19.1 12h2.4M4.6 19.4l1.7-1.7M17.7 6.3l1.7-1.7" /></svg> : <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11Z" /></svg>}
          </button>
          <a className="btn nav__cta" href={SIGN_IN_URL}>Sign in</a>
        </nav>
      </header>

      <main>
        <section className="hero">
          <div className="hero__copy">
            <p className="eyebrow enter enter--one"><span className="eyebrow__dot" /> For the people building the game</p>
            <h1 className="enter enter--two">Better records.<br /><em>More informed</em> coaching.</h1>
            <p className="hero-sub enter enter--three">A calmer way to keep training sessions, athlete check-ins and workload history in one place — built for grassroots sport.</p>
            <div className="hero-cta enter enter--four">
              <a className="btn btn--primary btn--lg" href={SIGN_UP_URL}>Get started</a>
              <a className="text-link" href="#how">See how it works</a>
            </div>
            <p className="hero-note enter enter--four">Made for real teams, on the devices they already have.</p>
          </div>
          <div className="hero__visual enter enter--three" aria-label="Illustrated football pitch at night">
            <div className="visual__halo" />
            <PitchMark />
            <div className="visual__ball" aria-hidden="true"><svg viewBox="0 0 48 48" fill="none"><circle cx="24" cy="24" r="21" /><path d="m24 13 8 6-3 10h-10l-3-10 8-6ZM24 13l-1-7M16 19 8 16M19 29l-5 8M29 29l6 8M32 19l8-3M14 37l-3 4M35 37l3 4" /></svg></div>
            <div className="visual__caption"><span>THE BIGGER PICTURE</span><span>One team. Better context.</span></div>
          </div>
          <div className="hero__bottom"><span>01 / RECORD WHAT MATTERS</span><span>BUILT FOR GRASSROOTS SPORT</span></div>
        </section>

        <section className="purpose section" aria-labelledby="purpose-title">
          <div className="section-heading"><p className="eyebrow">The point is the people</p><h2 id="purpose-title">Good coaching needs more than a good eye.</h2></div>
          <p className="purpose__statement">Grassroots coaches often work with limited time, tools and sports-science support. Sinopia helps bring the details they already collect into one clearer picture — so important conversations are easier to start and follow through.</p>
        </section>

        <section id="how" className="section workflow" aria-labelledby="how-title">
          <div className="section-heading"><p className="eyebrow">Simple by design</p><h2 id="how-title">From the session to the next conversation.</h2><p>Less scattered paperwork. More useful context.</p></div>
          <div className="workflow__grid">
            <article className="workflow-card"><span className="workflow-card__number">01</span><h3>Record</h3><p>Keep sessions, duration and perceived effort together with the athlete’s training history.</p></article>
            <article className="workflow-card"><span className="workflow-card__number">02</span><h3>Notice</h3><p>Bring recorded workload patterns and athlete check-ins into view, without pretending a flag is a diagnosis.</p></article>
            <article className="workflow-card"><span className="workflow-card__number">03</span><h3>Follow through</h3><p>Use the record as a starting point for a conversation, a closer look or a practical next step.</p></article>
          </div>
        </section>

        <section className="demo-section section" aria-labelledby="demo-title">
          <div className="section-heading"><p className="eyebrow">A look inside</p><h2 id="demo-title">A training picture, taking shape.</h2><p>Try a small, fictional workload example. No real athlete data is used.</p></div>
          <LiveDemo />
        </section>

        <section className="impact section" aria-labelledby="impact-title">
          <div className="impact__art" aria-hidden="true"><PitchMark /><span className="impact__orbit impact__orbit--one" /><span className="impact__orbit impact__orbit--two" /></div>
          <div className="impact__copy"><p className="eyebrow">Why this matters</p><h2 id="impact-title">Sports insight shouldn’t start with expensive infrastructure.</h2><p>For a community team, better support can begin with a reliable record, a simple check-in and a coach who has time to listen. Sinopia is being built to make that everyday process easier to sustain.</p><a className="text-link" href="#limits">What Sinopia can — and can’t — tell you</a></div>
        </section>

        <section id="limits" className="trust section" aria-labelledby="limits-title">
          <div><p className="eyebrow">Built with care</p><h2 id="limits-title">Useful context. Honest limits.</h2></div>
          <div className="trust__items">
            <article><span>01</span><div><h3>Designed for everyday teams</h3><p>Keep the workflow practical for coaches who may not have dedicated sports-science staff.</p></div></article>
            <article><span>02</span><div><h3>A flag is a prompt, not a verdict</h3><p>Current workload thresholds are provisional and not validated against season outcomes. They do not diagnose injuries or predict an individual athlete’s future.</p></div></article>
            <article><span>03</span><div><h3>Athletes deserve to be heard</h3><p>Check-ins should support a respectful conversation and appropriate follow-up — not replace an athlete’s voice or qualified care.</p></div></article>
          </div>
        </section>
      </main>

      <footer className="footer">
        <div className="footer__top"><a className="brand" href="#" aria-label="Sinopia home"><span className="brand__mark">S</span><span>sinopia<span className="brand__period">.</span></span></a><div><p>Better records. More informed coaching.</p><a className="btn btn--primary" href={SIGN_UP_URL}>Get started</a></div></div>
        <details className="sources-box"><summary>Research and references</summary><ol className="sources">{SOURCES.map((s, i) => <li key={i}>{s.text}{" "}{s.url && <a href={s.url} target="_blank" rel="noreferrer">Read source</a>}</li>)}</ol></details>
        <nav className="nav__links" aria-label="Legal"><a href="/privacy">Privacy</a><a href="/terms">Terms</a><a href="/delete-account">Delete account</a></nav>
        <div className="footer__bottom"><span>© 2026 Sinopia</span>{CONTACT_EMAIL && <a href={"mailto:" + CONTACT_EMAIL}>{CONTACT_EMAIL}</a>}<span>Built for the long game.</span></div>
      </footer>
      <button
        type="button"
        className="back-to-top-ball"
        aria-label="Back to top"
        title="Back to top"
        onClick={() => window.scrollTo({ top: 0, behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" })}
      >
        <svg viewBox="0 0 64 64" aria-hidden="true">
          <defs>
            <radialGradient id="sinopia-ball-shade" cx="28%" cy="22%" r="78%">
              <stop offset="0%" stopColor="#fff5e7" />
              <stop offset="48%" stopColor="#e8c6a6" />
              <stop offset="82%" stopColor="#b98563" />
              <stop offset="100%" stopColor="#754832" />
            </radialGradient>
          </defs>
          <circle cx="32" cy="32" r="28" fill="url(#sinopia-ball-shade)" stroke="#f9dfc7" strokeWidth="1.5" />
          <path d="m32 20 10 7-4 12H26l-4-12 10-7Zm0 0-1-9M22 27 12 24M26 39l-6 10M38 39l6 10M42 27l10-3" fill="none" stroke="#70452f" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
          <path d="M13 16A27 27 0 0 1 49 12" fill="none" stroke="#fffaf1" strokeWidth="2" strokeLinecap="round" opacity=".7" />
        </svg>
      </button>
    </div>
  );
}
