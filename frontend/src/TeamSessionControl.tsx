import { useEffect, useState } from "react";
import { closeTeamSession, fetchOpenTeamSession, openTeamSession } from "./api";
import { OpenTeamSession } from "./types";

function localDate() {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

export function TeamSessionControl() {
  const [session, setSession] = useState<OpenTeamSession | null>(null);
  const [date, setDate] = useState(localDate);
  const [duration, setDuration] = useState(60);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const refresh = async () => setSession(await fetchOpenTeamSession());

  useEffect(() => {
    void refresh().catch((e) => {
      const message = e instanceof Error ? e.message : "Could not load the open team session.";
      if (message.toLowerCase().includes("session expired") || message.toLowerCase().includes("sign-in required")) {
        window.location.assign("/sign-in?expired=1");
      } else setError(message);
    });
  }, []);

  const open = async () => {
    setBusy(true);
    setError("");
    try {
      setSession(await openTeamSession(date, duration));
    } catch (e) {
      const message = e instanceof Error ? e.message : "Could not open the team session.";
      if (message.toLowerCase().includes("session expired") || message.toLowerCase().includes("sign-in required")) {
        window.location.assign("/sign-in?expired=1");
      } else setError(message);
    } finally { setBusy(false); }
  };

  const close = async () => {
    setBusy(true);
    setError("");
    try {
      await closeTeamSession();
      setSession(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not close the team session.");
    } finally { setBusy(false); }
  };

  return <section className="panel">
    <p className="section-title">Athlete effort check-in</p>
    {session ? <>
      <p>Team session open · {session.session_date} · {session.duration_minutes} minutes. Athlete check-in links ask for an effort rating while this session is open.</p>
      <button type="button" className="record-btn" onClick={() => void close()} disabled={busy}>{busy ? "Saving…" : "Close team session"}</button>
    </> : <>
      <p>Open a team session to collect each athlete's effort rating through their personal check-in link.</p>
      <div className="field-row">
        <div className="field-group"><label className="field-group__label" htmlFor="team-session-date">Session date</label><input id="team-session-date" type="date" max={localDate()} value={date} onChange={(e) => setDate(e.target.value)} /></div>
        <div className="field-group"><label className="field-group__label" htmlFor="team-session-duration">Duration (minutes)</label><input id="team-session-duration" type="number" min={1} max={180} value={duration} onChange={(e) => setDuration(Number(e.target.value))} /></div>
      </div>
      <button type="button" className="record-btn" onClick={() => void open()} disabled={busy || !date || duration < 1 || duration > 180}>{busy ? "Saving…" : "Open team session"}</button>
    </>}
    {error && <p className="form-error" role="alert">{error}</p>}
  </section>;
}
