// frontend/src/App.tsx
import { useEffect, useState } from "react";
import { AthleteStatus, HistoryPoint, Player, TeamType } from "./types";
import { acknowledgePain, createCheckinToken, deletePlayer, exportTeamData, fetchPlayers, fetchTeamStatuses, registerPlayer } from "./api";
import { SessionEntryForm } from "./SessionEntryForm";
import { PlayerDirectory } from "./PlayerDirectory";
import { PlayerHistory } from "./PlayerHistory";
import { DashboardTable } from "./DashboardTable";
import { Glossary } from "./Glossary";

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
  const [teamType, setTeamType] = useState<TeamType>(() => {
    document.documentElement.dataset.team = "girls";
    return "girls";
  });
  const [players, setPlayers] = useState<Player[]>([]);
  const [statuses, setStatuses] = useState<AthleteStatus[]>([]);
  const [detailId, setDetailId] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryPoint[] | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchPlayers(teamType)
      .then((list) => { if (!cancelled) setPlayers(list); })
      .catch(() => { if (!cancelled) setPlayers([]); });
    fetchTeamStatuses(teamType)
      .then((list) => { if (!cancelled) setStatuses(list); })
      .catch(() => { if (!cancelled) setStatuses([]); });
    return () => { cancelled = true; };
  }, [teamType]);

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
    } catch {
      setStatuses([]);
    }
  };

  const handleTeamChange = (next: TeamType) => {
    document.documentElement.dataset.team = next;
    setTeamType(next);
    setDetailId(null); // never carry an athlete from one team into another
  };

  const handleAddPlayer = async (name: string) => {
    await registerPlayer(name, teamType);
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
          <label className="team-type">
            Team
            <select
              value={teamType}
              onChange={(e) => handleTeamChange(e.target.value as TeamType)}
            >
              <option value="girls">Girls</option>
              <option value="boys">Boys</option>
              <option value="mixed">Mixed</option>
            </select>
          </label>
        </div>
        <div>
          <p className="today-date">{TODAY}</p>
          <button type="button" className="copy-link" onClick={() => void handleExport("csv")}>Export CSV</button>
          <button type="button" className="copy-link" onClick={() => void handleExport("json")}>Export JSON</button>
        </div>
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
          <PlayerDirectory players={players} onAdd={handleAddPlayer} onCreateCheckinLink={handleCreateCheckinLink} onDeletePlayer={handleDeletePlayer} />
          <div className="panel">
            <p className="section-title">Team status</p>
            {statuses.length === 0 ? (
              <p className="empty-note">
                No athletes registered yet. Add each athlete once in the directory.
              </p>
            ) : (
              <DashboardTable entries={statuses} onSelect={setDetailId} onAcknowledgePain={handleAcknowledgePain} />
            )}
          </div>
        </div>
        <div>
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
