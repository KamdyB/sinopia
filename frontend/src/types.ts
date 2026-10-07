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
  level: string;
  reasons: string[];
  numbers: Record<string, number | boolean>;
}

export interface CheckinPayload {
  player_id: string;
  sleep: number;
  energy: number;
  soreness: number;
  stress: number;
  pain: boolean;
  pain_area?: string;
}
