// frontend/src/PlayerHistory.tsx
// Per-athlete history as a readable walk-forward list: each session with
// the level the rules produced at that date and the reason behind it.
import { HistoryPoint, Player } from "./types";
import { LEVEL_LABEL } from "./level";

export function PlayerHistory({
  player,
  history,
  loading,
  error,
  onClose,
}: {
  player: Player;
  history: HistoryPoint[] | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}) {
  return (
    <div className="panel player-detail">
      <div className="player-detail__head">
        <div>
          <p className="section-title">Athlete history</p>
          <h2 className="player-detail__name">{player.name}</h2>
          <p className="player-detail__meta">
            {history?.length ?? 0} sessions logged
          </p>
        </div>
        <button className="close-btn" onClick={onClose}>
          Close
        </button>
      </div>
      {loading && <p className="empty-note">Loading history...</p>}
      {error && <div className="form-error">{error}</div>}
      {!loading && !error && history !== null && (
        history.length === 0 ? (
          <p className="empty-note">No sessions logged yet.</p>
        ) : (
          <ol className="history-list">
            {history.map((point) => (
              <li key={point.date} data-level={point.level}>
                <span className="history-list__date">{point.date}</span>
                <span className="history-list__level">
                  {LEVEL_LABEL[point.level] ?? point.level}
                </span>
                <span className="history-list__load">{point.session_load} load</span>
                {point.reasons.length > 0 && <p>{point.reasons[0]}</p>}
              </li>
            ))}
          </ol>
        )
      )}
    </div>
  );
}
