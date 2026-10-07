// frontend/src/SessionEntryForm.tsx
import { FormEvent, useRef, useState } from "react";
import { Player, SessionPayload } from "./types";
import { logSession } from "./api";

const TODAY_ISO = new Date().toISOString().slice(0, 10);

export function SessionEntryForm({
  players,
  onScored,
}: {
  players: Player[];
  onScored: () => void;
}) {
  const [playerId, setPlayerId] = useState("");
  const [dateStr, setDateStr] = useState(TODAY_ISO);
  // Duration is set once for the whole squad and carries across submissions,
  // since the team trains the same length of time together.
  const [durationMinutes, setDurationMinutes] = useState(0);
  const [rpe, setRpe] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const playerSelectRef = useRef<HTMLSelectElement>(null);

  const calculatedLoad = durationMinutes * rpe;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!playerId) {
      setError("Choose an athlete first. Register them in the directory if they are missing.");
      return;
    }
    if (durationMinutes <= 0 || rpe <= 0) {
      setError("Enter a duration and RPE greater than zero.");
      return;
    }
    if (dateStr > TODAY_ISO) {
      setError("Session date cannot be in the future.");
      return;
    }
    setSubmitting(true);
    setError(null);
    const payload: SessionPayload = {
      player_id: playerId,
      date_str: dateStr,
      duration_minutes: durationMinutes,
      rpe,
    };
    try {
      await logSession(payload);
      onScored();
      setRpe(0); // next athlete, same sitting
      playerSelectRef.current?.focus(); // back to the top, no mouse needed
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not reach the scoring service. Is the backend running?",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="log-session" onSubmit={handleSubmit}>
      <p className="section-title">Log session</p>
      <div className="field-group">
        <label className="field-group__label" htmlFor="who">Who</label>
        <select
          id="who"
          ref={playerSelectRef}
          value={playerId}
          onChange={(e) => setPlayerId(e.target.value)}
        >
          <option value="">
            {players.length === 0 ? "No athletes registered yet" : "Choose an athlete"}
          </option>
          {players.map((p) => (
            <option key={p.player_id} value={p.player_id}>{p.name}</option>
          ))}
        </select>
      </div>
      <div className="field-row">
        <div className="field-group">
          <label className="field-group__label" htmlFor="session-date">Date</label>
          <input
            id="session-date"
            type="date"
            value={dateStr}
            max={TODAY_ISO}
            onChange={(e) => setDateStr(e.target.value)}
          />
        </div>
        <div className="field-group">
          <label className="field-group__label" htmlFor="duration">
            Session, minutes, set once for the squad
          </label>
          <input
            id="duration"
            type="number"
            min={1}
            max={180}
            value={durationMinutes || ""}
            placeholder="0"
            onChange={(e) => setDurationMinutes(+e.target.value)}
          />
        </div>
        <div className="field-group">
          <label className="field-group__label" htmlFor="rpe">Effort, 0 to 10</label>
          <input
            id="rpe"
            type="number"
            min={0}
            max={10}
            value={rpe || ""}
            placeholder="0"
            onChange={(e) => setRpe(+e.target.value)}
          />
        </div>
      </div>
      <div className="calculated-load">
        <div className="calculated-load__label">Calculated load</div>
        <div className="calculated-load__value">{calculatedLoad || 0}</div>
        <div className="calculated-load__unit">minutes &times; RPE</div>
      </div>
      <button className="record-btn" type="submit" disabled={submitting}>
        {submitting ? "Recording..." : "Record session"}
      </button>
      {error && <div className="form-error">{error}</div>}
    </form>
  );
}
