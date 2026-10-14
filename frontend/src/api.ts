// frontend/src/api.ts
import {
  AthleteStatus,
  CheckinPayload,
  HistoryPoint,
  Player,
  SessionPayload,
  StatusResponse,
  TeamType,
} from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE ?? "http://localhost:8000").replace(/\/$/, "");

async function parseError(res: Response): Promise<Error> {
  const body = (await res.json().catch(() => null)) as { detail?: unknown } | null;
  const detail =
    typeof body?.detail === "string" ? body.detail : `Request failed: ${res.status}`;
  return new Error(detail);
}

async function post<T>(path: string, payload: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Sinopia-Request": "1",
    },
    credentials: "include",
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw await parseError(res);
  return res.json();
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "X-Sinopia-Request": "1" },
  });
  if (!res.ok) throw await parseError(res);
  return res.json();
}

export async function logSession(payload: SessionPayload): Promise<StatusResponse> {
  return post<StatusResponse>("/sessions", payload);
}

export async function registerPlayer(name: string, teamType: TeamType): Promise<Player> {
  return post<Player>("/players", { name, team_type: teamType, consent_confirmed: true });
}

export async function fetchPlayers(teamType: TeamType): Promise<Player[]> {
  return get<Player[]>(`/players?team_type=${encodeURIComponent(teamType)}`);
}

export async function fetchPlayer(playerId: string): Promise<Player> {
  return get<Player>(`/players/${encodeURIComponent(playerId)}`);
}

export async function createCheckinToken(playerId: string): Promise<string> {
  const result = await post<{ token: string }>(
    `/players/${encodeURIComponent(playerId)}/checkin-token`, {},
  );
  return result.token;
}

export async function validateCheckinToken(token: string): Promise<void> {
  await get<{ valid: boolean }>(`/checkin/${encodeURIComponent(token)}`);
}

export async function fetchPlayerHistory(playerId: string): Promise<HistoryPoint[]> {
  return get<HistoryPoint[]>(`/players/${encodeURIComponent(playerId)}/history`);
}

export async function fetchTeamStatuses(teamType: TeamType): Promise<AthleteStatus[]> {
  return get<AthleteStatus[]>(`/statuses?team_type=${encodeURIComponent(teamType)}`);
}

export async function submitCheckin(payload: CheckinPayload): Promise<void> {
  await post<unknown>("/checkins", payload);
}

export async function acknowledgePain(playerId: string): Promise<void> {
  await post<unknown>(`/players/${encodeURIComponent(playerId)}/acknowledge-pain`, {});
}
