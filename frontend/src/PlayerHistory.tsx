import { HistoryPoint, Player } from "./types";
import { LEVEL_LABEL } from "./level";

const PAIN_AREAS = ["Head", "Shoulder", "Chest or back", "Hip or groin", "Thigh", "Knee", "Ankle or foot", "Other"] as const;

function TrendChart({ title, points, value, colour, unit, note }: {
  title: string; points: HistoryPoint[]; value: (point: HistoryPoint) => number | null;
  colour: string; unit: string; note: string;
}) {
  const values = points.map(value);
  const valid = values.filter((v): v is number => v !== null && Number.isFinite(v));
  if (!valid.length) return <section className="history-chart"><h3>{title}</h3><p className="empty-note">No data recorded yet.</p><p className="chart-note">{note}</p></section>;
  const width = 620, height = 180, left = 42, right = 16, top = 16, bottom = 32;
  const min = Math.min(0, ...valid), max = Math.max(...valid, 1);
  const plotW = width - left - right, plotH = height - top - bottom;
  const coords = values.map((v, i) => v === null || !Number.isFinite(v) ? null : ({
    x: left + (values.length === 1 ? plotW / 2 : i * plotW / (values.length - 1)),
    y: top + plotH - ((v - min) / (max - min || 1)) * plotH,
    value: v, date: points[i].date,
  }));
  const path = coords.filter((p) => p !== null).map((p, i) => (i ? "L " : "M ") + p!.x.toFixed(1) + " " + p!.y.toFixed(1)).join(" ");
  const labels = coords.filter((p): p is NonNullable<typeof p> => p !== null).filter((_, i, arr) => i === 0 || i === arr.length - 1 || i === Math.floor(arr.length / 2));
  return <section className="history-chart">
    <h3>{title}</h3>
    <div className="chart-scroll">
      <svg className="history-chart__svg" viewBox="0 0 620 180" role="img" aria-label={title + " over time"}>
        {[0, 0.5, 1].map((fraction) => {
          const y = top + plotH * fraction, label = (max - (max - min) * fraction).toFixed(0);
          return <g key={fraction}><line x1={left} x2={width-right} y1={y} y2={y} stroke="currentColor" opacity="0.15" /><text x={left-8} y={y+4} textAnchor="end" fill="currentColor" opacity="0.7" fontSize="10">{label}</text></g>;
        })}
        <path d={path} fill="none" stroke={colour} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
        {coords.map((p, i) => p && <circle key={p.date + "-" + i} cx={p.x} cy={p.y} r="3.5" fill={colour}><title>{p.date + ": " + p.value + " " + unit}</title></circle>)}
        {labels.map((p) => <text key={"label-" + p.date} x={p.x} y={height-8} textAnchor="middle" fill="currentColor" opacity="0.7" fontSize="10">{p.date.slice(5)}</text>)}
      </svg>
    </div>
    <p className="chart-note">{note}</p>
  </section>;
}

function PainRegionMap({ points }: { points: HistoryPoint[] }) {
  const counts = new Map<string, number>();
  points.forEach((point) => { if (point.pain && point.pain_area) counts.set(point.pain_area, (counts.get(point.pain_area) ?? 0) + 1); });
  const hasPain = counts.size > 0;
  const fill = (area: string) => counts.has(area) ? "var(--elevated)" : "var(--surface-alt)";
  return <section className="history-chart pain-map">
    <h3>Self-reported pain locations</h3>
    <p className="chart-note">Recorded check-ins only. This is not a diagnosis or anatomical assessment.</p>
    {!hasPain ? <p className="empty-note">No pain locations recorded in this history.</p> : <div className="pain-map__layout">
      <svg viewBox="0 0 220 330" role="img" aria-label="Approximate front-facing body map showing recorded pain regions">
        <circle cx="110" cy="32" r="21" fill={fill("Head")} stroke="currentColor" strokeOpacity=".35" />
        <path d="M88 58 Q110 49 132 58 L145 105 L137 151 L83 151 L75 105 Z" fill={fill("Chest or back")} stroke="currentColor" strokeOpacity=".35" />
        <path d="M85 62 L60 72 L43 133 L56 137 L78 96" fill={fill("Shoulder")} stroke="currentColor" strokeOpacity=".35" />
        <path d="M135 62 L160 72 L177 133 L164 137 L142 96" fill={fill("Shoulder")} stroke="currentColor" strokeOpacity=".35" />
        <path d="M83 151 L137 151 L130 185 L90 185 Z" fill={fill("Hip or groin")} stroke="currentColor" strokeOpacity=".35" />
        <path d="M91 184 L109 184 L105 252 L87 252 Z" fill={fill("Thigh")} stroke="currentColor" strokeOpacity=".35" />
        <path d="M111 184 L129 184 L133 252 L115 252 Z" fill={fill("Thigh")} stroke="currentColor" strokeOpacity=".35" />
        <path d="M87 252 L105 252 L104 280 L87 280 Z" fill={fill("Knee")} stroke="currentColor" strokeOpacity=".35" />
        <path d="M115 252 L133 252 L134 280 L116 280 Z" fill={fill("Knee")} stroke="currentColor" strokeOpacity=".35" />
        <path d="M87 280 L104 280 L102 315 L80 315 Z" fill={fill("Ankle or foot")} stroke="currentColor" strokeOpacity=".35" />
        <path d="M116 280 L134 280 L140 315 L118 315 Z" fill={fill("Ankle or foot")} stroke="currentColor" strokeOpacity=".35" />
        <text x="110" y="327" fill="currentColor" textAnchor="middle" fontSize="9">Front view · approximate regions</text>
      </svg>
      <ul className="pain-map__legend">{PAIN_AREAS.filter((area) => counts.has(area)).map((area) => <li key={area}><span className="pain-map__swatch" />{area}<strong>{counts.get(area)}</strong></li>)}</ul>
    </div>}
  </section>;
}

export function PlayerHistory({ player, history, loading, error, onClose }: {
  player: Player; history: HistoryPoint[] | null; loading: boolean; error: string | null; onClose: () => void;
}) {
  const painCount = history?.filter((point) => point.pain).length ?? 0;
  return <div className="panel player-detail">
    <div className="player-detail__head"><div><p className="section-title">Athlete history</p><h2 className="player-detail__name">{player.name}</h2><p className="player-detail__meta">{history?.length ?? 0} dates with records</p></div><button className="close-btn" onClick={onClose}>Close</button></div>
    {loading && <p className="empty-note" role="status">Loading history…</p>}
    {error && <div className="form-error" role="alert">{error}</div>}
    {!loading && !error && history !== null && (history.length === 0 ? <p className="empty-note">No training or check-in records yet.</p> : <>
      <div className="history-summary"><span><strong>{history.length}</strong> recorded dates</span><span><strong>{history.reduce((sum, point) => sum + point.session_count, 0)}</strong> sessions</span><span><strong>{painCount}</strong> dates with pain reports</span></div>
      <TrendChart title="Daily training load" points={history} value={(p) => p.session_count ? p.session_load : null} colour="var(--accent)" unit="load" note="Load is session duration × perceived effort (RPE). Sessions on one date are combined." />
      <TrendChart title="Daily self-reported wellness" points={history} value={(p) => p.wellness_score ?? null} colour="var(--stable)" unit="/ 5" note="Mean of the four check-in answers on dates with check-ins. All four scores are oriented so higher is more positive; a soreness score of 5 means not sore. Interpret in context." />
      <PainRegionMap points={history} />
      <h3>Record timeline</h3>
      <ol className="history-list">{history.map((point) => <li key={point.date} data-level={point.level}>
        <span className="history-list__date">{point.date}</span><span className="history-list__level">{LEVEL_LABEL[point.level] ?? point.level}</span>
        <span className="history-list__load">{point.session_count ? point.session_load + " load · " + point.session_count + " session(s)" : "Check-in only"}</span>
        {point.pain && <p className="history-list__pain">Pain reported: {point.pain_area ?? "area not specified"}{point.pain_acknowledged ? " · acknowledged by coach" : " · awaiting coach acknowledgement"}</p>}
        {point.reasons.length > 0 && <p>{point.reasons[0]}</p>}
      </li>)}</ol>
    </>)}
  </div>;
}
