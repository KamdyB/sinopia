import { useEffect, useState } from "react";

type InstallEvent = Event & { prompt: () => Promise<void>; userChoice: Promise<{ outcome: string }> };

// Shows an "Install app" button only when the browser says the app can be installed.
export function InstallButton() {
  const [event, setEvent] = useState<InstallEvent | null>(null);

  useEffect(() => {
    const onPrompt = (e: Event) => { e.preventDefault(); setEvent(e as InstallEvent); };
    const onInstalled = () => setEvent(null);
    window.addEventListener("beforeinstallprompt", onPrompt);
    window.addEventListener("appinstalled", onInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", onPrompt);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  if (!event) return null;
  return (
    <button
      type="button"
      className="copy-link"
      onClick={() => { void event.prompt(); setEvent(null); }}
    >
      Install app
    </button>
  );
}
