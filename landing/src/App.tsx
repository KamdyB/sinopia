// landing/src/App.tsx  — LANDING PAGE (imports LiveDemo, nothing from the coach tool)
import { LiveDemo } from "./LiveDemo";
import { LegalPage } from "./LegalPage";

// Dev: the coach tool runs on 5173. In production, deploy the landing page at
// "/" and the coach tool under "/app/", then set this to "/app/".
const COACH_APP_URL = import.meta.env.VITE_COACH_APP_URL ?? "http://localhost:5173";
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
  if (window.location.pathname === "/privacy") return <LegalPage kind="privacy" />;
  if (window.location.pathname === "/terms") return <LegalPage kind="terms" />;
  if (window.location.pathname === "/delete-account") return <LegalPage kind="delete-account" />;

  return (
    <div className="landing">
      <header className="nav">
        <span className="nav__wordmark">Sinopia</span>
        <nav className="nav__links">
          <a href="#how">How it works</a>
          <a href="#evidence">The evidence</a>
          <a href="#honesty">What is and isn\u2019t validated</a>
        </nav>
        <a className="btn btn--primary nav__cta" href={COACH_APP_URL}>Open the coach tool</a>
      </header>

      <section className="hero">
        <h1>Workload tracking was built mostly on male athletes. Your team deserved better numbers.</h1>
        <div className="hero-stat">
          <span className="hero-stat__number">&asymp;23 million</span>
          <span className="hero-stat__text">
            estimated sports-related injuries among African adolescents every year,
            with limited injury data across the continent to guide the coaches training them.
          </span>
          <span className="hero-stat__source">Estimate as cited in van Loggerenberg et al., 2025, South African Journal of Sports Medicine.</span>
        </div>
        <p className="hero-sub">
          Sinopia gives a coach of a girls\u2019, boys\u2019, or mixed youth team the same
          load-monitoring math sports scientists use \u2014 duration \u00d7 effort, rolling
          workload ratios, plain language \u2014 on one phone, for zero budget.
        </p>
        <div className="hero-cta">
          <a className="btn btn--primary btn--lg" href={COACH_APP_URL}>Open the coach tool</a>
          <a className="btn btn--lg" href="#how">See it work</a>
        </div>
      </section>

      <section id="how" className="section">
        <h2>How it works</h2>
        <ol className="steps">
          <li><strong>Register each player once.</strong> One name per team, at the start of the season. Two players named Amaka on different teams are always separate histories.</li>
          <li><strong>Set session length once.</strong> The whole squad trains together, so duration is entered one time for the sitting.</li>
          <li><strong>Tap effort per player.</strong> RPE 0\u201310 as the session ends. Enter submits and moves to the next player, no mouse needed.</li>
          <li><strong>Read the result.</strong> Each player gets a workload ratio, a plain-language band, and a history chart that shows the trend over time.</li>
        </ol>
        <LiveDemo />
        <p className="section-note">
          In the coach tool, this chart lives on each player\u2019s page: open the team directory and click a name.
        </p>
      </section>

      <section id="evidence" className="section section--tinted">
        <h2>The gap, in three numbers</h2>
        <div className="facts">
          <article className="fact">
            <span className="fact__number">6% vs 31%</span>
            <p>
              Across 5,261 papers in six leading sports-science journals (2014\u20132020),
              only 6% of studies included female participants only, while 31% included
              males only. Of 12.5 million participants where sex was reported, 66% were male.
              The load-monitoring thresholds used everywhere were mostly built on that base.
            </p>
            <span className="fact__source">Cowley et al., 2021</span>
          </article>
          <article className="fact">
            <span className="fact__number">72.2%</span>
            <p>
              In a 2025 study of Nigerian grassroots football, 72.2% of respondents said the
              country\u2019s age-grade development structure (U-15 to U-23) is not encouraging
              professional development; development overall was rated low, at a weighted mean
              of 1.77 on the study\u2019s scale.
            </p>
            <span className="fact__source">Nigerian Journal of Human Movement, Wellness, Leisure, and Sports, 2025</span>
          </article>
          <article className="fact">
            <span className="fact__number">10</span>
            <p>
              Women\u2019s Africa Cup of Nations titles for Nigeria \u2014 the most in the
              tournament\u2019s history, the latest won in Rabat in July 2025. The talent is
              already there. What\u2019s missing is the everyday infrastructure around it.
            </p>
            <span className="fact__source">2024 WAFCON, played July 2025</span>
          </article>
        </div>
      </section>

      <section id="honesty" className="section">
        <h2>What is and isn\u2019t validated \u2014 stated up front</h2>
        <div className="honesty">
          <div className="honesty__col">
            <h3>Established science</h3>
            <p>
              Sinopia\u2019s core math is the session-RPE method (duration \u00d7 effort,
              Foster et al., 2001) and the acute:chronic workload ratio, with 0.8\u20131.3 as
              the commonly cited optimal range (Gabbett, 2016). Published critiques of the
              ratio exist (e.g., Impellizzeri et al., 2020), so Sinopia treats it as a
              screening prompt for a conversation \u2014 never a diagnosis.
            </p>
          </div>
          <div className="honesty__col honesty__col--flag">
            <h3>Not validated yet, and we say so</h3>
            <p>
              Current workload thresholds are provisional and have not been validated
              against season outcomes. The app does not currently assess menstrual-cycle
              or growth-rate context. Do not treat a band as a prediction or medical finding.
            </p>
          </div>
        </div>
      </section>

      <section className="section section--tinted">
        <h2>Who it\u2019s for</h2>
        <p className="who">
          Coaches of under-resourced youth teams \u2014 girls\u2019, boys\u2019, or mixed \u2014
          with no budget for wearables or sports-science staff. One coach, one phone, one season.
        </p>
        <p className="who who--promise">
          Team records are intended to be accessible only to the authorised coach for that team.
          Hosting and sign-in providers may process some information as described in the privacy notice.
          Use initials or codes where possible. Sinopia does not currently provide a scout-facing
          view or a talent-evaluation feed.
        </p>
      </section>

      <footer className="footer">
        <div className="footer__top">
          <span className="nav__wordmark">Sinopia</span>
          <a className="btn btn--primary" href={COACH_APP_URL}>Open the coach tool</a>
        </div>
        <ol className="sources">
          {SOURCES.map((s, i) => (
            <li key={i}>
              {s.text}{" "}
              {s.url && <a href={s.url} target="_blank" rel="noreferrer">Source</a>}
            </li>
          ))}
        </ol>
        {/* TODO before ship: replace CONTACT_EMAIL with the real contact inbox. */}
        <div className="footer__bottom">
          <span>&copy; 2026 Sinopia. All rights reserved.</span>
          <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
        </div>
      </footer>
    </div>
  );
}
