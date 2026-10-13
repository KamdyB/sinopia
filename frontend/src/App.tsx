// frontend/src/App.tsx
// Coach dashboard for one signed-in coach: one team, athlete codes only,
// every query scoped by the backend to that coach's team. Also hosts the
// no-login demo mode reached with ?demo=1 (or straight from the landing
// page's try the demo button): fake DEMO-* athletes, real scoring engine,
// read-only, no account needed.
import { useCallback, useEffect, useState } from "react";
import { AthleteStatus, HistoryPoint, Player, Team, TeamProfilePayload } from "./types";
import {
  createTeam,
  fetchPlayers,
  fetchTeam,
  fetchTeamStatuses,
  fetchDemoStatuses,
  fetchPlayerHistory,
  registerPlayer,
  signOut,
  storedToken,
} from "./api";
import { SessionEntryForm } from "./SessionEntryForm";
import { PlayerDirectory } from "./PlayerDirectory";
import { PlayerHistory } from "./PlayerHistory";
import { DashboardTable } from "./DashboardTable";
import { Glossary } from "./Glossary";
import { GoogleSignIn } from "./GoogleSignIn";

const TODAY = new Date().toLocaleDateString(undefined, {
  weekday: "long",
  month: "long",
  day: "numeric",
});

const SPORTS = ["football", "basketball", "netball", "rugby", "athletics", "volleyball", "handball", "team-running", "other"];
const AGE_BANDS = ["under-10", "under-12", "under-14", "under-16", "under-18", "mixed-ages", "other"];
const COMPOSITIONS = ["full-squad", "small-squad", "school-club", "community-club", "other"];

type Screen = "signin" | "team-setup" | "dashboard";

function TeamSetup({ onReady }: { onReady: () => void }) {
  const [teamName, setTeamName] = useState("");
  const [sport, setSport] = useState(SPORTS[0]);
  const [ageBand, setAgeBand] = useState(AGE_BANDS[2]);
  const [composition, setComposition] = useState(COMPOSITIONS[0]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!teamName.trim()) {
      setError("Give the team a name.");
      return;
    }
    setSaving(true);
    setError(null);
    const profile: TeamProfilePayload = {
      team_name: teamName.trim(),
      sport,
      age_band: ageBand,
      composition,
    };
    try {
      await createTeam(profile);
      onReady();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the team.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form className="panel team-setup" onSubmit={handleCreate}>
      <p className="section-title">Create your team</p>
      <p className="empty-note">
        One coach account owns one team. Every query in the app is scoped to
        this team on the server side.
      </p>
      <div className="field-row">
        <div className="field-group">
          <label className="field-group__label" htmlFor="team-name">Team name</label>
          <input
            id="team-name"
            type="text"
            value={teamName}
            placeholder="e.g. Thursday training squad"
            onChange={(e) => setTeamName(e.target.value)}
          />
        </div>
        <div className="field-group">
          <label className="field-group__label" htmlFor="team-sport">Sport</label>
          <select id="team-sport" value={sport} onChange={(e) => setSport(e.target.value)}>
            {SPORTS.map((s) => <option key={s} value={s}>{s.replace("-", " ")}</option>)}
          </select>
        </div>
        <div className="field-group">
          <label className="field-group__label" htmlFor="team-age">Age band</label>
          <select id="team-age" value={ageBand} onChange={(e) => setAgeBand(e.target.value)}>
            {AGE_BANDS.map((a) => <option key={a} value={a}>{a.replace("-", " ")}</option>)}
          </select>
        </div>
        <div className="field-group">
          <label className="field-group__label" htmlFor="team-comp">Composition</label>
          <select id="team-comp" value={composition} onChange={(e) => setComposition(e.target.value)}>
            {COMPOSITIONS.map((c) => <option key={c} value={c}>{c.replace("-", " ")}</option>)}
          </select>
        </div>
      </div>
      <button className="record-btn" type="submit" disabled={saving}>
        {saving ? "Creating..." : "Create team"}
      </button>
      {error && <div className="form-error">{error}</div>}
    </form>
  );
}

export default function App() {
  const demoStart = new URLSearchParams(window.location.search).has("demo");
  const [demo, setDemo] = useState(demoStart);
  const [signedIn, setSignedIn] = useState<boolean>(() => Boolean(storedToken()));
  const [team, setTeam] = useState<Team | null>(null);
  const [teamLoaded, setTeamLoaded] = useState(false);
  const [players, setPlayers] = useState<Player[]>([]);
  const [statuses, setStatuses] = useState<AthleteStatus[]>([]);
  const [detailId, setDetailId] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryPoint[] | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);

  const loadTeam = useCallback(async () => {
    try {
      const t = await fetchTeam();
      setTeam(t);
    } catch {
      setTeam(null);
    } finally {
      setTeamLoaded(true);
    }
  }, []);

  useEffect(() => {
    if (!signedIn || demo) {
      setTeamLoaded(true);
      return;
    }
    loadTeam();
  }, [signedIn, demo, loadTeam]);

  useEffect(() => {
    if (demo) {
      fetchDemoStatuses()
        .then(setStatuses)
        .catch(() => setStatuses([]));
      return;
    }
    if (!signedIn || team === null) return;
    fetchPlayers()
      .then((list) => setPlayers(list))
      .catch(() => setPlayers([]));
    fetchTeamStatuses()
      .then((list) => setStatuses(list))
      .catch(() => setStatuses([]));
  }, [demo, signedIn, team]);

  useEffect(() => {
    if (!detailId) {
      setHistory(null);
      setHistoryError(null);
      return;
    }
    let cancelled = false;
    setHistoryLoading(true);
    setHistoryError(null);
    (demo
      ? import("./api").then(({ fetchDemoHistory }) => fetchDemoHistory(detailId))
      : import("./api").then(({ fetchPlayerHistory }) => fetchPlayerHistory(detailId))
    )
      .then((points) => { if (!cancelled) setHistory(points); })
      .catch(() => {
        if (!cancelled) setHistoryError("Could not load this athlete's history.");
      })
      .finally(() => { if (!cancelled) setHistoryLoading(false); });
    return () => { cancelled = true; };
  }, [detailId]);

  const refreshStatuses = async () => {
    if (demo) {
      setStatuses(await fetchDemoStatuses().catch(() => []));
      return;
    }
    try {
      setStatuses(await fetchTeamStatuses());
    } catch {
      setStatuses([]);
    }
  };

  const handleAddPlayer = async (code: string) => {
    await registerPlayer(code);
    setPlayers(await fetchPlayers());
    await refreshStatuses();
  };

  const handleSignOut = () => {
    signOut();
    setSignedIn(false);
    setTeam(null);
    setPlayers([]);
    setStatuses([]);
    setDetailId(null);
  };

  const detailPlayer = players.find((p) => p.player_id === detailId) ?? null;

  // ---- Screens ----

  if (demo) {
    return (
      <div className="page">
        <div className="header-row">
          <div>
            <p className="eyebrow">Demo mode</p>
            <h1 className="display-title">Fake athletes, real rules engine</h1>
            <p className="empty-note">
              Read-only demo with fake codes, still no account. Nothing here
              touches real teams.
            </p>
          </div>
          <p className="today-date">{TODAY}</p>
        </div>
        <div className="dashboard">
          <div>
            <PlayerDirectory players={[]} onAdd={async () => {}} demo />
            <div className="panel">
              <p className="section-title">Demo status</p>
              {statuses.length === 0 ? (
                <p className="empty-note">Loading demo data...</p>
              ) : (
                <DashboardTable entries={statuses} onSelect={setDetailId} />
              )}
            </div>
          </div>
          <div>
            <div className="panel demo-panel">
              <p className="section-title">What you can try signed in</p>
              <p className="empty-note">
                The real tool adds log session, athlete check-in links that
                open without an account, and a full history per athlete.
              </p>
              <div className="demo-exit-row">
                <a
                  className="record-btn demo-link"
                  href={`${window.location.origin}/?demo=0`}
                >Start with a real team</a>
                <button
                  className="record-btn demo-link"
                  type="button"
                  onClick={() => setDemo(false)}
                >Exit demo</button>
              </div>
            </div>
            <hr className="rule" />
            <Glossary />
          </div>
        </div>
        <p className="disclaimer">
          Not a medical tool. Statuses open a conversation and never diagnose
          anything; pain always points to a physiotherapist or doctor.
        </p>
      </div>
    );
  }

  if (!signedIn) {
    return (
      <div className="page signin-page">
        <div className="header-row">
          <div>
            <p className="eyebrow">Sinopia</p>
            <h1 className="display-title">Coach tool</h1>
          </div>
        </div>
        <GoogleSignIn onSignedIn={() => setSignedIn(true)} />
        <hr className="rule" />
        <div className="panel">
          <p className="section-title">Just looking around?</p>
          <p className="empty-note">
            The demo needs no account: fake athletes with codes like
            DEMO-A1, run through the same rules engine the real tool uses,
            read-only.
          </p>
          <button className="record-btn demo-link" type="button" onClick={() => setDemo(true)}>
            Try the demo
          </button>
        </div>
      </div>
    );
  }

  if (!teamLoaded) {
    return (
      <div className="page">
        <p className="empty-note">Loading your team...</p>
      </div>
    );
  }

  if (team === null) {
    return (
      <div className="page signin-page">
        <div className="header-row">
          <div>
            <p className="eyebrow">Sinopia</p>
            <h1 className="display-title">Set up in one step</h1>
          </div>
          <button className="record-btn demo-link" type="button" onClick={handleSignOut}>
            Sign out
          </button>
        </div>
        <TeamSetup onReady={loadTeam} />
      </div>
    );
  }

  return (
    <div className="page">
      <div className="header-row">
        <div>
          <p className="eyebrow">Sinopia</p>
          <h1 className="display-title">{team.team_name}</h1>
          <p className="empty-note">
            {team.sport.replace("-", " ")} · {team.age_band.replace("-", " ")}
          </p>
        </div>
        <button className="record-btn demo-link" type="button" onClick={handleSignOut}>
          Sign out
        </button>
      </div>
      <div className="dashboard">
        <div>
          {detailPlayer && (
            <PlayerHistory
              player={detailPlayer}
              history={history}
              loading={historyLoading}
              error={historyError}
              onClose={() => setDetailId(null)}
            />
          )}
          <PlayerDirectory players={players} onAdd={handleAddPlayer} />
          <div className="panel">
            <p className="section-title">Team status</p>
            {statuses.length === 0 ? (
              <p className="empty-note">
                No athletes registered yet. Add each athlete's code once in the directory.
              </p>
            ) : (
              <DashboardTable entries={statuses} onSelect={setDetailId} />
            )}
          </div>
        </div>
        <div>
          <SessionEntryForm players={players} onScored={refreshStatuses} />
          <hr className="rule" />
          <Glossary />
        </div>
      </div>
      <p className="disclaimer">
        Not a medical tool. Sinopia raises a flag for a conversation; it
        never diagnoses. Pain reported during check-ins always points to a
        physiotherapist or doctor, regardless of load.
      </p>
    </div>
  );
}
