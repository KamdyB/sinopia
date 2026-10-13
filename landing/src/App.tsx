// landing/src/App.tsx
// Minimal landing page plus About page. Basic CSS, basic hash routing,
// no router dependency. Branding is gender neutral by design: this pitch
// is for any school or youth coach, of any team.
import { useEffect, useState } from "react";
import { LiveDemo } from "./LiveDemo";

// In production set VITE_COACH_APP_URL to the coach tool's URL. The
// ?demo=1 suffix drops visitors straight into the no-login demo mode.
const COACH_APP_URL = import.meta.env.VITE_COACH_APP_URL || "http://localhost:5173";
const DEMO_URL = `${COACH_APP_URL}/?demo=1`;

// Contact placeholder. Replace with the real inbox before shipping.
const CONTACT_EMAIL = "coach@sinopia.example";

// PLACEHOLDER: paste the refined problem statement here, exactly as
// approved, and the page renders it under the heading below. The two
// sentences under it come from the project's own framing and invent no
// names and no numbers.
const PROBLEM_STATEMENT =
  "School and youth sports teams in low-resource settings often train " +
  "without any structured way to see how hard their athletes are working. " +
  "Load-monitoring tools that exist today assume staff, budgets and " +
  "wearables those teams do not have.";

const SOURCES: { text: string; url: string | null }[] = [
  {
    text: "Foster, C., et al. (2001). A new approach to monitoring exercise training. Journal of Strength and Conditioning Research, 15(1).",
    url: null,
  },
  {
    text: "Gabbett, T. J. (2016). The training-injury prevention paradox: should athletes be training smarter and harder? British Journal of Sports Medicine, 50(5).",
    url: "https://bjsm.bmj.com/content/50/5/273",
  },
  {
    text: "Impellizzeri, F. M., et al. (2020). Acute:Chronic Workload Ratio: conceptual issues and fundamental pitfalls. International Journal of Sports Physiology and Performance.",
    url: null,
  },
  {
    text: "Cowley, E. S., Olenick, A. A., McNulty, K. L., & Ross, E. Z. (2021). \u201cInvisible Sportswomen\u201d: The Sex Data Gap in Sport and Exercise Science Research. Women in Sport and Physical Activity Journal, 29(2).",
    url: "https://journals.humankinetics.com/view/journals/wspaj/29/2/article-p146.xml",
  },
  {
    text: "van Loggerenberg, C., Ramagole, D. A., Jansen van Rensburg, A., Janse van Rensburg, D. C., & Boer, P. (2025). Sports-related injuries and illnesses amongst adolescent athletes in an urban sports medicine practice setting. South African Journal of Sports Medicine, 37(1).",
    url: "https://scielo.org.za/scielo.php?script=sci_arttext&pid=S1015-51632025000100021",
  },
];

function useHashPage(): "home" | "about" {
  return typeof window !== "undefined" && window.location.hash === "#/about"
    ? "about"
    : "home";
}

function TryDemoButtons() {
  return (
    <div className="cta-row">
      <a className="btn btn--primary btn--lg" href={DEMO_URL}>Try the demo</a>
      <a className="btn btn--lg" href={COACH_APP_URL}>Sign in and open the coach tool</a>
    </div>
  );
}

function WhatItDoesRows({ about = false }: { about?: boolean }) {
  return (
    <div className="does-rows">
      <div className="does-col">
        <h3>What Sinopia does</h3>
        <ul>
          <li>Turns minutes and effort into one load number per session.</li>
          <li>Compares this week against an athlete's own recent history, and nobody else's.</li>
          <li>Colours one status per athlete: ok, watch, act or refer, with the reason.</li>
          <li>Collects a four question daily check-in, including any pain and where it hurts.</li>
          <li>Runs on one phone, with no wearables, and no budget.</li>
        </ul>
      </div>
      <div className="does-col does-col--no">
        <h3>What Sinopia does not do</h3>
        <ul>
          <li>It does not diagnose anything. It is a screening prompt for a coach conversation.</li>
          <li>It does not rank athletes against each other, ever.</li>
          <li>It does not store athlete names. Athletes are opaque codes.</li>
          <li>It does not share or export team data to anyone.</li>
          <li>It does not flag anything before an athlete has their own history to compare with.</li>
        </ul>
      </div>
      {about && (
        <p className="about-note">
          Every threshold lives in one labelled configuration file, every
          number in it is provisional, and the tool says so in its own
          interface. Statuses open a conversation. They never close one.
        </p>
      )}
    </div>
  );
}

function Sources() {
  return (
    <ol className="sources">
      {SOURCES.map((s, i) => (
        <li key={i}>
          {s.text}{" "}
          {s.url && <a href={s.url} target="_blank" rel="noreferrer">Source</a>}
        </li>
      ))}
    </ol>
  );
}

function Home() {
  return (
    <div className="landing">
      <header className="nav">
        <span className="nav__wordmark">Sinopia</span>
        <nav className="nav__links">
          <a href="#how">How it works</a>
          <a href="#privacy">Privacy</a>
          <a href="#/about">About</a>
        </nav>
        <a className="btn btn--primary nav__cta" href={DEMO_URL}>Try the demo</a>
      </header>

      <section className="hero">
        <h1>Training-load awareness for any school or youth coach, on one phone.</h1>
        <p className="hero-sub">
          Sinopia computes the same session-RPE load math sports scientists
          use, compares each athlete only with their own recent history, and
          answers with one plain-language status per athlete. No wearables,
          no staff, no budget.
        </p>
        <TryDemoButtons />
      </section>

      <section id="problem" className="section">
        <h2>The problem</h2>
        <p className="statement">{PROBLEM_STATEMENT}</p>
      </section>

      <section id="does" className="section section--tinted">
        <h2>What Sinopia does and does not do</h2>
        <WhatItDoesRows />
      </section>

      <section id="how" className="section">
        <h2>How it works</h2>
        <ol className="steps">
          <li><strong>Register each athlete once.</strong> An athlete code is all the tool stores, so the roster never holds names.</li>
          <li><strong>Sign in with Google.</strong> One coach account owns one team, and every query is scoped to that team.</li>
          <li><strong>Log each session.</strong> Duration once for the squad, effort per athlete as the session ends.</li>
          <li><strong>Read the dashboard.</strong> Each athlete gets a workload ratio, a status, and a history chart.</li>
        </ol>
        <LiveDemo />
      </section>

      <section id="privacy" className="section section--tinted">
        <h2>Privacy</h2>
        <p className="privacy">
          Athletes are codes, never names, so the data about minors stays
          minimal and non-identifying. Team data is visible only to the
          signed-in coach who owns that team; a second coach's account
          cannot reach another team's athletes, sessions or check-ins.
          Athlete check-ins arrive through a shared link and never require
          an account. There is no export, no third-party sharing, and no
          scout-facing view.
        </p>
      </section>

      <section id="care" className="section">
        <h2>Care, honestly framed</h2>
        <p className="care">
          Not a medical tool. Sinopia raises a flag for a conversation with
          the athlete, and points to a physiotherapist or doctor when pain
          is reported. It never diagnoses and never overrides a coach's or
          a clinician's judgement.
        </p>
        <TryDemoButtons />
      </section>

      <footer className="footer">
        <div className="footer__top">
          <span className="nav__wordmark">Sinopia</span>
          <a className="btn btn--primary" href={DEMO_URL}>Try the demo</a>
        </div>
        <div className="footer__bottom">
          <span>&copy; 2026 Sinopia. All rights reserved.</span>
          <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
        </div>
      </footer>
    </div>
  );
}

function About() {
  return (
    <div className="landing">
      <header className="nav">
        <span className="nav__wordmark">Sinopia</span>
        <nav className="nav__links">
          <a href="#/">Home</a>
          <a href="#/about">About</a>
        </nav>
        <a className="btn btn--primary nav__cta" href={DEMO_URL}>Try the demo</a>
      </header>

      <section className="hero">
        <h1>About Sinopia</h1>
        <p className="hero-sub">
          Sinopia exists so a coach of any school or youth team, of any
          sport, in a low-resource setting, can see workload stress early,
          from a phone they already own.
        </p>
      </section>

      <section className="section">
        <h2>How Sinopia treats the science</h2>
        <div className="honesty">
          <div className="honesty__col">
            <h3>Established science</h3>
            <p>
              The core math is the session-RPE method, minutes times effort,
              with rolling workload comparisons between an athlete and their
              own recent weeks. See Foster et al., 2001 in the sources below.
            </p>
          </div>
          <div className="honesty__col honesty__col--flag">
            <h3>Not validated yet, and we say so</h3>
            <p>
              Every threshold in the rules engine is provisional and labelled
              that way in the open configuration file. Published critiques of
              workload ratios exist. No number on this page or in the tool is
              invented, and no status is ever a diagnosis.
            </p>
          </div>
        </div>
      </section>

      <section className="section section--tinted">
        <h2>What Sinopia does and does not do</h2>
        <WhatItDoesRows about />
      </section>

      <section className="section">
        <h2>Privacy and care</h2>
        <p className="privacy">
          Athletes are stored as opaque codes only. Team data stays within
          the signed-in coach's team, and nobody outside it, including us,
          can see it. Not a medical tool: statuses open a conversation,
          pain always points to a qualified professional, and nothing here
          replaces one.
        </p>
      </section>

      <section className="section">
        <h2>Sources</h2>
        <Sources />
      </section>

      <footer className="footer">
        <div className="footer__top">
          <span className="nav__wordmark">Sinopia</span>
          <a className="btn btn--primary" href={DEMO_URL}>Try the demo</a>
        </div>
        <div className="footer__bottom">
          <span>&copy; 2026 Sinopia. All rights reserved.</span>
          <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  const [page, setPage] = useState<"home" | "about">(useHashPage());

  useEffect(() => {
    const route = () => setPage(useHashPage());
    window.addEventListener("hashchange", route);
    return () => window.removeEventListener("hashchange", route);
  }, []);

  return page === "about" ? <About /> : <Home />;
}
