// frontend/src/DashboardTable.tsx
// One row per athlete: name, level as text and colour, and the leading
// reason inline. The why view expands with every reason and the numbers.
import { useState } from "react";
import { AthleteStatus } from "./types";
import { LEVEL_LABEL } from "./level";

export function DashboardTable({
  entries,
  onSelect,
}: {
  entries: AthleteStatus[];
  onSelect: (playerId: string) => void;
}) {
  const [openId, setOpenId] = useState<string | null>(null);
  return (
    <div className="status-table">
      <div className="status-table__head">
        <span>Athlete</span>
        <span>Level</span>
        <span>Why</span>
      </div>
      {entries.map((entry) => (
        <div className="status-table__group" key={entry.player_id}>
          <div className="status-row">
            <button
              type="button"
              className="status-row__name"
              onClick={() => onSelect(entry.player_id)}
            >
              {entry.name}
            </button>
            <span className="status-row__level" data-level={entry.level}>
              {LEVEL_LABEL[entry.level] ?? entry.level}
            </span>
            <button
              type="button"
              className="status-row__why"
              onClick={() =>
                setOpenId(openId === entry.player_id ? null : entry.player_id)
              }
              aria-expanded={openId === entry.player_id}
            >
              {entry.reasons.length > 0 ? entry.reasons[0] : "No flags"}
            </button>
          </div>
          {openId === entry.player_id && (
            <div className="status-row__detail">
              <ul>
                {entry.reasons.map((reason, i) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
              <dl className="status-row__numbers">
                {Object.entries(entry.numbers).map(([key, value]) => (
                  <div key={key}>
                    <dt>{key.replace(/_/g, " ")}</dt>
                    <dd>{String(value)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
