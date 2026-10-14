type LegalPageKind = "privacy" | "terms" | "delete-account";

export function LegalPage({ kind }: { kind: LegalPageKind }) {
  const titles: Record<LegalPageKind, string> = {
    privacy: "Privacy notice",
    terms: "Terms of use",
    "delete-account": "Delete account and data",
  };

  return (
    <div className="landing">
      <header className="nav">
        <a className="nav__wordmark" href="/">Sinopia</a>
        <nav className="nav__links">
          <a href="/privacy">Privacy</a>
          <a href="/terms">Terms</a>
          <a href="/delete-account">Delete account</a>
        </nav>
      </header>
      <main className="section">
        <p className="demo-kicker">Draft for review before launch</p>
        <h1>{titles[kind]}</h1>
        <p><strong>Needs review by a qualified Nigerian privacy lawyer before public launch.</strong> Replace every operational placeholder and verify each statement against the deployed system. Last draft update: 14 October 2026.</p>

        {kind === "privacy" && (
          <>
            <h2>Who is responsible</h2>
            <p>Controller: the legal person or organisation operating Sinopia, to be confirmed before launch. Contact: publish a monitored privacy contact email before collecting real athlete information. Do not use this draft as a substitute for a completed controller identity and contact details.</p>

            <h2>Information processed</h2>
            <ul>
              <li>Coach account information returned by Google sign-in, including email address and display name.</li>
              <li>A team identifier and an athlete label or code, team category, and registration date.</li>
              <li>Training date, session duration, and perceived effort score.</li>
              <li>Daily self-reported sleep, energy, soreness, stress, pain response, and a selected pain-area category.</li>
              <li>Consent and coach declaration confirmations, session security data, and team exports.</li>
            </ul>
            <p>Do not enter athlete dates of birth, photographs, phone numbers, home addresses, precise location, or free-text medical histories. Use initials or a code instead of a full name where possible.</p>

            <h2>Why the information is used</h2>
            <p>Sinopia helps an authorised coach review training history and self-reported wellness, identify a prompt for a conversation, and export or delete team records. It is not a diagnosis or a validated individual injury prediction. The appropriate lawful basis for each use, including sensitive health-related information and information about children, must be confirmed before launch.</p>

            <h2>Children and consent</h2>
            <p>Coaches must be at least 18 and authorised by their school or club. Before registering any athlete under 18, the coach must obtain the required parent or guardian consent and provide the appropriate notice to the athlete. A checkbox records the coach's declaration; it does not independently verify age, authority, or consent.</p>

            <h2>Who may receive information</h2>
            <p>Authorised coaches for the owning team can access that team's roster, training history, and check-ins. Google processes sign-in information. If the optional explanation feature is enabled, Groq may receive a server-generated status level and generic reason text. Hosting and database providers depend on the deployment. Confirm the actual providers, processing purposes, contracts, and regions before launch. Intended deployment components may include Vercel, Render, and Neon if those services are used. The region for each provider is currently a deployment item to verify, not a confirmed fact.</p>

            <h2>Retention and security</h2>
            <p>The intended default retention period is 12 months, followed by deletion. Automated retention enforcement and inactivity warnings must be implemented and verified before this can be treated as an operating guarantee. The project is adding access controls, secure cookies, tokenised check-in links, and hard-deletion flows. Do not upload real athlete data until the remaining security work and deployment configuration have been reviewed.</p>

            <h2>Your choices and rights</h2>
            <p>Ask the coach or organisation that collected the information to access, correct, or delete it, or to explain how it is used. A coach can export the team's data. Account deletion is intended to permanently remove the coach's account and team records after a fresh Google sign-in. Rights and response deadlines will be handled under applicable law. You may also complain to the Nigeria Data Protection Commission (NDPC): <a href="https://ndpc.gov.ng/" target="_blank" rel="noreferrer">ndpc.gov.ng</a>.</p>

            <h2>International processing and incidents</h2>
            <p>Provider locations and any international transfers must be confirmed for the actual deployment and documented before launch. If a personal data breach occurs, the operator will assess and contain it, keep a record, and notify the NDPC and affected people within applicable legal deadlines, including 72 hours where required by law.</p>

            <h2>Contact and changes</h2>
            <p>Publish the controller's legal name and a monitored privacy contact before launch. This notice must be updated whenever data uses, providers, processing regions, retention settings, or user rights change.</p>
          </>
        )}

        {kind === "terms" && (
          <>
            <h2>Who may use Sinopia</h2>
            <p>Coach accounts are for people aged 18 or older who are authorised by a school or club to manage the team's data. You must provide accurate account information and protect your sign-in and check-in links.</p>

            <h2>Consent and responsibility</h2>
            <p>You are responsible for obtaining the required parent or guardian consent before recording information about an athlete under 18, explaining the check-in to athletes, limiting access to authorised people, and responding to requests about their data. Do not register athletes if you lack authority or consent.</p>

            <h2>Not medical advice</h2>
            <p>Sinopia is a workload-monitoring aid, not a medical device and not a diagnostic, treatment, or emergency service. Its thresholds and outputs are provisional and not fully validated. A status is a prompt for a qualified coach conversation, not a finding about injury or fitness. Seek qualified medical help for health concerns and do not use Sinopia to delay care.</p>

            <h2>Acceptable use</h2>
            <ul>
              <li>Use the service only for a team you are authorised to manage.</li>
              <li>Use athlete codes or initials where possible and do not upload unnecessary identifying or medical details.</li>
              <li>Do not share check-in links publicly or try to access another team's records.</li>
              <li>Do not use the output for scouting, selection discrimination, or decisions that require a medical assessment.</li>
            </ul>

            <h2>Availability, termination, and liability</h2>
            <p>The service may change or become unavailable while it is developed. Access may be suspended for misuse, lack of authority, or a security risk. Any limitation of liability and termination terms must be reviewed by counsel and cannot exclude rights or responsibilities that applicable law does not allow to be excluded.</p>

            <h2>Contact</h2>
            <p>The operator's legal identity and monitored contact address must be published before launch. These draft terms do not replace a signed school or club agreement where one is required.</p>
          </>
        )}

        {kind === "delete-account" && (
          <>
            <h2>Coach account deletion</h2>
            <p>Account deletion is intended to permanently delete the coach account, the team's athlete labels, training sessions, and check-in records. The action is irreversible. The in-app confirmation flow and fresh Google sign-in must be tested in the deployed environment before this page is treated as a working deletion service.</p>
            <p>Until that flow is available in the deployed app, contact the organisation operating Sinopia using the privacy contact published on the main site. The operator must verify your identity and process the request under applicable law. Do not send athlete health information in an email.</p>

            <h2>Athlete or parent requests</h2>
            <p>If you are an athlete or parent/guardian, contact the coach or school/club that collected the data to request access, correction, or deletion. If you cannot resolve the request with them, contact the operator's published privacy contact or the NDPC.</p>

            <h2>What deletion means</h2>
            <p>Hard deletion should remove the account and all records owned by that team from the active database. Backup expiry, legally required records, and any records held independently by a school or club must be explained before launch. The operator must verify the full deletion path and document any exceptions before making a complete-deletion promise.</p>
          </>
        )}
        <p><a className="btn" href="/">Back to Sinopia</a></p>
      </main>
      <footer className="footer">
        <nav className="nav__links">
          <a href="/privacy">Privacy</a>
          <a href="/terms">Terms</a>
          <a href="/delete-account">Delete account</a>
        </nav>
      </footer>
    </div>
  );
}
