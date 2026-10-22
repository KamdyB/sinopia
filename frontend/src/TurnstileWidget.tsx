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
const SCRIPT_URL = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";

export function TurnstileWidget({ action, onToken }: {
  action: "login" | "delete_account";
  onToken: (token: string | null) => void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const callbackRef = useRef(onToken);
  const [error, setError] = useState<string | null>(null);
  const [verified, setVerified] = useState(false);
  const [retryVersion, setRetryVersion] = useState(0);
  callbackRef.current = onToken;

  useEffect(() => {
    const sitekey = (import.meta.env.VITE_TURNSTILE_SITE_KEY as string | undefined)?.trim();
    setError(null);
    setVerified(false);

    if (!sitekey) {
      callbackRef.current(null);
      setError("Bot protection is not configured on this deployment. The site owner must set VITE_TURNSTILE_SITE_KEY in the coach app's Vercel environment and redeploy.");
      return;
    }

    let cancelled = false;
    let widgetId: string | null = null;
    let script: HTMLScriptElement | null = null;
    let timeoutId: number | undefined;

    const clearTimeoutIfNeeded = () => {
      if (timeoutId !== undefined) window.clearTimeout(timeoutId);
    };

    const fail = (message: string) => {
      if (cancelled) return;
      callbackRef.current(null);
      setVerified(false);
      setError(message);
      if (script) script.dataset.sinopiaFailed = "true";
      clearTimeoutIfNeeded();
    };

    const renderWidget = () => {
      if (cancelled || !hostRef.current || !window.turnstile || widgetId) return;
      clearTimeoutIfNeeded();
      try {
        widgetId = window.turnstile.render(hostRef.current, {
          sitekey,
          action,
          callback: (token) => {
            setError(null);
            setVerified(Boolean(token));
            callbackRef.current(token || null);
          },
          "expired-callback": () => {
            setVerified(false);
            callbackRef.current(null);
            setError("The bot check expired. Complete it again before signing in.");
          },
          "error-callback": () => fail("Cloudflare could not complete the bot check. Check your connection or Turnstile site-key/domain settings, then retry."),
          theme: "auto",
        });
      } catch {
        fail("Cloudflare's bot check could not start. Retry, and check the Turnstile site-key/domain settings if it persists.");
      }
    };

    const handleLoad = () => {
      if (window.turnstile) renderWidget();
      else fail("Cloudflare's script loaded without its widget API. Check network blocking, content-security settings, or retry.");
    };
    const handleError = () => fail("Cloudflare's bot-check script could not load. Check your connection, content blockers, and the coach app's security settings.");

    const existing = document.getElementById(SCRIPT_ID) as HTMLScriptElement | null;
    if (existing?.dataset.sinopiaFailed === "true") existing.remove();

    if (window.turnstile) {
      renderWidget();
    } else {
      script = document.getElementById(SCRIPT_ID) as HTMLScriptElement | null;
      const shouldAppend = !script;
      if (!script) {
        script = document.createElement("script");
        script.id = SCRIPT_ID;
        script.src = SCRIPT_URL;
        script.async = true;
        script.defer = true;
      }
      // Attach listeners before appending so a fast cached response cannot race past them.
      script.addEventListener("load", handleLoad, { once: true });
      script.addEventListener("error", handleError, { once: true });
      if (shouldAppend) document.head.appendChild(script);
      timeoutId = window.setTimeout(() => {
        if (!window.turnstile) fail("Cloudflare's bot check did not finish loading. Retry or check whether your browser/network blocks challenges.cloudflare.com.");
      }, 12000);
    }

    return () => {
      cancelled = true;
      clearTimeoutIfNeeded();
      script?.removeEventListener("load", handleLoad);
      script?.removeEventListener("error", handleError);
      if (widgetId && window.turnstile) window.turnstile.remove(widgetId);
    };
  }, [action, retryVersion]);

  return (
    <div className="turnstile-check" aria-label="Bot protection">
      <p className="turnstile-check__label">A quick security check</p>
      <div ref={hostRef} className="turnstile-check__widget" />
      {verified && <p className="turnstile-check__status" role="status">Security check complete.</p>}
      {error && (
        <div className="turnstile-check__error" role="alert">
          <p className="form-error">{error}</p>
          {!error.includes("VITE_TURNSTILE_SITE_KEY") && (
            <button type="button" className="copy-link" onClick={() => setRetryVersion((version) => version + 1)}>
              Retry security check
            </button>
          )}
        </div>
      )}
    </div>
  );
}
