export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
  is_verified: boolean;
  is_active: boolean;
  subscription_tier: 'free' | 'pro' | 'enterprise';
  created_at: string;
  updated_at: string;
}

export interface Profile {
  id: string;
  user_id: string;
  headline?: string;
  summary?: string;
  location?: string;
  phone?: string;
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  years_of_experience?: number;
  current_company?: string;
  current_title?: string;
  skills: string[];
  education: Education[];
  experience: Experience[];
}

export interface Education {
  id: string;
  institution: string;
  degree: string;
  field_of_study: string;
  start_date: string;
  end_date?: string;
  gpa?: number;
  description?: string;
}

export interface Experience {
  id: string;
  company: string;
  title: string;
  location?: string;
  start_date: string;
  end_date?: string;
  is_current: boolean;
  description?: string;
  skills: string[];
}

export interface Resume {
  id: string;
  user_id: string;
  filename: string;
  file_url: string;
  is_primary: boolean;
  parsed_data?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
