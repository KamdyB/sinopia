// frontend/src/api.ts
import {
  AthleteStatus,
  CheckinPayload,
  CheckinValidationResponse,
  HistoryPoint,
  Player,
  SessionPayload,
  StatusResponse,
  TeamType,
  OpenTeamSession,
} from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE ?? (import.meta.env.PROD ? "/api" : "http://localhost:8000")).replace(/\/$/, "");

async function parseError(res: Response): Promise<Error> {
  const body = (await res.json().catch(async () => ({ detail: await res.text().catch(() => "") }))) as { detail?: unknown } | null;
  const detail = typeof body?.detail === "string" && body.detail.trim()
    ? body.detail.trim().slice(0, 300)
    : `Request failed: ${res.status}`;
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

export async function registerPlayer(name: string, teamType: TeamType, consentConfirmed: boolean): Promise<Player> {
  return post<Player>("/players", { name, team_type: teamType, consent_confirmed: consentConfirmed });
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

export async function validateCheckinToken(token: string): Promise<CheckinValidationResponse> {
  return post<CheckinValidationResponse>("/checkin/validate", { token });
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

export interface CoachSession {
  email: string;
  display_name: string;
  team_id: string;
  team_name: string;
  team_type: TeamType | null;
  needs_onboarding: boolean;
  accepted_at: string | null;
  terms_version: string | null;
  privacy_version: string | null;
  needs_policy_acceptance: boolean;
}

export async function fetchCoachSession(): Promise<CoachSession> {
  return get<CoachSession>("/auth/me");
}

export async function signInWithGoogle(credential: string, turnstileToken?: string, intent: "signup" | "signin" = "signin"): Promise<CoachSession> {
  return post<CoachSession>("/auth/google", { credential, turnstile_token: turnstileToken ?? null, intent });
}

export async function requestEmailSignup(payload: {
  full_name: string;
  email: string;
  turnstile_token: string;
  age_18_or_older: boolean;
  authorised_and_parental_consent_obtained: boolean;
  accept_terms_and_privacy: boolean;
}): Promise<void> {
  await post<unknown>("/auth/email/request", payload);
}

export async function verifyEmailSignup(token: string): Promise<CoachSession> {
  return post<CoachSession>("/auth/email/verify", { token });
}

export async function acceptCoachPolicies(
  age18: boolean,
  authorisedAndConsent: boolean,
  acceptTermsAndPrivacy: boolean,
): Promise<void> {
  await post<unknown>("/auth/accept-policies", {
    age_18_or_older: age18,
    authorised_and_parental_consent_obtained: authorisedAndConsent,
    accept_terms_and_privacy: acceptTermsAndPrivacy,
  });
}

export async function setupCoachTeam(teamName: string, teamType: TeamType): Promise<CoachSession> {
  return post<CoachSession>("/auth/setup-team", { team_name: teamName, team_type: teamType });
}

export async function signOut(): Promise<void> {
  await post<unknown>("/auth/logout", {});
}

export async function deleteCoachAccount(credential: string, turnstileToken?: string): Promise<void> {
  await post<unknown>("/privacy/delete-account", { credential, confirm: true, turnstile_token: turnstileToken ?? null });
}

export async function exportTeamData(format: "csv" | "json"): Promise<void> {
  const res = await fetch(`${API_BASE}/privacy/export?format=${format}`, {
    credentials: "include",
    headers: { "X-Sinopia-Request": "1" },
  });
  if (!res.ok) throw await parseError(res);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = format === "csv" ? "sinopia-team-export.csv" : "sinopia-team-export.json";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export async function deletePlayer(playerId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/players/${encodeURIComponent(playerId)}`, {
    method: "DELETE",
    credentials: "include",
    headers: { "X-Sinopia-Request": "1" },
  });
  if (!res.ok) throw await parseError(res);
}

export async function fetchOpenTeamSession(): Promise<OpenTeamSession | null> {
  const result = await get<{ session: OpenTeamSession | null }>("/team-sessions/current");
  return result.session;
}

export async function openTeamSession(dateStr: string, durationMinutes: number): Promise<OpenTeamSession> {
  return post<OpenTeamSession>("/team-sessions/open", { date_str: dateStr, duration_minutes: durationMinutes });
}

export async function closeTeamSession(): Promise<OpenTeamSession> {
  return post<OpenTeamSession>("/team-sessions/close", {});
}
