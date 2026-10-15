import { useEffect, useState } from "react";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: { client_id: string; callback: (response: { credential: string }) => void }) => void;
          renderButton: (target: HTMLElement, options: Record<string, string | number>) => void;
        };
      };
    };
  }
}

const API_BASE = (import.meta.env.VITE_API_BASE || "/api").replace(/\/+$/, "");
const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

export function AuthPage({ intent }: { intent: "sign-in" | "sign-up" }) {
  const [adultConfirmed, setAdultConfirmed] = useState(false);
  const [authorized, setAuthorized] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [expired] = useState(() => new URLSearchParams(window.location.search).get("expired") === "1");

  useEffect(() => {
    if (!CLIENT_ID) {
      setError("Google sign-in is not configured. Set VITE_GOOGLE_CLIENT_ID in the coach app and GOOGLE_CLIENT_ID in the API.");
      return;
    }
    let cancelled = false;
    const init = () => {
      if (cancelled || !window.google) return;
      window.google.accounts.id.initialize({
        client_id: CLIENT_ID,
        callback: async ({ credential }) => {
          if (intent === "sign-up" && (!adultConfirmed || !authorized)) {
            setError("Confirm both declarations before creating an account.");
            return;
          }
          setBusy(true);
          setError("");
          try {
            const response = await fetch(`${API_BASE}/auth/google`, {
              method: "POST",
              credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ credential, intent, adult_confirmed: adultConfirmed, authorized }),
            });
            const body = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "Sign-in failed. Try again.");
            window.location.assign(body.team ? "/app" : "/onboarding");
          } catch (e) {
            setError(e instanceof Error ? e.message : "Could not sign in. Try again.");
          } finally {
            setBusy(false);
          }
        },
      });
      const button = document.getElementById("google-signin-button");
      if (button) window.google.accounts.id.renderButton(button, { theme: "outline", size: "large", text: "continue_with", shape: "rectangular", width: 280 });
    };
    if (window.google) init();
    else {
      const existing = document.querySelector<HTMLScriptElement>('script[data-sinopia-google="true"]');
      const script = existing || document.createElement("script");
      if (!existing) {
        script.src = "https://accounts.google.com/gsi/client";
        script.async = true;
        script.defer = true;
        script.dataset.sinopiaGoogle = "true";
        document.head.appendChild(script);
      }
      script.addEventListener("load", init, { once: true });
      script.addEventListener("error", () => setError("Google sign-in could not load. Check your connection."), { once: true });
      return () => {
        cancelled = true;
        script.removeEventListener("load", init);
      };
    }
    return () => { cancelled = true; };
  }, [intent, adultConfirmed, authorized]);

  return (
    <main className="page">
      <section className="panel">
        <h1>{intent === "sign-in" ? "Sign in to Sinopia" : "Create your coach account"}</h1>
        {expired && <p role="status">Your session expired. Sign in again to continue.</p>}
        {intent === "sign-up" && (
          <div className="checkin__question">
            <label><input type="checkbox" checked={adultConfirmed} onChange={(e) => setAdultConfirmed(e.target.checked)} /> I confirm I am at least 18 years old.</label>
            <label><input type="checkbox" checked={authorized} onChange={(e) => setAuthorized(e.target.checked)} /> I am authorized to manage this team's data and have responsibility for protecting athletes' information.</label>
          </div>
        )}
        <div id="google-signin-button" aria-label="Continue with Google" />
        {busy && <p role="status">Signing you in…</p>}
        {error && <p className="checkin__error" role="alert">{error}</p>}
        <p><a href={intent === "sign-in" ? "/sign-up" : "/sign-in"}>{intent === "sign-in" ? "New to Sinopia? Get started" : "Already have an account? Sign in"}</a></p>
        <p><a href="/privacy">Privacy</a> · <a href="/terms">Terms</a></p>
      </section>
    </main>
  );
}
