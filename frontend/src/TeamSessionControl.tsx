import { useEffect, useState } from "react";

const API_BASE = (import.meta.env.VITE_API_BASE || "/api").replace(/\/+$/, "");
type TeamSession = { session_id: string; date: string; duration_minutes: number; is_open: boolean };

export function TeamSessionControl() {
  const [session, setSession] = useState<TeamSession | null>(null);
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [duration, setDuration] = useState(60);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const refresh = async () => {
    const response = await fetch(`${API_BASE}/team-sessions/current`, { credentials: "include" });
    const body = await response.json().catch(() => ({}));
    if (response.status === 401) { window.location.assign("/sign-in?expired=1"); return; }
    if (!response.ok) throw new Error(body.detail || "Could not load the team session.");
    setSession(body.session);
  };

  useEffect(() => { void refresh().catch((e) => setError(e instanceof Error ? e.message : "Could not load the team session.")); }, []);

  const act = async (action: "open" | "close") => {
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/team-sessions/${action}`, {
        method: "POST", credentials: "include", headers: { "Content-Type": "application/json" },
        body: action === "open" ? JSON.stringify({ date_str: date, duration_minutes: duration }) : "{}",
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail || "Could not update the team session.");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not update the team session.");
    } finally { setBusy(false); }
  };

  return <section className="panel">
    <p className="section-title">Athlete effort check-in</p>
    {session ? <>
      <p>Session open · {session.date} · {session.duration_minutes} minutes. Athlete links now ask for an effort rating.</p>
      <button type="button" className="record-btn" onClick={() => void act("close")} disabled={busy}>{busy ? "Saving…" : "Close team session"}</button>
    </> : <>
      <p>Open a team session to ask athletes for their effort rating through their personal check-in links.</p>
      <div className="field-row">
        <div className="field-group"><label className="field-group__label" htmlFor="team-session-date">Session date</label><input id="team-session-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} /></div>
        <div className="field-group"><label className="field-group__label" htmlFor="team-session-duration">Duration (minutes)</label><input id="team-session-duration" type="number" min={1} max={180} value={duration} onChange={(e) => setDuration(Number(e.target.value))} /></div>
      </div>
      <button type="button" className="record-btn" onClick={() => void act("open")} disabled={busy || !date || duration < 1 || duration > 180}>{busy ? "Saving…" : "Open team session"}</button>
    </>}
    {error && <p className="checkin__error" role="alert">{error}</p>}
  </section>;
}
