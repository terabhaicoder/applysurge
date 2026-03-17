export type AgentState = 'idle' | 'running' | 'paused' | 'error' | 'stopped' | 'enabled';

export interface AgentStatus {
  is_running: boolean;
  is_paused: boolean;
  status: AgentState;
  current_task?: string | null;
  applications_made_today: number;
  applications_limit_today: number;
  applications_total: number;
  applications_limit_total: number;
  session_start_time?: string | null;
  last_activity_at?: string | null;
  errors_count: number;
  queue_size: number;
}

export interface AgentSettings {
  id: string;
  user_id: string;
  max_applications_per_day: number;
  cooldown_seconds: number;
  auto_apply: boolean;
  cover_letter_enabled: boolean;
  preferred_apply_time_start: string | null;
  preferred_apply_time_end: string | null;
  skip_easy_apply: boolean;
  require_salary_info: boolean;
  custom_answers: Record<string, unknown> | null;
  created_at: string;
  updated_at?: string;
}

export interface AgentLog {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  details?: Record<string, unknown>;
}

export interface QueueItem {
  id: string;
  job_id: string;
  job_title: string;
  company: string;
  match_score: number;
  priority: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  added_at: string;
}
