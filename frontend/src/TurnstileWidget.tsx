import { useEffect, useRef, useState } from "react";

type TurnstileApi = {
  render: (container: HTMLElement, options: {
    sitekey: string;
    action: string;
    callback: (token: string) => void;
    "expired-callback": () => void;
    "error-callback": () => void;
    theme?: "light" | "dark" | "auto";
  }) => string;
  remove: (widgetId: string) => void;
};
declare global {
  interface Window { turnstile?: TurnstileApi; }
}

const SCRIPT_ID = "sinopia-turnstile-script";

export function TurnstileWidget({ action, onToken }: {
  action: "login" | "delete_account";
  onToken: (token: string | null) => void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const callbackRef = useRef(onToken);
  const [error, setError] = useState<string | null>(null);
  callbackRef.current = onToken;

  useEffect(() => {
    const sitekey = import.meta.env.VITE_TURNSTILE_SITE_KEY as string | undefined;
    if (!sitekey) {
      setError("Bot protection is not configured for this deployment.");
      callbackRef.current(null);
      return;
    }
    let cancelled = false;
    let widgetId: string | null = null;
    const render = () => {
      if (cancelled || !hostRef.current || !window.turnstile || widgetId) return;
      widgetId = window.turnstile.render(hostRef.current, {
        sitekey,
        action,
        callback: (token) => { setError(null); callbackRef.current(token); },
        "expired-callback": () => { callbackRef.current(null); setError("Bot check expired. Complete it again."); },
        "error-callback": () => { callbackRef.current(null); setError("Bot check could not load. Try again."); },
        theme: "auto",
      });
    };
    const existing = document.getElementById(SCRIPT_ID) as HTMLScriptElement | null;
    if (window.turnstile) render();
    else if (existing) existing.addEventListener("load", render, { once: true });
    else {
      const script = document.createElement("script");
      script.id = SCRIPT_ID;
      script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
      script.async = true;
      script.defer = true;
      script.onload = render;
      script.onerror = () => setError("Bot check could not load. Try again.");
      document.head.appendChild(script);
    }
    return () => {
      cancelled = true;
      if (widgetId && window.turnstile) window.turnstile.remove(widgetId);
    };
  }, [action]);

  return <div className="turnstile-check">
    <div ref={hostRef} />
    {error && <p className="form-error" role="alert">{error}</p>}
  </div>;
}
