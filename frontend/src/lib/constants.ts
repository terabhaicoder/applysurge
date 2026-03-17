export const APP_NAME = "Apply Surge";
export const APP_DESCRIPTION = "AI-powered job application automation platform";

export const ROUTES = {
  HOME: "/",
  LOGIN: "/login",
  REGISTER: "/register",
  VERIFY_EMAIL: "/verify-email",
  FORGOT_PASSWORD: "/forgot-password",
  RESET_PASSWORD: "/reset-password",
  SETUP: "/setup",
  DASHBOARD: "/dashboard",
  JOBS: "/jobs",
  APPLICATIONS: "/applications",
  AGENT: "/agent",
  AGENT_LIVE: "/agent/live",
  ANALYTICS: "/analytics",
  EMAILS: "/emails",
  EMAIL_TEMPLATES: "/emails/templates",
  RESUME: "/resume",
  PREFERENCES: "/preferences",
  CONNECTIONS: "/connections",
  SETTINGS: "/settings",
  SETTINGS_PROFILE: "/settings/profile",
  SETTINGS_BILLING: "/settings/billing",
  EXPORT: "/export",
  PRICING: "/pricing",
  FEATURES: "/features",
  ABOUT: "/about",
} as const;

export const STATUS_LABELS: Record<string, string> = {
  queued: "Queued",
  in_progress: "In Progress",
  applied: "Applied",
  viewed: "Viewed",
  shortlisted: "Shortlisted",
  interview_scheduled: "Interview Scheduled",
  interviewed: "Interviewed",
  offered: "Offered",
  accepted: "Accepted",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
  failed: "Failed",
};

export const JOB_TYPES: Record<string, string> = {
  "full-time": "Full Time",
  "full_time": "Full Time",
  "part-time": "Part Time",
  "part_time": "Part Time",
  "contract": "Contract",
  "temporary": "Temporary",
  "internship": "Internship",
  "remote": "Remote",
  "volunteer": "Volunteer",
};

export const EXPERIENCE_LEVELS: Record<string, string> = {
  "entry_level": "Entry Level",
  "entry": "Entry Level",
  "associate": "Associate",
  "mid_senior": "Mid-Senior",
  "mid": "Mid Level",
  "senior": "Senior",
  "lead": "Lead",
  "director": "Director",
  "executive": "Executive",
  "internship": "Internship",
};

export const PLATFORMS: Record<string, string> = {
  linkedin: "LinkedIn",
  naukri: "Naukri",
  indeed: "Indeed",
  startup_outreach: "Startups",
  direct: "Direct",
};

export const SUBSCRIPTION_TIERS = {
  free: {
    name: "Free",
    price: 0,
    applications_per_day: 5,
    features: ["5 applications/day", "Basic job matching", "Email support"],
  },
  pro: {
    name: "Pro",
    price: 29,
    applications_per_day: 50,
    features: [
      "50 applications/day",
      "AI cover letters",
      "Advanced matching",
      "Email outreach",
      "Priority support",
      "Analytics dashboard",
    ],
  },
  enterprise: {
    name: "Enterprise",
    price: 79,
    applications_per_day: 200,
    features: [
      "200 applications/day",
      "Everything in Pro",
      "Multiple resumes",
      "API access",
      "Custom integrations",
      "Dedicated support",
    ],
  },
} as const;

export const AGENT_SPEEDS: Record<string, string> = {
  slow: "Slow (1-2 min between apps)",
  normal: "Normal (30-60s between apps)",
  fast: "Fast (15-30s between apps)",
};

export const EMAIL_TEMPLATE_TYPES: Record<string, string> = {
  follow_up: "Follow Up",
  cold_outreach: "Cold Outreach",
  thank_you: "Thank You",
  custom: "Custom",
};
