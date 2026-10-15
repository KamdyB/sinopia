// frontend/src/types.ts
export interface SessionPayload {
  player_id: string;
  date_str: string;
  duration_minutes: number;
  rpe: number;
}

export interface StatusResponse {
  player_id: string;
  level: string;
  reasons: string[];
  numbers: Record<string, number | boolean>;
  previous_level: string | null;
}

export interface AthleteStatus {
  player_id: string;
  name: string;
  level: string;
  reasons: string[];
  numbers: Record<string, number | boolean>;
}

export type TeamType = "girls" | "boys" | "mixed";

export interface Player {
  player_id: string;
  name: string;
  team_type: TeamType;
  registered_date: string;
}

export interface HistoryPoint {
  date: string;
  session_load: number;
  session_count: number;
  level: string;
  reasons: string[];
  numbers: Record<string, number | boolean>;
  pain: boolean;
  pain_area: string | null;
  pain_acknowledged: boolean;
  wellness_score: number | null;
}

export interface CheckinPayload {
  token: string;
  rpe?: number;
  sleep: number;
  energy: number;
  soreness: number;
  stress: number;
  pain: boolean;
  pain_area?: string;
}

export interface OpenTeamSession {
  team_id: string;
  session_date: string;
  duration_minutes: number;
  is_open: boolean;
  created_at: string;
}

export interface CheckinValidationResponse {
  valid: boolean;
  session_open: boolean;
  session_date: string | null;
  session_duration_minutes: number | null;
}
