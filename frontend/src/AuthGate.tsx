import { ReactNode, useEffect, useRef, useState } from "react";
import { TurnstileWidget } from "./TurnstileWidget";
import {
  acceptCoachPolicies,
  CoachSession,
  deleteCoachAccount,
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
  const [deletionMode, setDeletionMode] = useState(false);
  const [deleted, setDeleted] = useState(false);
  const turnstileTokenRef = useRef<string | null>(null);
  const [turnstileVersion, setTurnstileVersion] = useState(0);

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
            const token = turnstileTokenRef.current;
            if (import.meta.env.PROD && !token) throw new Error("Complete the bot-protection check first.");
            const signedIn = await signInWithGoogle(credentialResponse.credential, token ?? undefined);
            setCoach(signedIn);
          } catch (err) {
            setError(err instanceof Error ? err.message : "Google sign-in failed.");
          } finally {
            turnstileTokenRef.current = null;
            setTurnstileVersion((version) => version + 1);
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign out.");
    } finally {
      setBusy(false);
    }
  };

  if (deleted) return <div className="page"><div className="panel"><h1>Account deleted</h1><p>Your coach account and team data have been deleted from the active database.</p></div></div>;

  if (loading) return <div className="page"><p>Checking your session…</p></div>;

  if (!coach) {
    return (
      <div className="page">
        <div className="panel">
          <p className="eyebrow">Sinopia by KamdyB</p>
          <h1 className="display-title">Coach sign-in</h1>
          <p>Sign in with Google to access your team's training and check-in records.</p>
          <TurnstileWidget key={turnstileVersion} action="login" onToken={(token) => { turnstileTokenRef.current = token; }} />
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
        <button type="button" className="copy-link" disabled={busy} onClick={() => setDeletionMode(true)}>Delete account and team data</button>
      </div>
      {deletionMode ? (
        <DeleteAccountConfirmation
          onCancel={() => setDeletionMode(false)}
          onDelete={handleDeleteAccount}
        />
      ) : children}
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
