// frontend/src/GoogleSignIn.tsx
// Renders Google's own button with Google Identity Services and hands
// the obtained ID token to signIn(). The backend, not this page, is
// what verifies the token.
import { useEffect, useRef, useState } from "react";
import { signIn } from "./api";

type GoogleAccounts = {
  accounts: {
    id: {
      initialize: (config: {
        client_id: string;
        callback: (response: { credential: string }) => void;
      }) => void;
      renderButton: (parent: HTMLElement, options: Record<string, unknown>) => void;
    };
  };
};

export function GoogleSignIn({ onSignedIn }: { onSignedIn: () => void }) {
  const holder = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const envClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined;
    const clientId = envClientId ?? "";
    if (!clientId) {
      setError("Google sign-in is not configured yet. Set VITE_GOOGLE_CLIENT_ID.");
      return;
    }
    let cancelled = false;

    function render() {
      if (cancelled || !holder.current) return;
      const g = (window as unknown as { google?: GoogleAccounts }).google;
      if (!g) return; // wait until the GIS script finishes loading
      g.accounts.id.initialize({
        client_id: clientId,
        callback: (response: { credential: string }) => {
          if (!response?.credential) return;
          signIn(response.credential);
          onSignedIn();
        },
      });
      g.accounts.id.renderButton(holder.current, {
        theme: "outline",
        size: "large",
        text: "signin_with",
        shape: "pill",
      });
    }

    if ((window as unknown as { google?: GoogleAccounts }).google) {
      render();
    } else {
      window.addEventListener("load", render);
      // GIS script is async; poll briefly until it is ready.
      const timer = window.setInterval(() => {
        if ((window as unknown as { google?: GoogleAccounts }).google) {
          window.clearInterval(timer);
          window.removeEventListener("load", render);
          render();
        }
      }, 200);
      window.setTimeout(() => window.clearInterval(timer), 15000);
      return () => {
        cancelled = true;
        window.clearInterval(timer);
      };
    }
    return () => {
      cancelled = true;
    };
  }, [onSignedIn]);

  return (
    <div className="signin">
      <p className="signin__title">Sign in with Google</p>
      <p className="signin__sub">
        One account owns one team. Your athletes are stored as codes, never
        as names, and your team's data is visible only to you.
      </p>
      <div ref={holder} className="gsi-holder" />
      {error && <div className="form-error">{error}</div>}
    </div>
  );
}
