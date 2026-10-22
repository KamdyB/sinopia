// frontend/src/PlayerDirectory.tsx
import { useState } from "react";
import { AthleteStatus, Player } from "./types";
import { LEVEL_LABEL } from "./level";

export function PlayerDirectory({
  players,
  statuses,
  onAdd,
  onCreateCheckinLink,
  onDeletePlayer,
}: {
  players: Player[];
  statuses: AthleteStatus[];
  onAdd: (name: string, consentConfirmed: boolean) => Promise<void>;
  onCreateCheckinLink: (playerId: string) => Promise<string>;
  onDeletePlayer: (playerId: string) => Promise<void>;
}) {
  const [query, setQuery] = useState("");
  const [newName, setNewName] = useState("");
  const [consentConfirmed, setConsentConfirmed] = useState(false);
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const normalized = query.trim().toLowerCase();
  const visible = players.filter((p) => p.name.toLowerCase().includes(normalized));

  const handleAdd = async () => {
    if (!newName.trim()) {
      setError("Enter an athlete label or code.");
      return;
    }
    if (!consentConfirmed) {
      setError("Confirm that the required consent has been obtained before registering.");
      return;
    }
    setAdding(true);
    setError(null);
    try {
      await onAdd(newName.trim(), consentConfirmed);
      setNewName("");
      setConsentConfirmed(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not register the athlete.");
    } finally {
      setAdding(false);
    }
  };

  const copyCheckinLink = async (playerId: string) => {
    setError(null);
    try {
      const token = await onCreateCheckinLink(playerId);
      const url = window.location.origin + "/check-in/#checkin/" + encodeURIComponent(token);
      try {
        await navigator.clipboard.writeText(url);
      } catch {
        window.prompt("Copy this check-in link:", url);
      }
      setCopiedId(playerId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create a check-in link.");
    }
  };

  return (
    <div className="panel player-directory">
      <p className="section-title">Team directory</p>
      <div className="field-group roster-search">
        <label className="field-group__label" htmlFor="player-search">Find an athlete</label>
        <input id="player-search" type="search" value={query} placeholder="Search initials or team code"
          onChange={(e) => setQuery(e.target.value)} />
      </div>
      <details className="register-panel">
        <summary>Register an athlete</summary>
        <div className="register-panel__body">
          <div className="field-group">
            <label className="field-group__label" htmlFor="add-player">Athlete initials or team code</label>
            <input id="add-player" type="text" value={newName} placeholder="e.g. A12"
              maxLength={80} onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleAdd();
                }
              }} />
          </div>
          <label className="consent-confirmation">
            <input type="checkbox" checked={consentConfirmed}
              onChange={(e) => setConsentConfirmed(e.target.checked)} />
            I confirm that I am authorised to record this athlete's data and have obtained
            the required parent or guardian consent for athletes under 18.
          </label>
          <button type="button" className="record-btn" onClick={handleAdd} disabled={adding || !consentConfirmed}>
            {adding ? "Adding…" : "Save athlete"}
          </button>
          <p className="empty-note">Use initials or a code rather than a full name wherever possible.</p>
        </div>
      </details>
      {error && <div className="form-error">{error}</div>}
      {players.length === 0 ? (
        <p className="empty-note">Your roster is ready to get started. Register each athlete once, then log sessions as your team trains.</p>
      ) : visible.length === 0 ? (
        <p className="empty-note">No athlete matches &ldquo;{query}&rdquo;.</p>
      ) : (
        <ul className="directory-list">
          {visible.map((p) => (
            <li className="directory-card" key={p.player_id}>
              <div className={`directory-row${copiedId === p.player_id ? " directory-row--active" : ""}`}>
                <span className="directory-avatar" aria-hidden="true">
                  {p.name.trim().split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase() || "?"}
                </span>
                <span className="directory-card__main">
                  <span className="directory-row__name">{p.name}</span>
                  {(() => {
                    const status = statuses.find((entry) => entry.player_id === p.player_id);
                    return <span className="directory-status" data-level={status?.level ?? "building"}>
                      {status ? (LEVEL_LABEL[status.level] ?? status.level) : "No check-in yet"}
                    </span>;
                  })()}
                </span>
                <span className="directory-card__actions">
                  <button type="button" className="copy-link" onClick={() => copyCheckinLink(p.player_id)}>
                    {copiedId === p.player_id ? "Make new link" : "Check-in link"}
                  </button>
                  <button
                    type="button"
                    className="copy-link"
                    onClick={async () => {
                      if (!window.confirm("Permanently delete this athlete and all training/check-in history?")) return;
                      setError(null);
                      try {
                        await onDeletePlayer(p.player_id);
                      } catch (err) {
                        setError(err instanceof Error ? err.message : "Could not delete the athlete.");
                      }
                    }}
                  >
                    Delete
                  </button>
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
