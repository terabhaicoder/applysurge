export interface Application {
  id: string;
  user_id: string;
  job_id: string;
  job?: {
    title: string;
    company: string;
    company_logo?: string;
    location: string;
  };
  status: ApplicationStatus;
  applied_via: 'agent' | 'manual';
  resume_used?: string;
  cover_letter?: string;
  notes?: string;
  response_received: boolean;
  response_date?: string;
  interview_date?: string;
  match_score?: number;
  logs: ApplicationLog[];
  screenshots: ApplicationScreenshot[];
  created_at: string;
  updated_at: string;
}

export type ApplicationStatus =
  | 'queued'
  | 'in_progress'
  | 'applied'
  | 'viewed'
  | 'shortlisted'
  | 'interview_scheduled'
  | 'interviewed'
  | 'offered'
  | 'accepted'
  | 'rejected'
  | 'withdrawn'
  | 'failed';

export interface ApplicationLog {
  id: string;
  application_id: string;
  action: string;
  details?: string;
  screenshot_url?: string;
  created_at: string;
}

export interface ApplicationScreenshot {
  id: string;
  application_id: string;
  url: string;
  step: string;
  created_at: string;
}

export interface ApplicationFilters {
  status?: ApplicationStatus[];
  applied_via?: 'agent' | 'manual';
  search?: string;
  date_from?: string;
  date_to?: string;
  sort_by?: 'created_at' | 'status' | 'match_score';
  sort_order?: 'asc' | 'desc';
  page?: number;
  per_page?: number;
}
