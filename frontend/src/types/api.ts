export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
  errors?: Record<string, string[]>;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface AnalyticsData {
  applications_over_time: TimeSeriesData[];
  response_rates: ResponseRateData;
  source_breakdown: SourceBreakdownData[];
  status_distribution: StatusDistributionData[];
  weekly_summary: WeeklySummary;
}

export interface TimeSeriesData {
  date: string;
  count: number;
  label?: string;
}

export interface ResponseRateData {
  total_applied: number;
  responses_received: number;
  interviews_scheduled: number;
  offers_received: number;
  response_rate: number;
  interview_rate: number;
}

export interface SourceBreakdownData {
  source: string;
  count: number;
  percentage: number;
}

export interface StatusDistributionData {
  status: string;
  count: number;
  percentage: number;
}

export interface WeeklySummary {
  applications_this_week: number;
  applications_last_week: number;
  change_percentage: number;
  top_companies: string[];
}

export interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  body: string;
  type: 'follow_up' | 'cold_outreach' | 'thank_you' | 'custom';
  variables: string[];
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmailOutreach {
  id: string;
  template_id: string;
  recipient_email: string;
  recipient_name: string;
  company: string;
  subject: string;
  status: 'draft' | 'sent' | 'opened' | 'replied' | 'bounced';
  sent_at?: string;
  opened_at?: string;
  replied_at?: string;
  created_at: string;
}

export interface NotificationPreferences {
  email_on_response: boolean;
  email_on_interview: boolean;
  email_on_offer: boolean;
  email_daily_summary: boolean;
  push_on_agent_error: boolean;
  push_on_application: boolean;
}

export interface Subscription {
  id: string;
  tier: 'free' | 'pro' | 'enterprise';
  status: 'active' | 'canceled' | 'past_due';
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  stripe_customer_id?: string;
  stripe_subscription_id?: string;
}

export interface PlatformConnection {
  platform: 'linkedin' | 'naukri' | 'indeed';
  is_connected: boolean;
  username?: string;
  connected_at?: string;
  last_sync?: string;
  status: 'active' | 'expired' | 'error';
}
