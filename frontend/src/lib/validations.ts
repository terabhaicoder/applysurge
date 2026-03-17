import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

export const registerSchema = z.object({
  full_name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  confirm_password: z.string(),
}).refine((data) => data.password === data.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
});

export const forgotPasswordSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
});

export const resetPasswordSchema = z.object({
  password: z.string().min(8, "Password must be at least 8 characters"),
  confirm_password: z.string(),
}).refine((data) => data.password === data.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
});

export const profileSchema = z.object({
  full_name: z.string().min(2, "Name must be at least 2 characters"),
  headline: z.string().optional(),
  summary: z.string().optional(),
  location: z.string().optional(),
  phone: z.string().optional(),
  linkedin_url: z.string().url().optional().or(z.literal("")),
  github_url: z.string().url().optional().or(z.literal("")),
  portfolio_url: z.string().url().optional().or(z.literal("")),
  years_of_experience: z.number().min(0).max(50).optional(),
  current_company: z.string().optional(),
  current_title: z.string().optional(),
  skills: z.array(z.string()).optional(),
});

export const preferencesSchema = z.object({
  preferred_job_types: z.array(z.string()),
  preferred_locations: z.array(z.string()),
  salary_min: z.number().min(0).optional(),
  salary_max: z.number().min(0).optional(),
  remote_only: z.boolean(),
  experience_levels: z.array(z.string()),
  blacklisted_companies: z.array(z.string()).optional(),
});

export const agentSettingsSchema = z.object({
  max_applications_per_day: z.number().min(1).max(200),
  cooldown_seconds: z.number().min(5).max(300),
  auto_apply: z.boolean(),
  cover_letter_enabled: z.boolean(),
  preferred_apply_time_start: z.string().nullable().optional(),
  preferred_apply_time_end: z.string().nullable().optional(),
  skip_easy_apply: z.boolean(),
  require_salary_info: z.boolean(),
});

export const emailSettingsSchema = z.object({
  smtp_host: z.string().optional(),
  smtp_port: z.number().optional(),
  smtp_username: z.string().optional(),
  smtp_password: z.string().optional(),
  from_name: z.string().min(1, "From name is required"),
  from_email: z.string().email("Please enter a valid email"),
  use_gmail: z.boolean(),
  gmail_app_password: z.string().optional(),
});

export const emailTemplateSchema = z.object({
  name: z.string().min(1, "Template name is required"),
  subject: z.string().min(1, "Subject is required"),
  body: z.string().min(10, "Body must be at least 10 characters"),
  type: z.enum(["follow_up", "cold_outreach", "thank_you", "custom"]),
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
export type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;
export type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;
export type ProfileFormData = z.infer<typeof profileSchema>;
export type PreferencesFormData = z.infer<typeof preferencesSchema>;
export type AgentSettingsFormData = z.infer<typeof agentSettingsSchema>;
export type EmailSettingsFormData = z.infer<typeof emailSettingsSchema>;
export type EmailTemplateFormData = z.infer<typeof emailTemplateSchema>;
