export interface Job {
  id: string;
  title: string;
  company: string;
  company_logo?: string;
  company_logo_url?: string;
  company_size?: string;
  company_industry?: string;
  location: string;
  remote_type?: string;
  is_remote?: boolean;
  job_type: string;
  experience_level: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  salary_text?: string;
  description: string;
  description_html?: string;
  requirements?: string[];
  responsibilities?: string[];
  qualifications?: string[];
  nice_to_have?: string[];
  skills?: string[];
  preferred_skills?: string[];
  technologies?: string[];
  benefits?: string[];
  source: string;
  source_url: string;
  applicant_count?: number;
  is_easy_apply?: boolean;
  is_saved?: boolean;
  is_hidden?: boolean;
  is_queued?: boolean;
  // Backend returns posted_at, alias for compatibility
  posted_date?: string;
  posted_at?: string;
  deadline?: string;
  is_active?: boolean;
  match_score?: number;
  match_reasoning?: string;
  match_reasons?: string[];
  strengths?: string[];
  gaps?: string[];
  matched_skills?: string[];
  missing_skills?: string[];
  created_at: string;
  updated_at?: string;
}

export interface JobMatch {
  job_id: string;
  score: number;
  reasons: string[];
  missing_skills: string[];
  matching_skills: string[];
}

export interface JobFilters {
  search?: string;
  job_type?: string[];
  experience_level?: string[];
  location?: string;
  salary_min?: number;
  salary_max?: number;
  source?: string[];
  min_match_score?: number;
  sort_by?: 'match_score' | 'posted_date' | 'salary';
  sort_order?: 'asc' | 'desc';
  page?: number;
  per_page?: number;
}
