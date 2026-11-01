// frontend/src/App.tsx
import { useEffect, useState } from "react";
import { AthleteStatus, HistoryPoint, Player, TeamType } from "./types";
import { InstallButton } from "./InstallButton";
import { acknowledgePain, createCheckinToken, deletePlayer, exportTeamData, fetchCoachSession, fetchPlayerHistory, fetchPlayers, fetchTeamStatuses, registerPlayer } from "./api";
import { SessionEntryForm } from "./SessionEntryForm";
import { PlayerDirectory } from "./PlayerDirectory";
import { PlayerHistory } from "./PlayerHistory";
import { DashboardTable } from "./DashboardTable";
import { Glossary } from "./Glossary";
import { TeamSessionControl } from "./TeamSessionControl";

const TEAM_TITLES: Record<TeamType, string> = {
  girls: "Girls team status",
  boys: "Boys team status",
  mixed: "Mixed team status",
};

const LEGAL_BASE_URL = (import.meta.env.VITE_LEGAL_BASE_URL ?? (import.meta.env.PROD ? "" : "http://localhost:5174")).replace(/\/$/, "");

const TODAY = new Date().toLocaleDateString(undefined, {
  weekday: "long",
  month: "long",
  day: "numeric",
});

export default function App() {
  const [teamType, setTeamType] = useState<TeamType>("girls");
  const [teamReady, setTeamReady] = useState(false);
  const [players, setPlayers] = useState<Player[]>([]);
  const [statuses, setStatuses] = useState<AthleteStatus[]>([]);
  const [detailId, setDetailId] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryPoint[] | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [dataError, setDataError] = useState<string | null>(null);
  const [dataLoading, setDataLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchCoachSession()
      .then((coach) => {
        if (coach.team_type && !cancelled) {
          setTeamType(coach.team_type);
          document.documentElement.dataset.team = coach.team_type;
          setTeamReady(true);
        }
      })
      .catch(() => { if (!cancelled) setDataError("Could not load your saved team settings."); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!teamReady) return;
    let cancelled = false;
    setDataLoading(true);
    setDataError(null);
    Promise.all([fetchPlayers(teamType), fetchTeamStatuses(teamType)])
      .then(([roster, teamStatuses]) => {
        if (!cancelled) {
          setPlayers(roster);
          setStatuses(teamStatuses);
        }
      })
      .catch(() => {
        if (!cancelled) setDataError("Could not load team records. Check the connection and retry; the data has not been replaced with an empty roster.");
      })
      .finally(() => { if (!cancelled) setDataLoading(false); });
    return () => { cancelled = true; };
  }, [teamType, teamReady]);

  useEffect(() => {
    if (!detailId) {
      setHistory(null);
      setHistoryError(null);
      return;
    }
    let cancelled = false;
    setHistoryLoading(true);
    setHistoryError(null);
    fetchPlayerHistory(detailId)
      .then((points) => { if (!cancelled) setHistory(points); })
      .catch(() => {
        if (!cancelled) setHistoryError("Could not load this athlete's history.");
      })
      .finally(() => { if (!cancelled) setHistoryLoading(false); });
    return () => { cancelled = true; };
  }, [detailId]);

  const refreshStatuses = async () => {
    try {
      setStatuses(await fetchTeamStatuses(teamType));
      setDataError(null);
    } catch {
      setDataError("Could not refresh team status. Existing results may be out of date.");
    }
  };

  const handleAddPlayer = async (name: string, consentConfirmed: boolean) => {
    await registerPlayer(name, teamType, consentConfirmed);
    setPlayers(await fetchPlayers(teamType));
    await refreshStatuses();
  };

  const handleCreateCheckinLink = async (playerId: string) => createCheckinToken(playerId);

  const handleDeletePlayer = async (playerId: string) => {
    await deletePlayer(playerId);
    if (detailId === playerId) setDetailId(null);
    setPlayers(await fetchPlayers(teamType));
    await refreshStatuses();
  };

  const handleAcknowledgePain = async (playerId: string) => {
    await acknowledgePain(playerId);
    await refreshStatuses();
  };

  const handleExport = async (format: "csv" | "json") => {
    setExportError(null);
    try {
      await exportTeamData(format);
    } catch (err) {
      setExportError(err instanceof Error ? err.message : "Could not export team data.");
    }
  };

  const handleScored = () => {
    refreshStatuses();
  };

  const detailPlayer = players.find((p) => p.player_id === detailId) ?? null;
  const statusGroups = [
    { level: "building", label: "Building baseline", colour: "var(--muted)" },
    { level: "ok", label: "OK", colour: "var(--stable)" },
    { level: "watch", label: "Watch", colour: "var(--watch)" },
    { level: "act", label: "Act", colour: "var(--elevated)" },
    { level: "refer", label: "Refer", colour: "var(--elevated)" },
  ].map((group) => ({ ...group, count: statuses.filter((entry) => entry.level === group.level).length }));
  const reviewQueue = statuses
    .filter((entry) => entry.numbers.pain === true || ["watch", "act", "refer"].includes(entry.level))
    .sort((a, b) => {
      const priority = (entry: AthleteStatus) =>
        (entry.numbers.pain === true ? 100 : 0) +
        (entry.level === "refer" ? 30 : entry.level === "act" ? 20 : entry.level === "watch" ? 10 : 0);
      return priority(b) - priority(a) || a.name.localeCompare(b.name);
    })
    .slice(0, 4);

  return (
    <div className="page">
      <div className="header-row">
        <div>
          <p className="eyebrow">Sinopia by KamdyB</p>
          <h1 className="display-title">{TEAM_TITLES[teamType]}</h1>
        </div>
        <div className="header-actions">
          <p className="today-date">{TODAY}</p>
          <InstallButton />
          <button type="button" className="copy-link" onClick={() => void handleExport("csv")}>Export CSV</button>
          <button type="button" className="copy-link" onClick={() => void handleExport("json")}>Export JSON</button>
        </div>
      </div>
      {dataError && <p className="form-error" role="alert">{dataError}</p>}
      {(!teamReady || dataLoading) && <p className="empty-note" role="status">Loading team records…</p>}
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
          <section className="panel" aria-labelledby="team-picture-title">
            <p className="section-title" id="team-picture-title">Team picture</p>
            <p className="empty-note">Select a bar to focus the roster on that recorded status. These are monitoring prompts, not medical conclusions.</p>
            {dataLoading ? <p className="empty-note">Loading team picture…</p> : dataError ? null : statuses.length === 0 ? (
              <p className="empty-note">Your team picture will appear after athletes are registered and status records are available.</p>
            ) : <>
              <div className="team-picture__total"><strong>{statuses.length}</strong><span>athletes with a current status record</span></div>
              <div className="team-picture__bar" role="group" aria-label="Filter team status by category">
                {statusGroups.filter((group) => group.count > 0).map((group) => (
                  <button
                    key={group.level}
                    type="button"
                    title={group.label + ": " + group.count + ". Select to filter the roster."}
                    aria-label={group.label + ": " + group.count + " athletes. Filter roster."}
                    aria-pressed={statusFilter === group.level}
                    onClick={() => setStatusFilter(statusFilter === group.level ? null : group.level)}
                    style={{ width: (group.count / statuses.length * 100) + "%", background: group.colour }}
                  />
                ))}
              </div>
              <div className="team-picture__legend">
                {statusGroups.map((group) => (
                  <button key={group.level} type="button" className="team-picture__key"
                    aria-pressed={statusFilter === group.level}
                    onClick={() => setStatusFilter(statusFilter === group.level ? null : group.level)}>
                    <span style={{ background: group.colour }} />{group.label}<strong>{group.count}</strong>
                  </button>
                ))}
              </div>
              {statusFilter && <p className="team-picture__filter">Showing {statusGroups.find((group) => group.level === statusFilter)?.label} · <button type="button" className="copy-link" onClick={() => setStatusFilter(null)}>Show all statuses</button></p>}
              <div className="team-picture__review">
                <p className="team-picture__review-title">Worth a closer look</p>
                {reviewQueue.length === 0 ? <p className="empty-note">No current watch, act, refer or recorded pain flags in the loaded status records.</p> : reviewQueue.map((entry) => (
                  <div className="team-picture__review-row" key={entry.player_id}>
                    <button type="button" className="status-row__name" onClick={() => setDetailId(entry.player_id)}>{entry.name}</button>
                    <span className="status-row__level" data-level={entry.level}>{entry.numbers.pain === true ? "Pain reported · " : ""}{TEAM_TITLES[teamType].replace(" team status", "")} · {entry.level.toUpperCase()}</span>
                    <button type="button" className="copy-link" onClick={() => setDetailId(entry.player_id)}>Open history</button>
                  </div>
                ))}
              </div>
            </>}
          </section>
          <PlayerDirectory players={players} statuses={statuses} onAdd={handleAddPlayer} onCreateCheckinLink={handleCreateCheckinLink} onDeletePlayer={handleDeletePlayer} />
          <div className="panel">
            <p className="section-title">Team status{statusFilter ? " · " + (statusGroups.find((group) => group.level === statusFilter)?.label ?? statusFilter) : ""}</p>
            {!dataLoading && !dataError && statuses.length === 0 ? (
              <p className="empty-note">
                No athletes registered yet. Add each athlete once in the directory.
              </p>
            ) : !dataLoading && !dataError ? (
              <>
                {statusFilter && <button type="button" className="copy-link" onClick={() => setStatusFilter(null)}>Clear status filter</button>}
                <DashboardTable entries={statusFilter ? statuses.filter((entry) => entry.level === statusFilter) : statuses} onSelect={setDetailId} onAcknowledgePain={handleAcknowledgePain} />
              </>
            ) : null}
          </div>
        </div>
        <div>
          <TeamSessionControl />
          <hr className="rule" />
          <SessionEntryForm players={players} onScored={handleScored} />
          <hr className="rule" />
          <Glossary />
        </div>
      </div>
      {exportError && <p className="form-error">{exportError}</p>}
      <p className="disclaimer">
        Sinopia by KamdyB is a workload-monitoring tool for coaches, not a medical
        device. It does not diagnose, treat, or predict injury. All thresholds are
        provisional and not yet validated, and every flag is a prompt for a coach
        conversation, never a finding. For any health concern, consult a qualified
        medical professional.
      </p>
      <p className="footer-link">
        <a href={LEGAL_BASE_URL}>About Sinopia</a>
        {" · "}<a href={LEGAL_BASE_URL + "/privacy"}>Privacy</a>
        {" · "}<a href={LEGAL_BASE_URL + "/terms"}>Terms</a>
        {" · "}<a href={LEGAL_BASE_URL + "/delete-account"}>Delete account</a>
      </p>
    </div>
  );
}
