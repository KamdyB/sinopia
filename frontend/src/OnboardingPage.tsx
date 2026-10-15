import { useState } from "react";

const API_BASE = (import.meta.env.VITE_API_BASE || "/api").replace(/\/+$/, "");

export function OnboardingPage() {
  const [name, setName] = useState("");
  const [teamType, setTeamType] = useState<"girls" | "boys" | "mixed">("girls");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submit = async () => {
    if (!name.trim()) { setError("Enter a team name."); return; }
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/teams`, {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), team_type: teamType }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        if (response.status === 401) { window.location.assign("/sign-in?expired=1"); return; }
        throw new Error(typeof body.detail === "string" ? body.detail : "Could not save your team.");
      }
      window.location.assign("/app");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save your team.");
    } finally {
      setBusy(false);
    }
  };

  return <main className="page"><section className="panel">
    <h1>Set up your team</h1>
    <p>Choose your team composition once. Sinopia will use it for roster labels and athlete registration.</p>
    <div className="field-group">
      <label className="field-group__label" htmlFor="team-name">Team name</label>
      <input id="team-name" value={name} maxLength={120} onChange={(e) => setName(e.target.value)} placeholder="e.g. U17 Football" />
    </div>
    <fieldset className="checkin__question"><legend>Team composition</legend>
      <label><input type="radio" name="team-type" checked={teamType === "girls"} onChange={() => setTeamType("girls")} /> Girls</label>
      <label><input type="radio" name="team-type" checked={teamType === "boys"} onChange={() => setTeamType("boys")} /> Boys</label>
      <label><input type="radio" name="team-type" checked={teamType === "mixed"} onChange={() => setTeamType("mixed")} /> Mixed</label>
    </fieldset>
    <button className="record-btn" onClick={submit} disabled={busy}>{busy ? "Saving…" : "Create team"}</button>
    {error && <p className="checkin__error" role="alert">{error}</p>}
  </section></main>;
}
