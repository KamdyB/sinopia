import { useState } from "react";

const API_BASE = (import.meta.env.VITE_API_BASE || "/api").replace(/\/+$/, "");

export function OnboardingPage() {
  const [name, setName] = useState("");
  const [teamType, setTeamType] = useState<"girls" | "boys" | "mixed">("girls");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
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
        body: JSON.stringify({ name: name.trim(), team_type: teamType, accepted_terms: acceptedTerms }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        if (response.status === 401) { window.location.assign(String(body.detail || "").toLowerCase().includes("expired") ? "/sign-in?expired=1" : "/sign-in"); return; }
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
    <label><input type="checkbox" checked={acceptedTerms} onChange={(e) => setAcceptedTerms(e.target.checked)} /> I have read and accept the <a href="/terms" target="_blank" rel="noreferrer">Terms</a> and <a href="/privacy" target="_blank" rel="noreferrer">Privacy notice</a>.</label>
    <button className="record-btn" onClick={submit} disabled={busy || !acceptedTerms}>{busy ? "Saving…" : "Create team"}</button>
    {error && <p className="checkin__error" role="alert">{error}</p>}
  </section></main>;
}
