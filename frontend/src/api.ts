// frontend/src/api.ts
import {
  AthleteStatus,
  CheckinPayload,
  HistoryPoint,
  Player,
  SessionPayload,
  StatusResponse,
  Team,
  TeamProfilePayload,
} from "./types";

// The backend URL. In production set VITE_API_URL to the Render URL.
// Empty falls back to localhost for local development.
const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) || "http://localhost:8000";

const TOKEN_KEY = "sinopia_id_token";

export function storeToken(token: string | null): void {
  if (token) {
    sessionStorage.setItem(TOKEN_KEY, token);
  } else {
    sessionStorage.removeItem(TOKEN_KEY);
  }
}

export function storedToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function signIn(token: string): void {
  storeToken(token);
  window.dispatchEvent(new Event("sinopia:signin"));
}

export function signOut(): void {
  storeToken(null);
  // Ask Google Identity Services to drop any remembered session.
  const g = (window as unknown as { google?: { accounts?: { id?: { disableAutoSelect?: () => void } } } }).google;
  g?.accounts?.id?.disableAutoSelect?.();
}

async function parseError(res: Response): Promise<Error> {
  const body = (await res.json().catch(() => null)) as { detail?: unknown } | null;
  const detail =
    typeof body?.detail === "string" ? body.detail : `Request failed: ${res.status}`;
  // Dropped or revoked sign-in: surface it as a sign-out.
  if (res.status === 401) {
    signOut();
  }
  return new Error(detail);
}

function headers(withAuth: boolean): HeadersInit {
  const base: Record<string, string> = { "Content-Type": "application/json" };
  const token = storedToken();
  if (withAuth && token) {
    base.Authorization = `Bearer ${token}`;
  }
  return base;
}

async function request<T>(
  method: string,
  path: string,
  payload: unknown | undefined,
  auth = true,
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: headers(auth),
    ...(payload !== undefined ? { body: JSON.stringify(payload) } : {}),
  });
  if (!res.ok) throw await parseError(res);
  return res.json();
}

async function post<T>(path: string, payload: unknown, auth = true): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: headers(auth),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw await parseError(res);
  return res.json();
}

async function get<T>(path: string, auth = true): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: headers(auth),
  });
  if (!res.ok) throw await parseError(res);
  return res.json();
}

// ---- Teams and sign-in ----

export async function fetchTeam(): Promise<Team | null> {
  const body = await get<{ has_team: boolean; team: Team | null }>("/teams/me");
  return body.team;
}

export async function createTeam(profile: TeamProfilePayload): Promise<Team> {
  return post<Team>("/teams", profile);
}

export async function updateTeamProfile(profile: Partial<TeamProfilePayload>): Promise<Team> {
  return request<Team>("PATCH", "/teams/me/profile", profile);
}

// ---- Coach tool ----

export async function logSession(payload: SessionPayload): Promise<StatusResponse> {
  return post<StatusResponse>("/sessions", payload);
}

export async function registerPlayer(code: string): Promise<Player> {
  return post<Player>("/players", { code });
}

export async function fetchPlayers(): Promise<Player[]> {
  return get<Player[]>("/players");
}

export async function fetchPlayer(playerId: string): Promise<Player> {
  return get<Player>(`/players/${encodeURIComponent(playerId)}`, false); // public check-in link
}

export async function fetchPlayerHistory(playerId: string): Promise<HistoryPoint[]> {
  return get<HistoryPoint[]>(`/players/${encodeURIComponent(playerId)}/history`);
}

export async function fetchTeamStatuses(): Promise<AthleteStatus[]> {
  return get<AthleteStatus[]>("/statuses");
}

export async function submitCheckin(payload: CheckinPayload): Promise<void> {
  await post<unknown>("/checkins", payload, false); // public check-in link
}

// ---- No-login demo mode: fake DEMO-* codes through the real engine ----

export interface DemoStatus {
  player_id: string;
  code: string;
  level: string;
  reasons: string[];
  numbers: Record<string, number | boolean>;
}

export async function fetchDemoStatuses(): Promise<DemoStatus[]> {
  return get<DemoStatus[]>("/demo/statuses", false);
}

export async function fetchDemoHistory(code: string): Promise<HistoryPoint[]> {
  return get<HistoryPoint[]>(`/demo/athletes/${encodeURIComponent(code)}/history`, false);
}
