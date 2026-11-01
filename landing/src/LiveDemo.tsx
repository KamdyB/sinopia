// landing/src/LiveDemo.tsx
import { useState } from "react";
import { DEMO_PLAYER, DEMO_SESSIONS, walkForward, Assessment } from "./engine";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const shortDate = (iso: string) => MONTHS[Number(iso.slice(5, 7)) - 1] + " " + Number(iso.slice(8, 10));
const LABEL: Record<Assessment["level"], string> = {
  building: "Building baseline",
  ok: "No load flag",
  act: "Review next session",
};

export function LiveDemo() {
  const [logged, setLogged] = useState(1);
  const all = walkForward(DEMO_SESSIONS);
  const visible = all.slice(0, logged);
  const current = visible[visible.length - 1];
  const session = DEMO_SESSIONS[logged - 1];
  const maxLoad = Math.max(1, ...visible.map((point) => Math.max(point.weeklyLoad, point.baseline)));
  return (
    <div className="demo">
      <div className="demo-col">
        <p className="demo-kicker">Synthetic example for {DEMO_PLAYER}. No real athlete data.</p>
        <div className="demo-session-card">
          <span className="demo-session-card__date">{shortDate(session.date)}</span>
          <span className="demo-session-card__math">{session.minutes} min × RPE {session.rpe}</span>
          <span className="demo-session-card__load">{session.minutes * session.rpe} session-load units</span>
        </div>
        <div className="demo-controls">
          <button className="btn btn--primary" onClick={() => setLogged((n) => Math.min(n + 1, DEMO_SESSIONS.length))} disabled={logged >= DEMO_SESSIONS.length}>Log next session</button>
          <button className="btn" onClick={() => setLogged(1)}>Replay</button>
        </div>
        <p className="demo-progress">{logged} of {DEMO_SESSIONS.length} sessions logged</p>
      </div>
      <div className="demo-col">
        <p className="demo-kicker">Load-only demonstration. Wellness and pain reports are not simulated.</p>
        <div className="demo-score" data-band={current.level}>
          <span className="demo-score__band">{LABEL[current.level]}</span>
          <span className="demo-score__value">{current.weeklyLoad.toFixed(0)} load units / 7 days</span>
        </div>
        <div className="demo-chart demo-chart--simple">
          <div className="demo-comparison">
            <div className="demo-comparison__heading"><span>Current 7-day load</span><strong>{current.weeklyLoad.toFixed(0)}</strong></div>
            <div className="demo-comparison__track"><span className="demo-comparison__fill" style={{ width: (current.weeklyLoad / maxLoad * 100) + "%" }} /></div>
          </div>
          <div className="demo-comparison">
            <div className="demo-comparison__heading"><span>Prior complete-week baseline</span><strong>{current.baseline.toFixed(0)}</strong></div>
            <div className="demo-comparison__track"><span className="demo-comparison__fill demo-comparison__fill--baseline" style={{ width: (current.baseline / maxLoad * 100) + "%" }} /></div>
          </div>
          <p className="demo-comparison__note">Each bar shows one number. Compare the current week with the previous complete-week baseline.</p>
        </div>
        <ul className="demo-explanation">
          {current.level === "building" ? (
            <li>{current.weeksAvailable} tracked week(s). The load flag stays inactive until at least 3 weeks are tracked and a complete baseline exists.</li>
          ) : (
            <>
              <li>Previous complete-week baseline: {current.baseline.toFixed(0)} units.</li>
              <li>{current.level === "act" ? "The current weekly load is more than 1.5 times the baseline. Review the next session and speak with the athlete." : "The current weekly load has not crossed the provisional 1.5-times baseline threshold."}</li>
            </>
          )}
        </ul>
      </div>
    </div>
  );
}
