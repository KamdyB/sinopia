// landing/src/engine.ts
// Load-only demonstration matching backend/scoring/load_calculator.py and
// backend/scoring/athlete_status.py. Wellness and pain flags are not simulated.
export interface DemoSession { date: string; minutes: number; rpe: number; }
export interface Assessment {
  date: string;
  sessionLoad: number;
  weeklyLoad: number;
  baseline: number;
  level: "building" | "act" | "ok";
  weeksAvailable: number;
}
const DAY_MS = 24 * 60 * 60 * 1000;
const BASELINE_WEEKS = 4;
const MIN_BASELINE_WEEKS = 3;
const LOAD_JUMP_RATIO = 1.5;
function toUtc(iso: string): number { return Date.parse(iso + "T00:00:00Z"); }
function toIso(ms: number): string { return new Date(ms).toISOString().slice(0, 10); }
export function sessionLoad(session: DemoSession): number { return session.minutes * session.rpe; }
function dailyLoads(sessions: DemoSession[]): Map<string, number> {
  const daily = new Map<string, number>();
  for (const session of sessions) {
    daily.set(session.date, (daily.get(session.date) ?? 0) + sessionLoad(session));
  }
  return daily;
}
function weeklyLoad(daily: Map<string, number>, asOfMs: number): number {
  let total = 0;
  for (let day = 0; day < 7; day++) total += daily.get(toIso(asOfMs - day * DAY_MS)) ?? 0;
  return total;
}
function weeksTracked(daily: Map<string, number>, asOfMs: number): number {
  if (daily.size === 0) return 0;
  const first = Math.min(...Array.from(daily.keys(), toUtc));
  return Math.max(0, Math.floor((asOfMs - first) / (7 * DAY_MS)));
}
function rollingBaseline(daily: Map<string, number>, asOfMs: number): number {
  if (daily.size === 0) return 0;
  const first = Math.min(...Array.from(daily.keys(), toUtc));
  const windows: number[] = [];
  for (let week = 1; week <= BASELINE_WEEKS; week++) {
    const end = asOfMs - 7 * week * DAY_MS;
    if (end - 6 * DAY_MS < first) break;
    windows.push(weeklyLoad(daily, end));
  }
  return windows.length ? windows.reduce((sum, value) => sum + value, 0) / windows.length : 0;
}
export function assess(sessions: DemoSession[], asOf: string): Assessment {
  const daily = dailyLoads(sessions);
  const asOfMs = toUtc(asOf);
  const current = [...sessions].filter((session) => session.date <= asOf)
    .sort((a, b) => b.date.localeCompare(a.date))[0];
  const weekly = weeklyLoad(daily, asOfMs);
  const baseline = rollingBaseline(daily, asOfMs);
  const weeksAvailable = weeksTracked(daily, asOfMs);
  const level: Assessment["level"] =
    weeksAvailable < MIN_BASELINE_WEEKS || baseline <= 0 ? "building" :
    weekly > baseline * LOAD_JUMP_RATIO ? "act" : "ok";
  return { date: asOf, sessionLoad: current ? sessionLoad(current) : 0, weeklyLoad: weekly, baseline, level, weeksAvailable };
}
export function walkForward(sessions: DemoSession[]): Assessment[] {
  const ordered = [...sessions].sort((a, b) => a.date.localeCompare(b.date));
  return ordered.map((session, index) => assess(ordered.slice(0, index + 1), session.date));
}
export const DEMO_PLAYER = "Athlete code A01";
export const DEMO_SESSIONS: DemoSession[] = [
  { date: "2026-01-01", minutes: 60, rpe: 5 },
  { date: "2026-01-04", minutes: 60, rpe: 5 },
  { date: "2026-01-08", minutes: 60, rpe: 5 },
  { date: "2026-01-11", minutes: 60, rpe: 5 },
  { date: "2026-01-15", minutes: 60, rpe: 5 },
  { date: "2026-01-18", minutes: 60, rpe: 5 },
  { date: "2026-01-22", minutes: 60, rpe: 5 },
  { date: "2026-01-25", minutes: 60, rpe: 5 },
  { date: "2026-01-29", minutes: 60, rpe: 5 },
  { date: "2026-02-01", minutes: 60, rpe: 5 },
  { date: "2026-02-05", minutes: 60, rpe: 5 },
  { date: "2026-02-08", minutes: 60, rpe: 5 },
  { date: "2026-02-12", minutes: 60, rpe: 5 },
  { date: "2026-02-15", minutes: 60, rpe: 5 },
  { date: "2026-02-19", minutes: 60, rpe: 5 },
  { date: "2026-02-22", minutes: 60, rpe: 5 },
  { date: "2026-02-26", minutes: 120, rpe: 8 },
];
