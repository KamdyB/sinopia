import { InstallButton } from "./InstallButton";
import { ReactNode, useEffect, useRef, useState } from "react";
import { TurnstileWidget } from "./TurnstileWidget";
import {
  acceptCoachPolicies,
  CoachSession,
  deleteCoachAccount,
  fetchCoachSession,
  signInWithGoogle,
  signOut,
  setupCoachTeam,
  requestEmailSignup,
  verifyEmailSignup,
} from "./api";

type GoogleCredentialResponse = { credential: string };
type GoogleIdentity = {
  initialize: (options: {
    client_id: string;
    callback: (response: GoogleCredentialResponse) => void;
  }) => void;
  renderButton: (parent: HTMLElement, options: { theme: string; size: string }) => void;
};
declare global {
  interface Window {
    google?: { accounts: { id: GoogleIdentity } };
  }
}

const GOOGLE_SCRIPT_ID = "sinopia-google-identity";

export function AuthGate({ children }: { children: ReactNode }) {
  const buttonRef = useRef<HTMLDivElement>(null);
  const [coach, setCoach] = useState<CoachSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [ageConfirmed, setAgeConfirmed] = useState(false);
  const [consentConfirmed, setConsentConfirmed] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [teamName, setTeamName] = useState("");
  const [teamType, setTeamType] = useState<"girls" | "boys" | "mixed">("girls");
  const [error, setError] = useState<string | null>(null);
  const [emailMode, setEmailMode] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [emailFullName, setEmailFullName] = useState("");
  const [emailAddress, setEmailAddress] = useState("");
  const [deletionMode, setDeletionMode] = useState(false);
  const [deleted, setDeleted] = useState(false);
  const turnstileTokenRef = useRef<string | null>(null);
  const [turnstileVersion, setTurnstileVersion] = useState(0);
  const path = window.location.pathname;
  const isSignUp = path === "/sign-up";
  const expiredSession = new URLSearchParams(window.location.search).get("expired") === "1";

  const refreshSession = async () => {
    const current = await fetchCoachSession();
    setCoach(current);
    return current;
  };

  useEffect(() => {
    if (window.location.pathname === "/verify-email") {
      setLoading(false);
      return;
    }
    let cancelled = false;
    fetchCoachSession()
      .then((current) => { if (!cancelled) setCoach(current); })
      .catch((err) => {
        if (!cancelled) {
          setCoach(null);
          if (err instanceof Error && err.message.toLowerCase().includes("session expired")) {
            window.location.replace("/sign-in?expired=1");
          }
        }
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (path !== "/verify-email") return;
    const token = new URLSearchParams(window.location.search).get("token");
    if (!token) {
      setError("That verification link is incomplete. Start sign-up again.");
      return;
    }
    let cancelled = false;
    setLoading(true);
    verifyEmailSignup(token)
      .then((current) => {
        if (!cancelled) {
          setCoach(current);
          window.history.replaceState({}, "", "/verify-email");
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Email verification failed. Request a new link.");
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [path]);

  useEffect(() => {
    if (loading) return;
    if (!coach) {
      if (path === "/" || path === "/onboarding" || path.startsWith("/app")) {
        window.location.replace("/sign-in");
      }
      return;
    }
    if (coach.needs_policy_acceptance) return;
    if (coach.needs_onboarding) {
      if (path !== "/onboarding") window.location.replace("/onboarding");
      return;
    }
    if (path === "/" || path === "/sign-in" || path === "/sign-up" || path === "/onboarding") {
      window.location.replace("/app");
    }
  }, [loading, coach, path]);

  useEffect(() => {
    if (loading || coach || emailMode || !buttonRef.current) return;
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined;
    if (!clientId) {
      setError("Google sign-in is not configured. Set VITE_GOOGLE_CLIENT_ID for this deployment.");
      return;
    }
    let cancelled = false;
    const renderGoogleButton = () => {
      if (cancelled || !buttonRef.current || !window.google) return;
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async (credentialResponse) => {
          if (isSignUp && (!ageConfirmed || !consentConfirmed || !termsAccepted)) {
            setError("Confirm both declarations and accept the Terms and Privacy notice before continuing.");
            return;
          }
          setBusy(true);
          setError(null);
          try {
            const token = turnstileTokenRef.current;
            if (import.meta.env.PROD && !token) throw new Error("Complete the bot-protection check first.");
            const signedIn = await signInWithGoogle(credentialResponse.credential, token ?? undefined, isSignUp ? "signup" : "signin");
            if (isSignUp) {
              await acceptCoachPolicies(ageConfirmed, consentConfirmed, termsAccepted);
              const current = await refreshSession();
              window.location.replace(current.needs_onboarding ? "/onboarding" : "/app");
            } else {
              setCoach(signedIn);
              if (!signedIn.needs_policy_acceptance) {
                window.location.replace(signedIn.needs_onboarding ? "/onboarding" : "/app");
              }
            }
          } catch (err) {
            setError(err instanceof Error ? err.message : "Google sign-in failed.");
          } finally {
            turnstileTokenRef.current = null;
            setTurnstileVersion((version) => version + 1);
            setBusy(false);
          }
        },
      });
      buttonRef.current.replaceChildren();
      window.google.accounts.id.renderButton(buttonRef.current, { theme: "outline", size: "large" });
    };
    const existingScript = document.getElementById(GOOGLE_SCRIPT_ID) as HTMLScriptElement | null;
    if (window.google) renderGoogleButton();
    else if (existingScript) existingScript.addEventListener("load", renderGoogleButton, { once: true });
    else {
      const script = document.createElement("script");
      script.id = GOOGLE_SCRIPT_ID;
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.onload = renderGoogleButton;
      script.onerror = () => setError("Could not load Google sign-in. Check your connection and try again.");
      document.head.appendChild(script);
    }
    return () => { cancelled = true; };
  }, [loading, coach, isSignUp, ageConfirmed, consentConfirmed, termsAccepted, emailMode]);

  const handleEmailSignup = async () => {
    if (!emailFullName.trim() || !emailAddress.trim()) {
      setError("Enter your full name and email address.");
      return;
    }
    if (!ageConfirmed || !consentConfirmed || !termsAccepted) {
      setError("Confirm both declarations and accept the Terms and Privacy notice before continuing.");
      return;
    }
    const token = turnstileTokenRef.current;
    if (import.meta.env.PROD && !token) {
      setError("Complete the bot-protection check first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await requestEmailSignup({
        full_name: emailFullName.trim(),
        email: emailAddress.trim(),
        turnstile_token: token ?? "",
        age_18_or_older: ageConfirmed,
        authorised_and_parental_consent_obtained: consentConfirmed,
        accept_terms_and_privacy: termsAccepted,
      });
      setEmailSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send the verification email.");
    } finally {
      turnstileTokenRef.current = null;
      setTurnstileVersion((version) => version + 1);
      setBusy(false);
    }
  };

  const handleAccept = async () => {
    setBusy(true);
    setError(null);
    try {
      await acceptCoachPolicies(ageConfirmed, consentConfirmed, termsAccepted);
      const current = await refreshSession();
      if (current.needs_onboarding) window.location.replace("/onboarding");
      else window.location.replace("/app");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the declarations.");
    } finally {
      setBusy(false);
    }
  };

  const handleCreateTeam = async () => {
    if (!teamName.trim()) { setError("Enter a team name."); return; }
    setBusy(true);
    setError(null);
    try {
      await setupCoachTeam(teamName.trim(), teamType);
      const current = await refreshSession();
      if (!current.needs_onboarding) window.location.replace("/app");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save your team.");
    } finally {
      setBusy(false);
    }
  };

  const handleDeleteAccount = async (credential: string, turnstileToken?: string) => {
    setBusy(true);
    setError(null);
    try {
      await deleteCoachAccount(credential, turnstileToken);
      setDeleted(true);
      setCoach(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Could not delete the account.";
      setError(message);
      throw err;
    } finally {
      setBusy(false);
    }
  };

  const handleSignOut = async () => {
    setBusy(true);
    try {
      await signOut();
      setCoach(null);
      setAgeConfirmed(false);
      setConsentConfirmed(false);
      window.location.assign("/sign-in");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign out.");
    } finally {
      setBusy(false);
    }
  };

  if (deleted) return <div className="page"><div className="panel"><h1>Account deleted</h1><p>Your coach account and team data have been deleted from the active database.</p></div></div>;
  if (loading) return <div className="page"><p>Checking your session…</p></div>;

  if (path === "/verify-email" && !coach && loading) {
    return <div className="page"><div className="panel"><p role="status">Verifying your email and creating your account…</p></div></div>;
  }

  if (!coach) {
    return (
      <div className="page"><div className="panel auth-panel">
        <a className="auth-wordmark" href={import.meta.env.VITE_LEGAL_BASE_URL || "/"}>Sinopia</a>
        <p className="auth-caption">A clearer picture, one session at a time.</p>
        <p className="eyebrow">COACH SPACE</p>
        <InstallButton />
        <h1 className="display-title">{isSignUp ? "Create your coach account" : "Coach sign-in"}</h1>
        <p>{isSignUp ? "Create an account with Google or verify your email address." : "Sign in with Google to access your team's training and check-in records."}</p>
        {expiredSession && <p role="status">Your session expired. Sign in again to continue.</p>}
        {isSignUp && <>
          <label className="consent-confirmation"><input type="checkbox" checked={ageConfirmed} onChange={(event) => setAgeConfirmed(event.target.checked)} /> I am 18 years old or older.</label>
          <label className="consent-confirmation"><input type="checkbox" checked={consentConfirmed} onChange={(event) => setConsentConfirmed(event.target.checked)} /> I am authorised by my school or club to manage this team's data, and I have obtained parent or guardian consent for every athlete under 18.</label>
          <label className="consent-confirmation"><input type="checkbox" checked={termsAccepted} onChange={(event) => setTermsAccepted(event.target.checked)} /> I have read and accept the <a href="/terms" target="_blank" rel="noreferrer">Terms</a> and <a href="/privacy" target="_blank" rel="noreferrer">Privacy notice</a>.</label>
        </>}
        <TurnstileWidget key={turnstileVersion} action="login" onToken={(token) => { turnstileTokenRef.current = token; }} />
        {isSignUp && emailMode ? (
          emailSent ? (
            <div role="status">
              <h2>Check your inbox</h2>
              <p>If the email was sent, use the verification link within 15 minutes to finish creating your account.</p>
              <button type="button" className="copy-link" onClick={() => { setEmailSent(false); setError(null); }}>Try another email</button>
            </div>
          ) : (
            <div className="email-signup">
              <label className="field-group__label" htmlFor="coach-full-name">Full name</label>
              <input id="coach-full-name" autoComplete="name" value={emailFullName} maxLength={120} onChange={(event) => setEmailFullName(event.target.value)} placeholder="Your full name" />
              <label className="field-group__label" htmlFor="coach-email">Email address</label>
              <input id="coach-email" type="email" autoComplete="email" value={emailAddress} maxLength={320} onChange={(event) => setEmailAddress(event.target.value)} placeholder="you@example.com" />
              <button type="button" className="record-btn" disabled={busy || !emailFullName.trim() || !emailAddress.trim()} onClick={() => void handleEmailSignup()}>{busy ? "Sending verification…" : "Send verification email"}</button>
              <button type="button" className="copy-link" disabled={busy} onClick={() => { setEmailMode(false); setError(null); }}>Use Google instead</button>
            </div>
          )
        ) : (
          <>
            <div ref={buttonRef} />
            {isSignUp && <button type="button" className="copy-link" disabled={busy} onClick={() => { setEmailMode(true); setError(null); }}>Sign up with full name and email instead</button>}
          </>
        )}
        {busy && <p role="status">{emailMode ? "Sending…" : "Signing in…"}</p>}
        {error && <p className="form-error" role="alert">{error}</p>}
        <p><a href={isSignUp ? "/sign-in" : "/sign-up"}>{isSignUp ? "Already have an account? Sign in" : "New to Sinopia? Get started"}</a></p>
      </div></div>
    );
  }

  if (coach.needs_policy_acceptance) {
    return (
      <div className="page"><div className="panel">
        <p className="eyebrow">Sinopia by KamdyB</p><h1 className="display-title">Before you continue</h1>
        <p>Sinopia stores athlete training and wellness check-in information. You must make both declarations and accept the current terms before accessing the dashboard.</p>
        <label className="consent-confirmation"><input type="checkbox" checked={ageConfirmed} onChange={(event) => setAgeConfirmed(event.target.checked)} /> I am 18 years old or older.</label>
        <label className="consent-confirmation"><input type="checkbox" checked={consentConfirmed} onChange={(event) => setConsentConfirmed(event.target.checked)} /> I am authorised by my school or club to record this team's data, and I have obtained parent or guardian consent for every athlete under 18.</label>
        <label className="consent-confirmation"><input type="checkbox" checked={termsAccepted} onChange={(event) => setTermsAccepted(event.target.checked)} /> I have read and accept the <a href="/terms" target="_blank" rel="noreferrer">Terms</a> and <a href="/privacy" target="_blank" rel="noreferrer">Privacy notice</a>.</label>
        <p>These are declarations, not independent age verification. Only continue if both statements are true.</p>
        <button className="record-btn" disabled={!ageConfirmed || !consentConfirmed || !termsAccepted || busy} onClick={handleAccept}>{busy ? "Saving…" : "Accept and continue"}</button>
        <button className="copy-link" disabled={busy} onClick={handleSignOut}>Sign out</button>
        {error && <p className="form-error">{error}</p>}
      </div></div>
    );
  }

  if (coach.needs_onboarding) {
    return (
      <div className="page"><div className="panel">
        <p className="eyebrow">Sinopia by KamdyB</p><h1 className="display-title">Set up your team</h1>
        <p>Choose your team composition once. Sinopia uses it for registration and roster labels.</p>
        <label className="field-group__label" htmlFor="team-name">Team name</label>
        <input id="team-name" value={teamName} maxLength={120} onChange={(event) => setTeamName(event.target.value)} placeholder="e.g. U17 Football" />
        <fieldset className="consent-confirmation"><legend>Team composition</legend>
          <label><input type="radio" name="team-type" checked={teamType === "girls"} onChange={() => setTeamType("girls")} /> Girls</label>
          <label><input type="radio" name="team-type" checked={teamType === "boys"} onChange={() => setTeamType("boys")} /> Boys</label>
          <label><input type="radio" name="team-type" checked={teamType === "mixed"} onChange={() => setTeamType("mixed")} /> Mixed</label>
        </fieldset>
        <button className="record-btn" disabled={busy || !teamName.trim()} onClick={handleCreateTeam}>{busy ? "Saving…" : "Create team"}</button>
        <button className="copy-link" disabled={busy} onClick={handleSignOut}>Sign out</button>
        {error && <p className="form-error">{error}</p>}
      </div></div>
    );
  }

  return (
    <div>
      <div className="auth-toolbar">
        <span>{coach.display_name}</span>
        <button type="button" className="copy-link" disabled={busy} onClick={handleSignOut}>Sign out</button>
        <button type="button" className="copy-link" disabled={busy} onClick={() => setDeletionMode(true)}>Delete account and team data</button>
      </div>
      {deletionMode ? <DeleteAccountConfirmation onCancel={() => setDeletionMode(false)} onDelete={handleDeleteAccount} /> : children}
      {error && <p className="form-error">{error}</p>}
    </div>
  );
}

function DeleteAccountConfirmation({
  onCancel,
  onDelete,
}: {
  onCancel: () => void;
  onDelete: (credential: string, turnstileToken?: string) => Promise<void>;
}) {
  const buttonRef = useRef<HTMLDivElement>(null);
  const callbackRef = useRef(onDelete);
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const turnstileTokenRef = useRef<string | null>(null);
  const [turnstileVersion, setTurnstileVersion] = useState(0);

  useEffect(() => { callbackRef.current = onDelete; }, [onDelete]);

  useEffect(() => {
    if (!confirmed || !buttonRef.current) return;
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined;
    if (!clientId) {
      setError("Google sign-in is not configured for this deployment.");
      return;
    }
    let cancelled = false;
    const renderDeleteButton = () => {
      if (cancelled || !buttonRef.current || !window.google) return;
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response) => {
          setBusy(true);
          setError(null);
          try {
            const token = turnstileTokenRef.current;
            if (import.meta.env.PROD && !token) throw new Error("Complete the bot-protection check first.");
            await callbackRef.current(response.credential, token ?? undefined);
          } catch (err) {
            setError(err instanceof Error ? err.message : "Deletion could not be confirmed.");
          } finally {
            turnstileTokenRef.current = null;
            setTurnstileVersion((version) => version + 1);
            setBusy(false);
          }
        },
      });
      window.google.accounts.id.renderButton(buttonRef.current, { theme: "outline", size: "large" });
    };
    if (window.google) {
      renderDeleteButton();
    } else {
      const existing = document.getElementById(GOOGLE_SCRIPT_ID) as HTMLScriptElement | null;
      if (existing) existing.addEventListener("load", renderDeleteButton, { once: true });
      else {
        const script = document.createElement("script");
        script.id = GOOGLE_SCRIPT_ID;
        script.src = "https://accounts.google.com/gsi/client";
        script.async = true;
        script.defer = true;
        script.onload = renderDeleteButton;
        script.onerror = () => setError("Could not load Google sign-in.");
        document.head.appendChild(script);
      }
    }
    return () => { cancelled = true; };
  }, [confirmed]);

  return (
    <div className="page">
      <div className="panel">
        <h1>Delete account and all team data?</h1>
        <p>This permanently deletes your coach account, team roster, training sessions, and check-ins from the active database. This cannot be undone.</p>
        <label className="consent-confirmation">
          <input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />
          I understand this deletion is permanent and want to continue.
        </label>
        {confirmed && <><p>Complete the bot check and a fresh Google sign-in below to confirm this deletion.</p><TurnstileWidget key={turnstileVersion} action="delete_account" onToken={(token) => { turnstileTokenRef.current = token; }} /></>}
        <div ref={buttonRef} />
        {busy && <p>Deleting account and team data…</p>}
        {error && <p className="form-error">{error}</p>}
        <button type="button" className="copy-link" disabled={busy} onClick={onCancel}>Cancel</button>
      </div>
    </div>
  );
}
