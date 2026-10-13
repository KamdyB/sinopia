export interface SessionPayload {
  player_id: string;
  date_str: string;
  duration_minutes: number;
  rpe: number;
}

export interface StatusResponse {
  player_id: string;
  code: string;
  level: string;
  reasons: string[];
  numbers: Record<string, number | boolean>;
  previous_level: string | null;
}

export interface AthleteStatus {
  player_id: string;
  code: string;
  level: string;
  reasons: string[];
  numbers: Record<string, number | boolean>;
}

export interface Team {
  team_id: string;
  coach_email: string;
  team_name: string;
  sport: string;
  age_band: string;
  composition: string;
  created_date: string;
}

export interface TeamProfilePayload {
  team_name: string;
  sport: string;
  age_band: string;
  composition: string;
}

export interface Player {
  player_id: string;
  code: string;
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
