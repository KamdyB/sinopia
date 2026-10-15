// frontend/src/api.ts
import { AthleteStatus, CheckinPayload, HistoryPoint, Player, SessionPayload, StatusResponse, TeamType } from "./types";
const API_BASE = (import.meta.env.VITE_API_BASE || "/api").replace(/\/+$/, "");
async function parseError(res: Response): Promise<Error> {
  const body = (await res.json().catch(() => null)) as { detail?: unknown } | null;
  return new Error(typeof body?.detail === "string" ? body.detail : `Request failed (${res.status}). Please try again.`);
}
async function post<T>(path: string, payload: unknown): Promise<T> {
  let res: Response;
  try { res = await fetch(`${API_BASE}${path}`, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload),credentials:"include"}); }
  catch { throw new Error("Could not reach Sinopia. Check your connection and try again."); }
  if (!res.ok) throw await parseError(res);
  return res.status === 204 ? undefined as T : res.json();
}
async function get<T>(path: string): Promise<T> {
  let res: Response;
  try { res = await fetch(`${API_BASE}${path}`, {credentials:"include"}); }
  catch { throw new Error("Could not reach Sinopia. Check your connection and try again."); }
  if (!res.ok) throw await parseError(res);
  return res.json();
}
export async function logSession(payload: SessionPayload): Promise<StatusResponse> { return post("/sessions",payload); }
export async function registerPlayer(name:string, teamType:TeamType):Promise<Player>{return post("/players",{name,team_type:teamType});}
export async function fetchPlayers(teamType:TeamType):Promise<Player[]>{return get(`/players?team_type=${encodeURIComponent(teamType)}`);}
export async function fetchPlayer(playerId:string):Promise<Player>{return get(`/players/${encodeURIComponent(playerId)}`);}
export async function fetchCheckinPlayer(token:string):Promise<Player>{return get(`/check-in/${encodeURIComponent(token)}`);}
export async function fetchPlayerHistory(playerId:string):Promise<HistoryPoint[]>{return get(`/players/${encodeURIComponent(playerId)}/history`);}
export async function fetchTeamStatuses(teamType:TeamType):Promise<AthleteStatus[]>{return get(`/statuses?team_type=${encodeURIComponent(teamType)}`);}
export async function submitCheckin(payload:CheckinPayload):Promise<void>{await post("/checkins",payload);}

export async function signOut(): Promise<void> { await post("/auth/logout", {}); }
