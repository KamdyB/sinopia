// frontend/src/App.tsx
import { useEffect, useState } from "react";
import { AthleteStatus, HistoryPoint, Player, TeamType } from "./types";
import { acknowledgePain, createCheckinToken, deletePlayer, exportTeamData, fetchCoachSession, fetchPlayers, fetchTeamStatuses, registerPlayer } from "./api";
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
    import("./api")
      .then(({ fetchPlayerHistory }) => fetchPlayerHistory(detailId))
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

  return (
    <div className="page">
      <div className="header-row">
        <div>
          <p className="eyebrow">Sinopia by KamdyB</p>
          <h1 className="display-title">{TEAM_TITLES[teamType]}</h1>
        </div>
        <div>
          <p className="today-date">{TODAY}</p>
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
          <PlayerDirectory players={players} onAdd={handleAddPlayer} onCreateCheckinLink={handleCreateCheckinLink} onDeletePlayer={handleDeletePlayer} />
          <div className="panel">
            <p className="section-title">Team status</p>
            {!dataLoading && !dataError && statuses.length === 0 ? (
              <p className="empty-note">
                No athletes registered yet. Add each athlete once in the directory.
              </p>
            ) : !dataLoading && !dataError ? (
              <DashboardTable entries={statuses} onSelect={setDetailId} onAcknowledgePain={handleAcknowledgePain} />
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
