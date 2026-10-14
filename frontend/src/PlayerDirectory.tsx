// frontend/src/PlayerDirectory.tsx
import { useState } from "react";
import { Player } from "./types";

export function PlayerDirectory({
  players,
  onAdd,
}: {
  players: Player[];
  onAdd: (name: string) => Promise<void>;
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
      await onAdd(newName.trim());
      setNewName("");
      setConsentConfirmed(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not register the athlete.");
    } finally {
      setAdding(false);
    }
  };

  const copyCheckinLink = async (playerId: string) => {
    const url = `${window.location.origin}/checkin/${playerId}`;
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      window.prompt("Copy this link:", url);
    }
    setCopiedId(playerId);
  };

  return (
    <div className="panel player-directory">
      <p className="section-title">Team directory</p>
      <div className="field-row">
        <div className="field-group">
          <label className="field-group__label" htmlFor="player-search">Search roster</label>
          <input id="player-search" type="search" value={query} placeholder="Type a name or code"
            onChange={(e) => setQuery(e.target.value)} />
        </div>
        <div className="field-group">
          <label className="field-group__label" htmlFor="add-player">Add athlete, once per season</label>
          <input id="add-player" type="text" value={newName} placeholder="Initials or team code"
            maxLength={80} onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleAdd();
              }
            }} />
        </div>
        <button className="record-btn" onClick={handleAdd} disabled={adding || !consentConfirmed}>
          {adding ? "Adding..." : "Add athlete"}
        </button>
      </div>
      <label className="consent-confirmation">
        <input type="checkbox" checked={consentConfirmed}
          onChange={(e) => setConsentConfirmed(e.target.checked)} />
        I confirm that I am authorised to record this athlete's data and have obtained
        the required parent or guardian consent for athletes under 18.
      </label>
      <p className="empty-note">Use initials or a code rather than a full name wherever possible.</p>
      {error && <div className="form-error">{error}</div>}
      {players.length === 0 ? (
        <p className="empty-note">Nobody registered for this team yet. Add each athlete once, then log sessions against them.</p>
      ) : visible.length === 0 ? (
        <p className="empty-note">No athlete matches &ldquo;{query}&rdquo;.</p>
      ) : (
        <ul className="directory-list">
          {visible.map((p) => (
            <li key={p.player_id}>
              <span className={`directory-row${copiedId === p.player_id ? " directory-row--active" : ""}`}>
                <span className="directory-row__name">{p.name}</span>
                <button type="button" className="copy-link" onClick={() => copyCheckinLink(p.player_id)}>
                  {copiedId === p.player_id ? "Link copied" : "Copy check-in link"}
                </button>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
