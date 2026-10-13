// frontend/src/PlayerDirectory.tsx
// The roster holds athlete codes only; names never enter the system.
import { useState } from "react";
import { Player } from "./types";

export function PlayerDirectory({
  players,
  onAdd,
  demo = false,
}: {
  players: Player[];
  onAdd: (code: string) => Promise<void>;
  demo?: boolean;
}) {
  const [query, setQuery] = useState("");
  const [newCode, setNewCode] = useState("");
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const normalized = query.trim().toLowerCase();
  const visible = players.filter((p) =>
    p.code.toLowerCase().includes(normalized),
  );

  const handleAdd = async () => {
    if (!newCode.trim()) {
      setError("Enter a code to register.");
      return;
    }
    setAdding(true);
    setError(null);
    try {
      await onAdd(newCode.trim());
      setNewCode("");
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
      // Clipboard can be blocked; the prompt fallback still lets the
      // coach copy the link manually.
      window.prompt("Copy this link:", url);
    }
    setCopiedId(playerId);
  };

  return (
    <div className="panel player-directory">
      <p className="section-title">
        {demo ? "Demo squad" : "Team directory"}
      </p>
      {!demo && (
        <div className="field-row">
          <div className="field-group">
            <label className="field-group__label" htmlFor="player-search">
              Search roster
            </label>
            <input
              id="player-search"
              type="search"
              value={query}
              placeholder="Type a code"
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <div className="field-group">
            <label className="field-group__label" htmlFor="add-player">
              Add athlete code, once per season
            </label>
            <input
              id="add-player"
              type="text"
              value={newCode}
              placeholder="e.g. ATH-01, J.SMITH-7"
              onChange={(e) => setNewCode(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleAdd();
                }
              }}
            />
          </div>
          <button className="record-btn" onClick={handleAdd} disabled={adding}>
            {adding ? "Adding..." : "Add athlete"}
          </button>
        </div>
      )}
      {error && <div className="form-error">{error}</div>}
      <p className="empty-note roster-note">
        Codes only, never names. The check-in link works per athlete.
      </p>
      {players.length === 0 ? (
        <p className="empty-note">
          {demo
            ? "Loading the demo squad..."
            : "Nobody registered for this team yet. Add each athlete's code once, then log sessions against it."}
        </p>
      ) : visible.length === 0 ? (
        <p className="empty-note">No athlete code matches &ldquo;{query}&rdquo;.</p>
      ) : (
        <ul className="directory-list">
          {visible.map((p) => (
            <li key={p.player_id}>
              <span
                className={`directory-row${copiedId === p.player_id ? " directory-row--active" : ""}`}
              >
                <span className="directory-row__name">{p.code}</span>
                {!demo && (
                  <button
                    type="button"
                    className="copy-link"
                    onClick={() => copyCheckinLink(p.player_id)}
                  >
                    {copiedId === p.player_id ? "Link copied" : "Copy check-in link"}
                  </button>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
