import { ReactNode, useEffect, useRef, useState } from "react";
import {
  acceptCoachPolicies,
  CoachSession,
  fetchCoachSession,
  signInWithGoogle,
  signOut,
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
  const [error, setError] = useState<string | null>(null);

  const refreshSession = async () => {
    const current = await fetchCoachSession();
    setCoach(current);
    return current;
  };

  useEffect(() => {
    let cancelled = false;
    fetchCoachSession()
      .then((current) => { if (!cancelled) setCoach(current); })
      .catch(() => { if (!cancelled) setCoach(null); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (loading || coach || !buttonRef.current) return;
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
          setBusy(true);
          setError(null);
          try {
            const signedIn = await signInWithGoogle(credentialResponse.credential);
            setCoach(signedIn);
          } catch (err) {
            setError(err instanceof Error ? err.message : "Google sign-in failed.");
          } finally {
            setBusy(false);
          }
        },
      });
      window.google.accounts.id.renderButton(buttonRef.current, {
        theme: "outline",
        size: "large",
      });
    };

    const existingScript = document.getElementById(GOOGLE_SCRIPT_ID) as HTMLScriptElement | null;
    if (window.google) {
      renderGoogleButton();
    } else if (existingScript) {
      existingScript.addEventListener("load", renderGoogleButton, { once: true });
    } else {
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
  }, [loading, coach]);

  const handleAccept = async () => {
    setBusy(true);
    setError(null);
    try {
      await acceptCoachPolicies(ageConfirmed, consentConfirmed);
      await refreshSession();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the declarations.");
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign out.");
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <div className="page"><p>Checking your session…</p></div>;

  if (!coach) {
    return (
      <div className="page">
        <div className="panel">
          <p className="eyebrow">Sinopia by KamdyB</p>
          <h1 className="display-title">Coach sign-in</h1>
          <p>Sign in with Google to access your team's training and check-in records.</p>
          <div ref={buttonRef} />
          {busy && <p>Signing in…</p>}
          {error && <p className="form-error">{error}</p>}
        </div>
      </div>
    );
  }

  if (coach.needs_policy_acceptance) {
    return (
      <div className="page">
        <div className="panel">
          <p className="eyebrow">Sinopia by KamdyB</p>
          <h1 className="display-title">Before you continue</h1>
          <p>Sinopia stores athlete training and wellness check-in information. You must make both declarations before accessing the dashboard.</p>
          <label className="consent-confirmation">
            <input type="checkbox" checked={ageConfirmed} onChange={(event) => setAgeConfirmed(event.target.checked)} />
            I am 18 years old or older.
          </label>
          <label className="consent-confirmation">
            <input type="checkbox" checked={consentConfirmed} onChange={(event) => setConsentConfirmed(event.target.checked)} />
            I am authorised by my school or club to record this team's data, and I have obtained parent or guardian consent for every athlete under 18.
          </label>
          <p>These are declarations, not independent age verification. Only continue if both statements are true.</p>
          <button className="record-btn" disabled={!ageConfirmed || !consentConfirmed || busy} onClick={handleAccept}>
            {busy ? "Saving…" : "Accept and continue"}
          </button>
          <button className="copy-link" disabled={busy} onClick={handleSignOut}>Sign out</button>
          {error && <p className="form-error">{error}</p>}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="auth-toolbar">
        <span>{coach.display_name}</span>
        <button type="button" className="copy-link" disabled={busy} onClick={handleSignOut}>Sign out</button>
      </div>
      {children}
      {error && <p className="form-error">{error}</p>}
    </div>
  );
}
