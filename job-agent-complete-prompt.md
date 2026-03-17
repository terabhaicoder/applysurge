# 🚀 COMPLETE LLM PROMPT: AI Job Application Agent

## PROJECT OVERVIEW

Build a production-ready, full-stack AI-powered job application platform called **"JobPilot"** that autonomously:

1. **Scrapes jobs** from LinkedIn and Naukri.com based on user preferences
2. **Applies automatically** via LinkedIn Easy Apply and Naukri Quick Apply
3. **Sends cold emails** to hiring managers/recruiters with personalized outreach
4. **Tracks everything** with full analytics, history, and export capabilities

The platform must be:
- Production-ready with Docker deployment
- Scalable for thousands of users
- Secure with encrypted credentials
- Monetization-ready with subscription tiers

---

## CORE USER FLOWS

### Flow 1: User Onboarding
```
1. User signs up (email/password or Google OAuth)
2. Email verification
3. Upload resume (PDF/DOCX) → AI parses and extracts data
4. Fill profile: name, phone, location, LinkedIn URL, work authorization
5. Set job preferences: titles, locations, salary, remote preference, company size
6. Connect LinkedIn account (credentials stored encrypted)
7. Connect Naukri account (credentials stored encrypted)
8. Set up email for cold outreach (Gmail OAuth or SMTP)
9. Configure agent settings: daily limits, speed, application methods
10. Start the agent!
```

### Flow 2: Job Discovery & Application
```
1. Agent runs on schedule (every hour or continuous)
2. Scrapes LinkedIn Jobs matching user preferences
3. Scrapes Naukri.com jobs matching user preferences
4. AI scores each job for match quality (0-100%)
5. Filters out already-applied jobs
6. Adds matched jobs to application queue
7. For each job in queue:
   a. Research company (website, news, funding, tech stack)
   b. Generate personalized cover letter
   c. Apply via appropriate method:
      - LinkedIn Easy Apply → Fill form, upload resume, submit
      - Naukri Quick Apply → One-click apply
      - Cold Email → Find HM email, send personalized email
   d. Screenshot confirmation
   e. Save to database
   f. Send screenshot to frontend via WebSocket (real-time view)
8. Track status updates and responses
```

### Flow 3: Cold Email Outreach
```
1. For jobs where direct apply isn't ideal OR user enables outreach
2. Find hiring manager/recruiter on LinkedIn
3. Find their email (Hunter.io + pattern guessing + verification)
4. AI generates personalized email using:
   - User's resume/experience
   - Job description
   - Company research
   - HM's LinkedIn activity
5. Send email with resume attached
6. Track opens and clicks
7. Auto follow-up sequence:
   - Day 3: First follow-up if no response
   - Day 7: Second follow-up with added value
   - Day 14: Breakup email
8. Parse responses and classify (interested/not interested/question)
```

---

## TECH STACK (MANDATORY)

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 14 (App Router) | React framework with SSR |
| TypeScript | 5.x | Type safety |
| Tailwind CSS | 3.x | Styling |
| shadcn/ui | Latest | UI components |
| Zustand | 4.x | State management |
| TanStack Query | 5.x | Server state, caching |
| Socket.io Client | 4.x | Real-time updates |
| React Hook Form | 7.x | Form handling |
| Zod | 3.x | Validation |
| Recharts | 2.x | Analytics charts |
| Lucide React | Latest | Icons |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Backend language |
| FastAPI | 0.100+ | API framework |
| SQLAlchemy | 2.0 | ORM (async) |
| Alembic | 1.x | Database migrations |
| Pydantic | 2.x | Data validation |
| Celery | 5.x | Task queue |
| Redis | 7.x | Cache, sessions, rate limiting |
| RabbitMQ | 3.x | Message broker |
| Playwright | 1.40+ | Browser automation |
| Anthropic SDK | Latest | Claude API |

### External Services
| Service | Purpose |
|---------|---------|
| Claude API (claude-sonnet-4-20250514) | AI for cover letters, research, Q&A |
| Hunter.io API | Find email addresses |
| ZeroBounce/NeverBounce API | Verify emails |
| SendGrid / AWS SES | Send cold emails |
| AWS S3 / Cloudflare R2 | File storage (resumes, screenshots) |
| Stripe | Payments & subscriptions |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| Docker | Containerization |
| Docker Compose | Multi-container orchestration |
| Traefik | Reverse proxy, SSL, load balancing |
| PostgreSQL 15 | Primary database |
| Redis 7 | Cache, sessions, Celery broker |
| Let's Encrypt | Free SSL certificates |

---

## DATABASE SCHEMA

```sql
-- ============================================
-- DATABASE: jobpilot_db
-- ============================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS & AUTHENTICATION
-- ============================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    full_name VARCHAR(255),
    avatar_url VARCHAR(500),
    
    -- OAuth
    google_id VARCHAR(255) UNIQUE,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    is_superuser BOOLEAN DEFAULT false,
    
    -- Subscription
    subscription_tier VARCHAR(50) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'basic', 'pro', 'enterprise')),
    subscription_status VARCHAR(50) DEFAULT 'active',
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Usage tracking
    applications_this_month INT DEFAULT 0,
    emails_sent_this_month INT DEFAULT 0,
    usage_reset_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE verification_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'email_verification', 'password_reset'
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(500) UNIQUE NOT NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- USER PROFILE & PREFERENCES
-- ============================================

CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Personal Info
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    phone_country_code VARCHAR(10),
    headline VARCHAR(500), -- Professional headline
    summary TEXT, -- Professional summary
    
    -- Location
    current_city VARCHAR(255),
    current_state VARCHAR(255),
    current_country VARCHAR(100),
    willing_to_relocate BOOLEAN DEFAULT false,
    relocation_cities JSONB DEFAULT '[]', -- Cities willing to relocate to
    
    -- Links
    linkedin_url VARCHAR(500),
    portfolio_url VARCHAR(500),
    github_url VARCHAR(500),
    website_url VARCHAR(500),
    other_links JSONB DEFAULT '[]',
    
    -- Work Authorization
    work_authorization VARCHAR(100), -- 'us_citizen', 'green_card', 'h1b', 'opt', 'indian_citizen', etc.
    sponsorship_required BOOLEAN DEFAULT false,
    
    -- Current Status
    current_company VARCHAR(255),
    current_title VARCHAR(255),
    current_salary INT,
    current_salary_currency VARCHAR(10) DEFAULT 'USD',
    notice_period_days INT DEFAULT 0,
    
    -- Experience
    total_years_experience DECIMAL(4,1),
    
    -- Additional Info for Applications
    gender VARCHAR(50),
    date_of_birth DATE,
    nationality VARCHAR(100),
    languages JSONB DEFAULT '[]', -- [{language, proficiency}]
    
    -- Profile Completeness
    profile_completeness_score INT DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE user_education (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    institution VARCHAR(255) NOT NULL,
    degree VARCHAR(255),
    field_of_study VARCHAR(255),
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT false,
    grade VARCHAR(50),
    description TEXT,
    
    display_order INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE user_experience (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    company VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT false,
    description TEXT,
    highlights JSONB DEFAULT '[]', -- Key achievements
    skills_used JSONB DEFAULT '[]',
    
    display_order INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE user_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    skill_name VARCHAR(100) NOT NULL,
    proficiency VARCHAR(50), -- 'beginner', 'intermediate', 'advanced', 'expert'
    years_of_experience DECIMAL(4,1),
    is_primary BOOLEAN DEFAULT false, -- Primary/highlighted skill
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, skill_name)
);

CREATE TABLE user_certifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    issuing_organization VARCHAR(255),
    issue_date DATE,
    expiry_date DATE,
    credential_id VARCHAR(255),
    credential_url VARCHAR(500),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- RESUMES
-- ============================================

CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL, -- "Software Engineer Resume", "Frontend Resume"
    file_url VARCHAR(500) NOT NULL, -- S3 URL
    file_name VARCHAR(255),
    file_size INT,
    file_type VARCHAR(50), -- 'pdf', 'docx'
    
    -- Parsed content
    raw_text TEXT, -- Extracted text
    parsed_data JSONB, -- Structured data from parsing
    
    -- Settings
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    
    -- AI-generated versions
    tailored_versions JSONB DEFAULT '[]', -- Job-specific versions
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- JOB PREFERENCES
-- ============================================

CREATE TABLE job_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Target Roles
    target_titles JSONB DEFAULT '[]', -- ["Software Engineer", "Full Stack Developer"]
    title_variations JSONB DEFAULT '[]', -- AI-generated variations
    
    -- Location Preferences
    preferred_locations JSONB DEFAULT '[]', -- ["Remote", "San Francisco", "Bangalore"]
    remote_preference VARCHAR(50) DEFAULT 'any', -- 'remote_only', 'hybrid', 'onsite', 'any'
    
    -- Salary
    min_salary INT,
    max_salary INT,
    salary_currency VARCHAR(10) DEFAULT 'USD',
    include_jobs_without_salary BOOLEAN DEFAULT true,
    
    -- Company Preferences
    preferred_company_sizes JSONB DEFAULT '[]', -- ['startup', 'mid', 'enterprise']
    preferred_industries JSONB DEFAULT '[]', -- ['technology', 'fintech', 'healthcare']
    company_blacklist JSONB DEFAULT '[]', -- Companies to never apply to
    company_whitelist JSONB DEFAULT '[]', -- Priority companies
    
    -- Experience Level
    experience_levels JSONB DEFAULT '[]', -- ['mid', 'senior']
    
    -- Job Type
    job_types JSONB DEFAULT '[]', -- ['full_time', 'contract']
    
    -- Other Filters
    min_match_score INT DEFAULT 60, -- Minimum AI match score (0-100)
    max_job_age_days INT DEFAULT 30, -- Only apply to jobs posted within X days
    
    -- Keywords
    required_keywords JSONB DEFAULT '[]', -- Must have these
    excluded_keywords JSONB DEFAULT '[]', -- Skip if has these
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- PLATFORM CREDENTIALS (ENCRYPTED)
-- ============================================

CREATE TABLE platform_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    platform VARCHAR(50) NOT NULL, -- 'linkedin', 'naukri', 'indeed'
    
    -- Credentials (encrypted)
    email_encrypted BYTEA,
    password_encrypted BYTEA,
    
    -- Session management
    session_cookies JSONB, -- Encrypted cookies
    session_valid_until TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_valid BOOLEAN DEFAULT true,
    last_validated_at TIMESTAMP WITH TIME ZONE,
    last_error TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, platform)
);

-- ============================================
-- EMAIL SETTINGS (FOR COLD OUTREACH)
-- ============================================

CREATE TABLE email_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Email Configuration
    provider VARCHAR(50), -- 'gmail', 'outlook', 'smtp'
    email_address VARCHAR(255) NOT NULL,
    
    -- For OAuth (Gmail, Outlook)
    oauth_access_token_encrypted BYTEA,
    oauth_refresh_token_encrypted BYTEA,
    oauth_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- For Custom SMTP
    smtp_host VARCHAR(255),
    smtp_port INT,
    smtp_username VARCHAR(255),
    smtp_password_encrypted BYTEA,
    smtp_use_tls BOOLEAN DEFAULT true,
    
    -- Sending Settings
    from_name VARCHAR(255), -- Display name
    reply_to VARCHAR(255),
    daily_send_limit INT DEFAULT 50,
    emails_sent_today INT DEFAULT 0,
    last_send_reset_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Signature
    email_signature TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_verified_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- EMAIL TEMPLATES
-- ============================================

CREATE TABLE email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Template content (with placeholders)
    subject_template TEXT NOT NULL,
    body_template TEXT NOT NULL,
    
    -- Placeholders available:
    -- {{first_name}}, {{company}}, {{job_title}}, {{hiring_manager_name}},
    -- {{company_research}}, {{relevant_experience}}, {{user_name}}, etc.
    
    -- Type
    template_type VARCHAR(50) DEFAULT 'initial', -- 'initial', 'followup_1', 'followup_2', 'breakup'
    
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    
    -- Performance metrics
    times_used INT DEFAULT 0,
    open_rate DECIMAL(5,2),
    response_rate DECIMAL(5,2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- AGENT SETTINGS
-- ============================================

CREATE TABLE agent_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Agent Status
    is_active BOOLEAN DEFAULT false,
    is_paused BOOLEAN DEFAULT false,
    
    -- Schedule
    schedule_enabled BOOLEAN DEFAULT false,
    schedule_start_time TIME, -- Start time daily
    schedule_end_time TIME, -- End time daily
    schedule_days JSONB DEFAULT '["mon","tue","wed","thu","fri"]', -- Days to run
    schedule_timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Limits
    daily_application_limit INT DEFAULT 25,
    applications_today INT DEFAULT 0,
    daily_email_limit INT DEFAULT 20,
    emails_today INT DEFAULT 0,
    limit_reset_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Speed & Behavior
    application_speed VARCHAR(20) DEFAULT 'medium', -- 'slow', 'medium', 'fast'
    -- slow: 3-5 min between apps, medium: 1-3 min, fast: 30s-1min
    
    min_delay_seconds INT DEFAULT 60,
    max_delay_seconds INT DEFAULT 180,
    
    -- Application Methods Enabled
    linkedin_easy_apply_enabled BOOLEAN DEFAULT true,
    naukri_apply_enabled BOOLEAN DEFAULT true,
    cold_email_enabled BOOLEAN DEFAULT true,
    
    -- Review Settings
    require_review_before_apply BOOLEAN DEFAULT false, -- Human-in-the-loop
    auto_apply_high_match_only BOOLEAN DEFAULT false, -- Only auto-apply if match > 80%
    
    -- Cover Letter Settings
    always_include_cover_letter BOOLEAN DEFAULT true,
    cover_letter_tone VARCHAR(50) DEFAULT 'professional', -- 'professional', 'casual', 'enthusiastic'
    
    -- Cold Email Settings
    cold_email_strategy VARCHAR(50) DEFAULT 'after_apply', -- 'instead_of_apply', 'after_apply', 'high_value_only'
    followup_enabled BOOLEAN DEFAULT true,
    followup_delay_days_1 INT DEFAULT 3,
    followup_delay_days_2 INT DEFAULT 7,
    max_followups INT DEFAULT 2,
    
    -- Notifications
    notify_on_application BOOLEAN DEFAULT false,
    notify_on_response BOOLEAN DEFAULT true,
    notify_on_interview BOOLEAN DEFAULT true,
    notify_daily_summary BOOLEAN DEFAULT true,
    notification_email VARCHAR(255),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- JOBS (DISCOVERED)
-- ============================================

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source Info
    source VARCHAR(50) NOT NULL, -- 'linkedin', 'naukri'
    source_job_id VARCHAR(255) NOT NULL, -- ID on the platform
    source_url VARCHAR(1000) NOT NULL,
    
    -- Basic Info
    title VARCHAR(500) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    company_logo_url VARCHAR(500),
    company_linkedin_url VARCHAR(500),
    company_website VARCHAR(500),
    
    -- Location
    location VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    is_remote BOOLEAN DEFAULT false,
    remote_type VARCHAR(50), -- 'fully_remote', 'hybrid', 'onsite'
    
    -- Job Details
    description TEXT,
    description_html TEXT,
    requirements TEXT,
    responsibilities TEXT,
    benefits TEXT,
    
    -- Compensation
    salary_min INT,
    salary_max INT,
    salary_currency VARCHAR(10),
    salary_period VARCHAR(20), -- 'yearly', 'monthly', 'hourly'
    salary_text VARCHAR(255), -- Original text
    
    -- Job Meta
    job_type VARCHAR(50), -- 'full_time', 'part_time', 'contract', 'internship'
    experience_level VARCHAR(50), -- 'entry', 'mid', 'senior', 'lead', 'executive'
    experience_years_min INT,
    experience_years_max INT,
    
    -- Application Info
    application_type VARCHAR(50), -- 'easy_apply', 'external', 'email'
    application_url VARCHAR(1000),
    easy_apply_available BOOLEAN DEFAULT false,
    
    -- Extracted Data (AI)
    required_skills JSONB DEFAULT '[]',
    preferred_skills JSONB DEFAULT '[]',
    technologies JSONB DEFAULT '[]',
    
    -- Company Research (populated later)
    company_research JSONB,
    company_size VARCHAR(50),
    company_industry VARCHAR(100),
    company_funding VARCHAR(255),
    
    -- Hiring Manager (if found)
    hiring_manager_name VARCHAR(255),
    hiring_manager_title VARCHAR(255),
    hiring_manager_linkedin VARCHAR(500),
    hiring_manager_email VARCHAR(255),
    hiring_manager_email_verified BOOLEAN DEFAULT false,
    
    -- Metadata
    posted_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    applicant_count INT, -- If available
    
    -- Our metadata
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    
    UNIQUE(source, source_job_id)
);

-- ============================================
-- JOB MATCHES (Per User)
-- ============================================

CREATE TABLE job_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    
    -- Match Analysis
    match_score INT NOT NULL, -- 0-100
    match_reasons JSONB DEFAULT '[]', -- Why it matched
    missing_skills JSONB DEFAULT '[]', -- Skills user lacks
    
    -- Status
    status VARCHAR(50) DEFAULT 'new', -- 'new', 'queued', 'skipped', 'applied', 'saved'
    
    -- User actions
    is_saved BOOLEAN DEFAULT false, -- User bookmarked
    is_hidden BOOLEAN DEFAULT false, -- User dismissed
    user_notes TEXT,
    
    -- Queue info
    queue_priority INT DEFAULT 0,
    queued_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, job_id)
);

-- ============================================
-- APPLICATIONS
-- ============================================

CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    job_match_id UUID REFERENCES job_matches(id) ON DELETE SET NULL,
    
    -- Job Info (denormalized for history)
    job_title VARCHAR(500),
    company_name VARCHAR(255),
    job_location VARCHAR(255),
    job_url VARCHAR(1000),
    job_source VARCHAR(50),
    
    -- Application Method
    application_method VARCHAR(50) NOT NULL, -- 'linkedin_easy_apply', 'naukri_apply', 'cold_email', 'manual'
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    -- pending, in_progress, applied, failed, response_received, 
    -- interview_scheduled, interviewing, offer_received, rejected, withdrawn, hired
    
    -- Status History
    status_history JSONB DEFAULT '[]', -- [{status, timestamp, notes}]
    
    -- Application Content
    resume_id UUID REFERENCES resumes(id),
    resume_url_used VARCHAR(500),
    cover_letter_generated TEXT,
    cover_letter_used TEXT, -- Final version (may be edited)
    
    -- Screening Questions & Answers
    screening_questions JSONB DEFAULT '[]', -- [{question, answer, confidence}]
    
    -- For Cold Email
    email_sent_to VARCHAR(255),
    email_subject VARCHAR(500),
    email_body TEXT,
    email_sent_at TIMESTAMP WITH TIME ZONE,
    email_message_id VARCHAR(255), -- For tracking
    email_opened BOOLEAN DEFAULT false,
    email_opened_at TIMESTAMP WITH TIME ZONE,
    email_clicked BOOLEAN DEFAULT false,
    email_clicked_at TIMESTAMP WITH TIME ZONE,
    email_replied BOOLEAN DEFAULT false,
    email_replied_at TIMESTAMP WITH TIME ZONE,
    
    -- Follow-ups
    followup_count INT DEFAULT 0,
    last_followup_at TIMESTAMP WITH TIME ZONE,
    next_followup_at TIMESTAMP WITH TIME ZONE,
    followup_stopped BOOLEAN DEFAULT false,
    followup_stop_reason VARCHAR(255),
    
    -- Response
    response_received_at TIMESTAMP WITH TIME ZONE,
    response_type VARCHAR(50), -- 'interview_request', 'rejection', 'question', 'positive', 'negative'
    response_content TEXT,
    response_summary TEXT, -- AI-generated summary
    
    -- Interview
    interview_scheduled_at TIMESTAMP WITH TIME ZONE,
    interview_type VARCHAR(50), -- 'phone', 'video', 'onsite', 'technical'
    interview_notes TEXT,
    
    -- Outcome
    outcome VARCHAR(50), -- 'hired', 'rejected', 'withdrawn', 'ghosted'
    outcome_notes TEXT,
    offer_amount INT,
    offer_currency VARCHAR(10),
    
    -- Evidence/Proof
    screenshots JSONB DEFAULT '[]', -- URLs to screenshots
    confirmation_screenshot VARCHAR(500),
    
    -- Error handling
    error_message TEXT,
    retry_count INT DEFAULT 0,
    last_error_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    applied_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- APPLICATION LOGS (Detailed)
-- ============================================

CREATE TABLE application_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    
    action VARCHAR(100) NOT NULL, -- 'navigated', 'clicked', 'typed', 'uploaded', 'submitted', 'error'
    action_details JSONB,
    screenshot_url VARCHAR(500),
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INT,
    
    -- Error info
    is_error BOOLEAN DEFAULT false,
    error_message TEXT
);

-- ============================================
-- EMAIL TRACKING
-- ============================================

CREATE TABLE email_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    
    event_type VARCHAR(50) NOT NULL, -- 'sent', 'delivered', 'opened', 'clicked', 'bounced', 'complained'
    event_data JSONB,
    
    ip_address VARCHAR(50),
    user_agent TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE scheduled_followups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    
    followup_number INT NOT NULL, -- 1, 2, 3
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Content (pre-generated)
    subject TEXT,
    body TEXT,
    
    -- Status
    status VARCHAR(50) DEFAULT 'scheduled', -- 'scheduled', 'sent', 'cancelled', 'skipped'
    sent_at TIMESTAMP WITH TIME ZONE,
    cancelled_reason VARCHAR(255),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- ANALYTICS & STATS
-- ============================================

CREATE TABLE daily_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    
    -- Application stats
    jobs_discovered INT DEFAULT 0,
    jobs_matched INT DEFAULT 0,
    applications_attempted INT DEFAULT 0,
    applications_successful INT DEFAULT 0,
    applications_failed INT DEFAULT 0,
    
    -- Email stats
    emails_sent INT DEFAULT 0,
    emails_opened INT DEFAULT 0,
    emails_clicked INT DEFAULT 0,
    emails_replied INT DEFAULT 0,
    
    -- Response stats
    responses_received INT DEFAULT 0,
    interviews_scheduled INT DEFAULT 0,
    rejections_received INT DEFAULT 0,
    
    -- By source
    linkedin_applications INT DEFAULT 0,
    naukri_applications INT DEFAULT 0,
    email_applications INT DEFAULT 0,
    
    -- By method
    easy_apply_count INT DEFAULT 0,
    direct_apply_count INT DEFAULT 0,
    cold_email_count INT DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, date)
);

-- ============================================
-- EXPORTS
-- ============================================

CREATE TABLE exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    export_type VARCHAR(50) NOT NULL, -- 'csv', 'xlsx', 'pdf', 'google_sheets'
    export_scope VARCHAR(50), -- 'all', 'applications', 'jobs', 'analytics'
    
    filters_applied JSONB,
    record_count INT,
    
    file_url VARCHAR(500),
    file_name VARCHAR(255),
    file_size INT,
    
    status VARCHAR(50) DEFAULT 'processing', -- 'processing', 'completed', 'failed'
    error_message TEXT,
    
    -- For Google Sheets
    google_sheet_id VARCHAR(255),
    google_sheet_url VARCHAR(500),
    
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- NOTIFICATIONS
-- ============================================

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    type VARCHAR(50) NOT NULL, -- 'application_success', 'response_received', 'interview', 'daily_summary', 'error'
    title VARCHAR(255) NOT NULL,
    message TEXT,
    
    -- Related entities
    application_id UUID REFERENCES applications(id) ON DELETE SET NULL,
    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    
    -- Status
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP WITH TIME ZONE,
    
    -- Delivery
    email_sent BOOLEAN DEFAULT false,
    email_sent_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- SUBSCRIPTIONS & BILLING
-- ============================================

CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL, -- 'free', 'basic', 'pro', 'enterprise'
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Pricing
    price_monthly INT, -- in cents
    price_yearly INT,
    currency VARCHAR(10) DEFAULT 'USD',
    
    -- Stripe
    stripe_price_id_monthly VARCHAR(255),
    stripe_price_id_yearly VARCHAR(255),
    
    -- Limits
    applications_per_month INT,
    emails_per_month INT,
    resumes_limit INT,
    job_sources JSONB DEFAULT '[]', -- Which sources available
    
    -- Features
    features JSONB DEFAULT '[]',
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE payment_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    stripe_payment_intent_id VARCHAR(255),
    stripe_invoice_id VARCHAR(255),
    
    amount INT NOT NULL, -- in cents
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(50), -- 'succeeded', 'failed', 'pending'
    
    description TEXT,
    receipt_url VARCHAR(500),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================

-- Users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_stripe_customer ON users(stripe_customer_id);

-- Jobs
CREATE INDEX idx_jobs_source ON jobs(source);
CREATE INDEX idx_jobs_source_job_id ON jobs(source, source_job_id);
CREATE INDEX idx_jobs_company ON jobs(company_name);
CREATE INDEX idx_jobs_posted ON jobs(posted_at DESC);
CREATE INDEX idx_jobs_location ON jobs(city, state, country);
CREATE INDEX idx_jobs_active ON jobs(is_active) WHERE is_active = true;

-- Job Matches
CREATE INDEX idx_job_matches_user ON job_matches(user_id);
CREATE INDEX idx_job_matches_user_status ON job_matches(user_id, status);
CREATE INDEX idx_job_matches_score ON job_matches(match_score DESC);

-- Applications
CREATE INDEX idx_applications_user ON applications(user_id);
CREATE INDEX idx_applications_user_status ON applications(user_id, status);
CREATE INDEX idx_applications_applied ON applications(applied_at DESC);
CREATE INDEX idx_applications_job ON applications(job_id);
CREATE INDEX idx_applications_method ON applications(application_method);

-- Follow-ups
CREATE INDEX idx_followups_scheduled ON scheduled_followups(scheduled_for) WHERE status = 'scheduled';

-- Daily Stats
CREATE INDEX idx_daily_stats_user_date ON daily_stats(user_id, date DESC);

-- Notifications
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read) WHERE is_read = false;

-- ============================================
-- TRIGGERS
-- ============================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_resumes_updated_at BEFORE UPDATE ON resumes FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_job_preferences_updated_at BEFORE UPDATE ON job_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_platform_credentials_updated_at BEFORE UPDATE ON platform_credentials FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_email_settings_updated_at BEFORE UPDATE ON email_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_agent_settings_updated_at BEFORE UPDATE ON agent_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_job_matches_updated_at BEFORE UPDATE ON job_matches FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_applications_updated_at BEFORE UPDATE ON applications FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_daily_stats_updated_at BEFORE UPDATE ON daily_stats FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

---

## ENVIRONMENT VARIABLES

```env
# ============================================
# APPLICATION
# ============================================
APP_NAME=JobPilot
APP_ENV=production
DEBUG=false
SECRET_KEY=your-super-secret-key-at-least-32-characters-long
ENCRYPTION_KEY=your-32-byte-encryption-key-for-credentials

# URLs
FRONTEND_URL=https://jobpilot.yourdomain.com
BACKEND_URL=https://api.jobpilot.yourdomain.com
DOMAIN=yourdomain.com

# ============================================
# DATABASE
# ============================================
DATABASE_URL=postgresql+asyncpg://jobpilot_user:your_secure_db_password@postgres:5432/jobpilot_db
POSTGRES_USER=jobpilot_user
POSTGRES_PASSWORD=your_secure_db_password
POSTGRES_DB=jobpilot_db

# ============================================
# REDIS
# ============================================
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=your_redis_password

# ============================================
# RABBITMQ
# ============================================
RABBITMQ_URL=amqp://jobpilot:rabbitmq_password@rabbitmq:5672/
RABBITMQ_DEFAULT_USER=jobpilot
RABBITMQ_DEFAULT_PASS=rabbitmq_password

# ============================================
# JWT & AUTH
# ============================================
JWT_SECRET_KEY=your-jwt-secret-key-at-least-32-characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# ============================================
# AI / LLM
# ============================================
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key

# ============================================
# EMAIL SERVICES
# ============================================
# SendGrid (for sending cold emails)
SENDGRID_API_KEY=SG.your-sendgrid-api-key

# OR AWS SES
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1

# Email verification & finding
HUNTER_API_KEY=your-hunter-io-api-key
ZEROBOUNCE_API_KEY=your-zerobounce-api-key

# ============================================
# FILE STORAGE
# ============================================
# AWS S3
S3_BUCKET_NAME=jobpilot-files
S3_ACCESS_KEY=your-s3-access-key
S3_SECRET_KEY=your-s3-secret-key
S3_REGION=us-east-1
S3_ENDPOINT_URL=  # Leave empty for AWS, or set for S3-compatible (R2, MinIO)

# OR Cloudflare R2
R2_ACCOUNT_ID=your-cloudflare-account-id
R2_ACCESS_KEY_ID=your-r2-access-key
R2_SECRET_ACCESS_KEY=your-r2-secret-key
R2_BUCKET_NAME=jobpilot-files

# ============================================
# STRIPE (PAYMENTS)
# ============================================
STRIPE_SECRET_KEY=sk_live_your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=pk_live_your-stripe-publishable-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# Price IDs
STRIPE_PRICE_BASIC_MONTHLY=price_xxxxx
STRIPE_PRICE_BASIC_YEARLY=price_xxxxx
STRIPE_PRICE_PRO_MONTHLY=price_xxxxx
STRIPE_PRICE_PRO_YEARLY=price_xxxxx

# ============================================
# SMTP (For transactional emails - verification, etc.)
# ============================================
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=JobPilot

# ============================================
# BROWSER AUTOMATION
# ============================================
PLAYWRIGHT_HEADLESS=true
BROWSER_TIMEOUT_MS=30000
MAX_CONCURRENT_BROWSERS=5

# Proxy (optional, for avoiding detection)
PROXY_SERVER=
PROXY_USERNAME=
PROXY_PASSWORD=

# ============================================
# RATE LIMITING
# ============================================
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_AUTH_PER_MINUTE=10

# ============================================
# TRAEFIK / SSL
# ============================================
ACME_EMAIL=admin@yourdomain.com
```

---

## PROJECT STRUCTURE

```
jobpilot/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .gitignore
├── Makefile
├── README.md
│
├── frontend/
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   ├── package.json
│   ├── package-lock.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── postcss.config.js
│   ├── components.json          # shadcn config
│   │
│   ├── public/
│   │   ├── favicon.ico
│   │   ├── logo.svg
│   │   └── images/
│   │
│   └── src/
│       ├── app/
│       │   ├── layout.tsx                    # Root layout
│       │   ├── page.tsx                      # Landing page
│       │   ├── globals.css
│       │   │
│       │   ├── (auth)/
│       │   │   ├── layout.tsx                # Auth layout (no sidebar)
│       │   │   ├── login/
│       │   │   │   └── page.tsx
│       │   │   ├── register/
│       │   │   │   └── page.tsx
│       │   │   ├── verify-email/
│       │   │   │   └── page.tsx
│       │   │   ├── forgot-password/
│       │   │   │   └── page.tsx
│       │   │   └── reset-password/
│       │   │       └── page.tsx
│       │   │
│       │   ├── (dashboard)/
│       │   │   ├── layout.tsx                # Dashboard layout (with sidebar)
│       │   │   ├── dashboard/
│       │   │   │   └── page.tsx              # Main dashboard / overview
│       │   │   ├── jobs/
│       │   │   │   ├── page.tsx              # Discovered jobs list
│       │   │   │   └── [id]/
│       │   │   │       └── page.tsx          # Job details
│       │   │   ├── applications/
│       │   │   │   ├── page.tsx              # All applications
│       │   │   │   └── [id]/
│       │   │   │       └── page.tsx          # Application details
│       │   │   ├── agent/
│       │   │   │   ├── page.tsx              # Agent control panel
│       │   │   │   └── live/
│       │   │   │       └── page.tsx          # Live browser view
│       │   │   ├── analytics/
│       │   │   │   └── page.tsx              # Statistics & charts
│       │   │   ├── emails/
│       │   │   │   ├── page.tsx              # Email outreach dashboard
│       │   │   │   └── templates/
│       │   │   │       └── page.tsx          # Email templates
│       │   │   ├── settings/
│       │   │   │   ├── page.tsx              # Settings overview
│       │   │   │   ├── profile/
│       │   │   │   │   └── page.tsx          # Profile settings
│       │   │   │   ├── resume/
│       │   │   │   │   └── page.tsx          # Resume management
│       │   │   │   ├── preferences/
│       │   │   │   │   └── page.tsx          # Job preferences
│       │   │   │   ├── connections/
│       │   │   │   │   └── page.tsx          # LinkedIn, Naukri connections
│       │   │   │   ├── email/
│       │   │   │   │   └── page.tsx          # Email settings
│       │   │   │   ├── agent/
│       │   │   │   │   └── page.tsx          # Agent settings
│       │   │   │   ├── notifications/
│       │   │   │   │   └── page.tsx          # Notification preferences
│       │   │   │   └── billing/
│       │   │   │       └── page.tsx          # Subscription & billing
│       │   │   └── export/
│       │   │       └── page.tsx              # Export data
│       │   │
│       │   ├── (marketing)/
│       │   │   ├── pricing/
│       │   │   │   └── page.tsx
│       │   │   ├── features/
│       │   │   │   └── page.tsx
│       │   │   └── about/
│       │   │       └── page.tsx
│       │   │
│       │   └── api/
│       │       └── [...]/                    # API routes if needed
│       │
│       ├── components/
│       │   ├── ui/                           # shadcn components
│       │   │   ├── button.tsx
│       │   │   ├── input.tsx
│       │   │   ├── card.tsx
│       │   │   ├── dialog.tsx
│       │   │   ├── dropdown-menu.tsx
│       │   │   ├── select.tsx
│       │   │   ├── table.tsx
│       │   │   ├── tabs.tsx
│       │   │   ├── toast.tsx
│       │   │   ├── badge.tsx
│       │   │   ├── progress.tsx
│       │   │   ├── skeleton.tsx
│       │   │   ├── switch.tsx
│       │   │   ├── slider.tsx
│       │   │   ├── checkbox.tsx
│       │   │   ├── radio-group.tsx
│       │   │   ├── textarea.tsx
│       │   │   ├── label.tsx
│       │   │   ├── separator.tsx
│       │   │   ├── avatar.tsx
│       │   │   ├── scroll-area.tsx
│       │   │   ├── sheet.tsx
│       │   │   ├── tooltip.tsx
│       │   │   ├── popover.tsx
│       │   │   ├── command.tsx
│       │   │   ├── calendar.tsx
│       │   │   └── form.tsx
│       │   │
│       │   ├── layout/
│       │   │   ├── navbar.tsx
│       │   │   ├── sidebar.tsx
│       │   │   ├── footer.tsx
│       │   │   ├── mobile-nav.tsx
│       │   │   └── user-menu.tsx
│       │   │
│       │   ├── auth/
│       │   │   ├── login-form.tsx
│       │   │   ├── register-form.tsx
│       │   │   ├── forgot-password-form.tsx
│       │   │   ├── reset-password-form.tsx
│       │   │   ├── google-button.tsx
│       │   │   └── protected-route.tsx
│       │   │
│       │   ├── dashboard/
│       │   │   ├── stats-cards.tsx
│       │   │   ├── recent-applications.tsx
│       │   │   ├── agent-status.tsx
│       │   │   ├── activity-feed.tsx
│       │   │   └── quick-actions.tsx
│       │   │
│       │   ├── jobs/
│       │   │   ├── job-card.tsx
│       │   │   ├── job-list.tsx
│       │   │   ├── job-details.tsx
│       │   │   ├── job-filters.tsx
│       │   │   ├── match-score-badge.tsx
│       │   │   └── job-actions.tsx
│       │   │
│       │   ├── applications/
│       │   │   ├── application-card.tsx
│       │   │   ├── application-list.tsx
│       │   │   ├── application-details.tsx
│       │   │   ├── application-timeline.tsx
│       │   │   ├── status-badge.tsx
│       │   │   └── application-filters.tsx
│       │   │
│       │   ├── agent/
│       │   │   ├── agent-control-panel.tsx
│       │   │   ├── agent-status-indicator.tsx
│       │   │   ├── live-browser-view.tsx
│       │   │   ├── application-queue.tsx
│       │   │   ├── agent-logs.tsx
│       │   │   └── speed-selector.tsx
│       │   │
│       │   ├── analytics/
│       │   │   ├── stats-overview.tsx
│       │   │   ├── applications-chart.tsx
│       │   │   ├── response-rate-chart.tsx
│       │   │   ├── source-breakdown.tsx
│       │   │   └── trends-chart.tsx
│       │   │
│       │   ├── settings/
│       │   │   ├── profile-form.tsx
│       │   │   ├── resume-uploader.tsx
│       │   │   ├── resume-list.tsx
│       │   │   ├── preferences-form.tsx
│       │   │   ├── platform-connection.tsx
│       │   │   ├── email-settings-form.tsx
│       │   │   ├── agent-settings-form.tsx
│       │   │   └── notification-settings.tsx
│       │   │
│       │   ├── email/
│       │   │   ├── email-template-editor.tsx
│       │   │   ├── email-preview.tsx
│       │   │   ├── email-stats.tsx
│       │   │   └── followup-settings.tsx
│       │   │
│       │   └── common/
│       │       ├── page-header.tsx
│       │       ├── empty-state.tsx
│       │       ├── loading-state.tsx
│       │       ├── error-state.tsx
│       │       ├── confirmation-dialog.tsx
│       │       ├── file-upload.tsx
│       │       ├── date-picker.tsx
│       │       ├── search-input.tsx
│       │       ├── pagination.tsx
│       │       └── data-table.tsx
│       │
│       ├── lib/
│       │   ├── api.ts                        # API client (axios)
│       │   ├── auth.ts                       # Auth utilities
│       │   ├── socket.ts                     # Socket.io client
│       │   ├── utils.ts                      # General utilities
│       │   ├── validations.ts                # Zod schemas
│       │   └── constants.ts                  # Constants
│       │
│       ├── hooks/
│       │   ├── use-auth.ts
│       │   ├── use-user.ts
│       │   ├── use-socket.ts
│       │   ├── use-agent.ts
│       │   ├── use-applications.ts
│       │   ├── use-jobs.ts
│       │   ├── use-analytics.ts
│       │   ├── use-debounce.ts
│       │   ├── use-local-storage.ts
│       │   └── use-media-query.ts
│       │
│       ├── stores/
│       │   ├── auth-store.ts
│       │   ├── agent-store.ts
│       │   ├── notification-store.ts
│       │   └── ui-store.ts
│       │
│       ├── types/
│       │   ├── index.ts
│       │   ├── user.ts
│       │   ├── job.ts
│       │   ├── application.ts
│       │   ├── agent.ts
│       │   └── api.ts
│       │
│       └── providers/
│           ├── auth-provider.tsx
│           ├── query-provider.tsx
│           ├── socket-provider.tsx
│           ├── theme-provider.tsx
│           └── toast-provider.tsx
│
├── backend/
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   ├── Dockerfile.worker
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── alembic.ini
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                           # FastAPI app entry
│   │   ├── config.py                         # Settings
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                       # Dependencies (get_current_user, etc.)
│   │   │   │
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py                 # Main router
│   │   │       ├── auth.py                   # Auth endpoints
│   │   │       ├── users.py                  # User endpoints
│   │   │       ├── profile.py                # Profile endpoints
│   │   │       ├── resumes.py                # Resume endpoints
│   │   │       ├── preferences.py            # Job preferences endpoints
│   │   │       ├── credentials.py            # Platform credentials
│   │   │       ├── jobs.py                   # Jobs endpoints
│   │   │       ├── applications.py           # Applications endpoints
│   │   │       ├── agent.py                  # Agent control endpoints
│   │   │       ├── analytics.py              # Analytics endpoints
│   │   │       ├── email_settings.py         # Email settings endpoints
│   │   │       ├── email_templates.py        # Email templates endpoints
│   │   │       ├── notifications.py          # Notifications endpoints
│   │   │       ├── exports.py                # Export endpoints
│   │   │       ├── billing.py                # Stripe billing endpoints
│   │   │       └── websocket.py              # WebSocket endpoints
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py                     # Pydantic settings
│   │   │   ├── security.py                   # JWT, password hashing
│   │   │   ├── encryption.py                 # Credential encryption
│   │   │   ├── exceptions.py                 # Custom exceptions
│   │   │   └── rate_limiter.py               # Rate limiting
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py                    # Database session
│   │   │   ├── base.py                       # Base model class
│   │   │   └── init_db.py                    # Database initialization
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── profile.py
│   │   │   ├── resume.py
│   │   │   ├── preferences.py
│   │   │   ├── credentials.py
│   │   │   ├── job.py
│   │   │   ├── job_match.py
│   │   │   ├── application.py
│   │   │   ├── email_settings.py
│   │   │   ├── email_template.py
│   │   │   ├── agent_settings.py
│   │   │   ├── notification.py
│   │   │   ├── analytics.py
│   │   │   └── billing.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── profile.py
│   │   │   ├── resume.py
│   │   │   ├── preferences.py
│   │   │   ├── credentials.py
│   │   │   ├── job.py
│   │   │   ├── application.py
│   │   │   ├── email.py
│   │   │   ├── agent.py
│   │   │   ├── analytics.py
│   │   │   ├── notification.py
│   │   │   └── billing.py
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── profile_service.py
│   │   │   ├── resume_service.py
│   │   │   ├── resume_parser.py              # Parse resume content
│   │   │   ├── preferences_service.py
│   │   │   ├── credentials_service.py
│   │   │   ├── job_service.py
│   │   │   ├── application_service.py
│   │   │   ├── agent_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── email_service.py
│   │   │   ├── notification_service.py
│   │   │   ├── export_service.py
│   │   │   ├── stripe_service.py
│   │   │   ├── s3_service.py                 # File uploads
│   │   │   └── llm_service.py                # Claude API
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── email_finder.py               # Hunter.io integration
│   │       ├── email_verifier.py             # ZeroBounce integration
│   │       └── helpers.py
│   │
│   ├── worker/
│   │   ├── __init__.py
│   │   ├── celery_app.py                     # Celery configuration
│   │   │
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   ├── job_discovery.py              # Scrape jobs task
│   │   │   ├── job_matching.py               # Match jobs to users
│   │   │   ├── application_task.py           # Apply to jobs
│   │   │   ├── email_task.py                 # Send cold emails
│   │   │   ├── followup_task.py              # Send follow-ups
│   │   │   ├── research_task.py              # Company research
│   │   │   ├── analytics_task.py             # Update analytics
│   │   │   ├── notification_task.py          # Send notifications
│   │   │   └── scheduled_tasks.py            # Periodic tasks
│   │   │
│   │   ├── scrapers/
│   │   │   ├── __init__.py
│   │   │   ├── base_scraper.py               # Base scraper class
│   │   │   ├── linkedin_scraper.py           # LinkedIn jobs scraper
│   │   │   ├── linkedin_applicator.py        # LinkedIn Easy Apply
│   │   │   ├── naukri_scraper.py             # Naukri.com scraper
│   │   │   ├── naukri_applicator.py          # Naukri apply
│   │   │   └── company_scraper.py            # Company info scraper
│   │   │
│   │   ├── automation/
│   │   │   ├── __init__.py
│   │   │   ├── browser_manager.py            # Playwright browser pool
│   │   │   ├── session_manager.py            # Session/cookie management
│   │   │   ├── captcha_handler.py            # CAPTCHA detection/handling
│   │   │   ├── form_filler.py                # Intelligent form filling
│   │   │   └── screenshot_manager.py         # Screenshot capture
│   │   │
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── cover_letter_generator.py     # Generate cover letters
│   │   │   ├── question_answerer.py          # Answer screening questions
│   │   │   ├── company_researcher.py         # Research companies
│   │   │   ├── job_matcher.py                # AI job matching
│   │   │   ├── email_generator.py            # Generate cold emails
│   │   │   └── response_classifier.py        # Classify email responses
│   │   │
│   │   └── email/
│   │       ├── __init__.py
│   │       ├── email_sender.py               # Send emails (SendGrid/SES)
│   │       ├── email_tracker.py              # Track opens/clicks
│   │       └── email_parser.py               # Parse incoming emails
│   │
│   ├── migrations/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 001_initial_migration.py
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_users.py
│       ├── test_jobs.py
│       ├── test_applications.py
│       └── test_scrapers.py
│
├── nginx/
│   └── nginx.conf
│
└── scripts/
    ├── init-db.sh
    ├── backup-db.sh
    ├── deploy.sh
    ├── seed-data.py
    └── healthcheck.py
```

---

## DOCKER CONFIGURATION

### docker-compose.yml (Development)

```yaml
version: '3.8'

services:
  # ============================================
  # FRONTEND
  # ============================================
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000
    depends_on:
      - backend
    networks:
      - jobpilot-network

  # ============================================
  # BACKEND API
  # ============================================
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    env_file:
      - .env
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - RABBITMQ_URL=${RABBITMQ_URL}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
      rabbitmq:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - jobpilot-network

  # ============================================
  # CELERY WORKER (Job Processing)
  # ============================================
  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    volumes:
      - ./backend:/app
    env_file:
      - .env
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - RABBITMQ_URL=${RABBITMQ_URL}
    depends_on:
      - backend
      - rabbitmq
      - redis
    command: celery -A worker.celery_app worker --loglevel=info --concurrency=4 -Q default,scraping,applications,emails
    networks:
      - jobpilot-network

  # ============================================
  # CELERY WORKER (Browser Automation - needs more resources)
  # ============================================
  worker-browser:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    volumes:
      - ./backend:/app
    env_file:
      - .env
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - RABBITMQ_URL=${RABBITMQ_URL}
    depends_on:
      - backend
      - rabbitmq
      - redis
    command: celery -A worker.celery_app worker --loglevel=info --concurrency=2 -Q browser
    deploy:
      resources:
        limits:
          memory: 4G
    networks:
      - jobpilot-network

  # ============================================
  # CELERY BEAT (Scheduler)
  # ============================================
  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    volumes:
      - ./backend:/app
    env_file:
      - .env
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - RABBITMQ_URL=${RABBITMQ_URL}
    depends_on:
      - worker
    command: celery -A worker.celery_app beat --loglevel=info
    networks:
      - jobpilot-network

  # ============================================
  # POSTGRESQL
  # ============================================
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - jobpilot-network

  # ============================================
  # REDIS
  # ============================================
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    networks:
      - jobpilot-network

  # ============================================
  # RABBITMQ
  # ============================================
  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    environment:
      - RABBITMQ_DEFAULT_USER=${RABBITMQ_DEFAULT_USER}
      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_DEFAULT_PASS}
    healthcheck:
      test: rabbitmq-diagnostics -q ping
      interval: 10s
      timeout: 10s
      retries: 5
    networks:
      - jobpilot-network

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data:

networks:
  jobpilot-network:
    driver: bridge
```

### docker-compose.prod.yml (Production)

```yaml
version: '3.8'

services:
  # ============================================
  # TRAEFIK (Reverse Proxy)
  # ============================================
  traefik:
    image: traefik:v2.10
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--entrypoints.web.http.redirections.entryPoint.to=websecure"
      - "--entrypoints.web.http.redirections.entryPoint.scheme=https"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik_letsencrypt:/letsencrypt
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.traefik.rule=Host(`traefik.${DOMAIN}`)"
      - "traefik.http.routers.traefik.entrypoints=websecure"
      - "traefik.http.routers.traefik.tls.certresolver=letsencrypt"
      - "traefik.http.routers.traefik.service=api@internal"
      - "traefik.http.routers.traefik.middlewares=auth"
      - "traefik.http.middlewares.auth.basicauth.users=admin:$apr1$xxxx"
    networks:
      - jobpilot-network

  # ============================================
  # FRONTEND
  # ============================================
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`${DOMAIN}`) || Host(`www.${DOMAIN}`)"
      - "traefik.http.routers.frontend.entrypoints=websecure"
      - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
      - "traefik.http.services.frontend.loadbalancer.server.port=3000"
    environment:
      - NEXT_PUBLIC_API_URL=https://api.${DOMAIN}
      - NEXT_PUBLIC_WS_URL=wss://api.${DOMAIN}
    depends_on:
      - backend
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
    networks:
      - jobpilot-network

  # ============================================
  # BACKEND API
  # ============================================
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.backend.rule=Host(`api.${DOMAIN}`)"
      - "traefik.http.routers.backend.entrypoints=websecure"
      - "traefik.http.routers.backend.tls.certresolver=letsencrypt"
      - "traefik.http.services.backend.loadbalancer.server.port=8000"
    env_file:
      - .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
      rabbitmq:
        condition: service_healthy
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
    command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    networks:
      - jobpilot-network

  # ============================================
  # CELERY WORKERS
  # ============================================
  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    env_file:
      - .env
    depends_on:
      - backend
      - rabbitmq
      - redis
    deploy:
      replicas: 4
      resources:
        limits:
          memory: 1G
    command: celery -A worker.celery_app worker --loglevel=warning --concurrency=4 -Q default,scraping,applications,emails
    networks:
      - jobpilot-network

  worker-browser:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    env_file:
      - .env
    depends_on:
      - backend
      - rabbitmq
      - redis
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 4G
    command: celery -A worker.celery_app worker --loglevel=warning --concurrency=1 -Q browser
    networks:
      - jobpilot-network

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    env_file:
      - .env
    depends_on:
      - worker
    deploy:
      replicas: 1
    command: celery -A worker.celery_app beat --loglevel=warning
    networks:
      - jobpilot-network

  # ============================================
  # DATABASES
  # ============================================
  postgres:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 2G
    networks:
      - jobpilot-network

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    deploy:
      resources:
        limits:
          memory: 512M
    networks:
      - jobpilot-network

  rabbitmq:
    image: rabbitmq:3-management-alpine
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    environment:
      - RABBITMQ_DEFAULT_USER=${RABBITMQ_DEFAULT_USER}
      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_DEFAULT_PASS}
    healthcheck:
      test: rabbitmq-diagnostics -q ping
      interval: 10s
      timeout: 10s
      retries: 5
    networks:
      - jobpilot-network

volumes:
  traefik_letsencrypt:
  postgres_data:
  redis_data:
  rabbitmq_data:

networks:
  jobpilot-network:
    driver: bridge
```

---

## API ENDPOINTS

### Authentication (`/api/v1/auth`)
```
POST   /register                    # Register new user
POST   /login                       # Login with email/password
POST   /logout                      # Logout (revoke tokens)
POST   /refresh                     # Refresh access token
POST   /forgot-password             # Request password reset
POST   /reset-password              # Reset password with token
GET    /verify-email/{token}        # Verify email address
POST   /google                      # Google OAuth login
GET    /me                          # Get current user
```

### Users (`/api/v1/users`)
```
GET    /me                          # Get current user
PATCH  /me                          # Update current user
DELETE /me                          # Delete account
PATCH  /me/password                 # Change password
GET    /me/usage                    # Get usage stats
```

### Profile (`/api/v1/profile`)
```
GET    /                            # Get user profile
PUT    /                            # Update profile
GET    /education                   # Get education list
POST   /education                   # Add education
PUT    /education/{id}              # Update education
DELETE /education/{id}              # Delete education
GET    /experience                  # Get experience list
POST   /experience                  # Add experience
PUT    /experience/{id}             # Update experience
DELETE /experience/{id}             # Delete experience
GET    /skills                      # Get skills
POST   /skills                      # Add skill
DELETE /skills/{id}                 # Delete skill
GET    /certifications              # Get certifications
POST   /certifications              # Add certification
DELETE /certifications/{id}         # Delete certification
```

### Resumes (`/api/v1/resumes`)
```
GET    /                            # List resumes
POST   /                            # Upload resume
GET    /{id}                        # Get resume
DELETE /{id}                        # Delete resume
PATCH  /{id}                        # Update resume (name, default)
POST   /{id}/parse                  # Re-parse resume
GET    /{id}/download               # Download resume file
```

### Job Preferences (`/api/v1/preferences`)
```
GET    /                            # Get job preferences
PUT    /                            # Update preferences
GET    /suggestions                 # Get AI suggestions for preferences
```

### Platform Credentials (`/api/v1/credentials`)
```
GET    /                            # List connected platforms
POST   /linkedin                    # Connect LinkedIn
POST   /naukri                      # Connect Naukri
DELETE /{platform}                  # Disconnect platform
POST   /{platform}/validate         # Validate credentials
GET    /{platform}/status           # Check connection status
```

### Jobs (`/api/v1/jobs`)
```
GET    /                            # List matched jobs (paginated)
GET    /{id}                        # Get job details
POST   /{id}/save                   # Save/bookmark job
POST   /{id}/hide                   # Hide job
POST   /{id}/queue                  # Add to application queue
DELETE /{id}/queue                  # Remove from queue
GET    /queue                       # Get application queue
POST   /search                      # Manual job search
```

### Applications (`/api/v1/applications`)
```
GET    /                            # List applications (paginated, filtered)
GET    /{id}                        # Get application details
GET    /{id}/logs                   # Get application logs
GET    /{id}/screenshots            # Get screenshots
PATCH  /{id}/status                 # Update status manually
POST   /{id}/withdraw               # Withdraw application
POST   /{id}/note                   # Add note
DELETE /{id}                        # Delete application record
GET    /stats                       # Get application statistics
```

### Agent (`/api/v1/agent`)
```
GET    /status                      # Get agent status
POST   /start                       # Start agent
POST   /stop                        # Stop agent
POST   /pause                       # Pause agent
POST   /resume                      # Resume agent
GET    /settings                    # Get agent settings
PUT    /settings                    # Update agent settings
GET    /queue                       # Get current queue
POST   /queue/clear                 # Clear queue
GET    /logs                        # Get agent activity logs
WS     /live                        # WebSocket for live updates
```

### Email Settings (`/api/v1/email-settings`)
```
GET    /                            # Get email settings
PUT    /                            # Update email settings
POST   /connect/gmail               # Connect Gmail OAuth
POST   /connect/outlook             # Connect Outlook OAuth
POST   /connect/smtp                # Configure SMTP
POST   /verify                      # Verify email configuration
POST   /test                        # Send test email
```

### Email Templates (`/api/v1/email-templates`)
```
GET    /                            # List templates
POST   /                            # Create template
GET    /{id}                        # Get template
PUT    /{id}                        # Update template
DELETE /{id}                        # Delete template
POST   /{id}/preview                # Preview template with sample data
POST   /generate                    # AI generate template
```

### Analytics (`/api/v1/analytics`)
```
GET    /overview                    # Get overview stats
GET    /applications                # Application stats over time
GET    /responses                   # Response rate stats
GET    /sources                     # Stats by source (LinkedIn, Naukri, Email)
GET    /daily                       # Daily breakdown
GET    /weekly                      # Weekly summary
GET    /monthly                     # Monthly summary
```

### Notifications (`/api/v1/notifications`)
```
GET    /                            # List notifications
GET    /unread/count                # Get unread count
POST   /{id}/read                   # Mark as read
POST   /read-all                    # Mark all as read
DELETE /{id}                        # Delete notification
GET    /settings                    # Get notification settings
PUT    /settings                    # Update notification settings
```

### Exports (`/api/v1/exports`)
```
GET    /                            # List exports
POST   /                            # Create export
GET    /{id}                        # Get export status
GET    /{id}/download               # Download export file
DELETE /{id}                        # Delete export
```

### Billing (`/api/v1/billing`)
```
GET    /plans                       # Get available plans
GET    /subscription                # Get current subscription
POST   /checkout                    # Create Stripe checkout session
POST   /portal                      # Get Stripe portal URL
GET    /invoices                    # Get invoice history
POST   /webhook                     # Stripe webhook handler
```

### WebSocket (`/api/v1/ws`)
```
WS     /agent/{user_id}             # Live agent updates & browser view
WS     /notifications/{user_id}     # Real-time notifications
```

---

## CORE LOGIC IMPLEMENTATIONS

### 1. LinkedIn Scraper (worker/scrapers/linkedin_scraper.py)

```python
"""
LinkedIn Job Scraper

Scrapes jobs from LinkedIn based on user preferences.
Handles pagination, rate limiting, and anti-detection.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Optional
from playwright.async_api import async_playwright, Page, Browser
from app.models.job import Job
from app.schemas.job import JobCreate
from worker.automation.session_manager import SessionManager
from worker.automation.captcha_handler import CaptchaHandler
import logging

logger = logging.getLogger(__name__)

class LinkedInScraper:
    def __init__(self, user_id: str, credentials: dict):
        self.user_id = user_id
        self.credentials = credentials
        self.session_manager = SessionManager("linkedin", user_id)
        self.captcha_handler = CaptchaHandler()
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def initialize(self):
        """Initialize browser with stealth settings"""
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
            ]
        )
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
        )
        
        # Add stealth scripts
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = { runtime: {} };
        """)
        
        self.page = await context.new_page()
        
        # Try to restore session
        cookies = await self.session_manager.get_cookies()
        if cookies:
            await context.add_cookies(cookies)
            
    async def login(self) -> bool:
        """Login to LinkedIn"""
        await self.page.goto('https://www.linkedin.com/login')
        await asyncio.sleep(random.uniform(1, 2))
        
        # Check if already logged in
        if 'feed' in self.page.url:
            logger.info("Already logged in via cookies")
            return True
            
        # Fill login form
        await self.page.fill('#username', self.credentials['email'])
        await asyncio.sleep(random.uniform(0.5, 1))
        await self.page.fill('#password', self.credentials['password'])
        await asyncio.sleep(random.uniform(0.5, 1))
        
        # Click login
        await self.page.click('button[type="submit"]')
        await asyncio.sleep(random.uniform(2, 4))
        
        # Check for CAPTCHA or verification
        if await self.captcha_handler.detect_captcha(self.page):
            logger.warning("CAPTCHA detected, notifying user")
            await self.notify_user_captcha()
            return False
            
        # Check for 2FA
        if 'checkpoint' in self.page.url:
            logger.warning("2FA required, notifying user")
            await self.notify_user_2fa()
            return False
            
        # Verify login success
        if 'feed' in self.page.url or 'mynetwork' in self.page.url:
            # Save cookies for future use
            cookies = await self.page.context.cookies()
            await self.session_manager.save_cookies(cookies)
            logger.info("LinkedIn login successful")
            return True
            
        return False
        
    async def search_jobs(
        self,
        keywords: List[str],
        locations: List[str],
        remote: bool = False,
        posted_within_days: int = 7,
        easy_apply_only: bool = True,
        max_jobs: int = 100
    ) -> List[JobCreate]:
        """Search for jobs on LinkedIn"""
        jobs = []
        
        for keyword in keywords:
            for location in locations:
                query_jobs = await self._search_single_query(
                    keyword=keyword,
                    location=location,
                    remote=remote,
                    posted_within_days=posted_within_days,
                    easy_apply_only=easy_apply_only,
                    max_jobs=max_jobs // (len(keywords) * len(locations))
                )
                jobs.extend(query_jobs)
                
                # Rate limiting
                await asyncio.sleep(random.uniform(5, 10))
                
        return jobs
        
    async def _search_single_query(
        self,
        keyword: str,
        location: str,
        remote: bool,
        posted_within_days: int,
        easy_apply_only: bool,
        max_jobs: int
    ) -> List[JobCreate]:
        """Execute a single search query"""
        jobs = []
        
        # Build search URL
        params = {
            'keywords': keyword,
            'location': location,
            'f_TPR': f'r{posted_within_days * 86400}',  # Time posted filter
            'f_AL': 'true' if easy_apply_only else '',   # Easy Apply filter
            'f_WT': '2' if remote else '',               # Remote filter
        }
        
        search_url = self._build_search_url(params)
        await self.page.goto(search_url)
        await asyncio.sleep(random.uniform(2, 4))
        
        page_num = 0
        while len(jobs) < max_jobs:
            # Extract jobs from current page
            page_jobs = await self._extract_jobs_from_page()
            jobs.extend(page_jobs)
            
            logger.info(f"Scraped {len(page_jobs)} jobs from page {page_num + 1}")
            
            # Check for next page
            next_button = await self.page.query_selector('button[aria-label="Next"]')
            if not next_button or await next_button.is_disabled():
                break
                
            # Go to next page
            await next_button.click()
            await asyncio.sleep(random.uniform(3, 6))
            page_num += 1
            
            # Safety limit
            if page_num >= 10:
                break
                
        return jobs[:max_jobs]
        
    async def _extract_jobs_from_page(self) -> List[JobCreate]:
        """Extract job listings from current page"""
        jobs = []
        
        # Wait for job cards to load
        await self.page.wait_for_selector('.job-card-container', timeout=10000)
        
        # Get all job cards
        job_cards = await self.page.query_selector_all('.job-card-container')
        
        for card in job_cards:
            try:
                job_data = await self._extract_job_card_data(card)
                if job_data:
                    jobs.append(job_data)
            except Exception as e:
                logger.error(f"Error extracting job card: {e}")
                continue
                
        return jobs
        
    async def _extract_job_card_data(self, card) -> Optional[JobCreate]:
        """Extract data from a single job card"""
        try:
            # Click on card to load details
            await card.click()
            await asyncio.sleep(random.uniform(1, 2))
            
            # Extract basic info
            title_el = await self.page.query_selector('.job-details-jobs-unified-top-card__job-title')
            company_el = await self.page.query_selector('.job-details-jobs-unified-top-card__company-name')
            location_el = await self.page.query_selector('.job-details-jobs-unified-top-card__bullet')
            
            title = await title_el.inner_text() if title_el else None
            company = await company_el.inner_text() if company_el else None
            location = await location_el.inner_text() if location_el else None
            
            if not title or not company:
                return None
                
            # Get job URL
            job_url = self.page.url
            source_job_id = self._extract_job_id(job_url)
            
            # Check for Easy Apply
            easy_apply_btn = await self.page.query_selector('.jobs-apply-button--top-card')
            easy_apply = easy_apply_btn is not None
            
            # Extract description
            desc_el = await self.page.query_selector('.jobs-description__content')
            description = await desc_el.inner_text() if desc_el else ""
            
            # Extract salary if present
            salary_el = await self.page.query_selector('.job-details-jobs-unified-top-card__job-insight')
            salary_text = await salary_el.inner_text() if salary_el else None
            
            # Extract posted date
            posted_el = await self.page.query_selector('.job-details-jobs-unified-top-card__posted-date')
            posted_text = await posted_el.inner_text() if posted_el else None
            
            return JobCreate(
                source='linkedin',
                source_job_id=source_job_id,
                source_url=job_url,
                title=title.strip(),
                company_name=company.strip(),
                location=location.strip() if location else None,
                description=description,
                salary_text=salary_text,
                easy_apply_available=easy_apply,
                posted_at=self._parse_posted_date(posted_text),
            )
            
        except Exception as e:
            logger.error(f"Error extracting job data: {e}")
            return None
            
    def _build_search_url(self, params: dict) -> str:
        """Build LinkedIn search URL"""
        base_url = "https://www.linkedin.com/jobs/search/?"
        query_params = "&".join([f"{k}={v}" for k, v in params.items() if v])
        return base_url + query_params
        
    def _extract_job_id(self, url: str) -> str:
        """Extract job ID from URL"""
        import re
        match = re.search(r'/jobs/view/(\d+)', url)
        return match.group(1) if match else url
        
    def _parse_posted_date(self, text: str) -> Optional[datetime]:
        """Parse posted date from text like '2 days ago'"""
        if not text:
            return None
        # Implementation for parsing relative dates
        # ...
        return datetime.utcnow()
        
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
```

### 2. LinkedIn Easy Apply (worker/scrapers/linkedin_applicator.py)

```python
"""
LinkedIn Easy Apply Automation

Handles the complete Easy Apply flow including:
- Multi-step form filling
- Resume upload
- Cover letter attachment
- Screening question answering
- Screenshot capture
"""

import asyncio
import random
from typing import Dict, List, Optional, Tuple
from playwright.async_api import Page
from app.models.application import Application
from app.services.llm_service import LLMService
from worker.automation.form_filler import FormFiller
from worker.automation.screenshot_manager import ScreenshotManager
import logging

logger = logging.getLogger(__name__)

class LinkedInApplicator:
    def __init__(
        self,
        page: Page,
        user_profile: dict,
        resume_path: str,
        llm_service: LLMService
    ):
        self.page = page
        self.user_profile = user_profile
        self.resume_path = resume_path
        self.llm = llm_service
        self.form_filler = FormFiller(user_profile)
        self.screenshot_manager = ScreenshotManager()
        
    async def apply_to_job(
        self,
        job_url: str,
        cover_letter: Optional[str] = None,
        additional_answers: Optional[Dict] = None
    ) -> Tuple[bool, List[str], Optional[str]]:
        """
        Apply to a job via Easy Apply
        
        Returns:
            Tuple of (success, screenshot_urls, error_message)
        """
        screenshots = []
        
        try:
            # Navigate to job
            await self.page.goto(job_url)
            await asyncio.sleep(random.uniform(2, 3))
            
            # Take initial screenshot
            screenshots.append(await self.screenshot_manager.capture(self.page, "job_page"))
            
            # Find and click Easy Apply button
            easy_apply_btn = await self._find_easy_apply_button()
            if not easy_apply_btn:
                return False, screenshots, "Easy Apply button not found"
                
            await easy_apply_btn.click()
            await asyncio.sleep(random.uniform(1, 2))
            
            # Process application modal
            step = 1
            max_steps = 10  # Safety limit
            
            while step <= max_steps:
                logger.info(f"Processing Easy Apply step {step}")
                
                # Take screenshot of current step
                screenshots.append(
                    await self.screenshot_manager.capture(self.page, f"step_{step}")
                )
                
                # Check if we're done
                if await self._check_application_submitted():
                    logger.info("Application submitted successfully!")
                    screenshots.append(
                        await self.screenshot_manager.capture(self.page, "confirmation")
                    )
                    return True, screenshots, None
                    
                # Fill current step
                await self._fill_current_step(cover_letter, additional_answers)
                
                # Click next/submit
                clicked = await self._click_next_or_submit()
                if not clicked:
                    return False, screenshots, "Could not find next/submit button"
                    
                await asyncio.sleep(random.uniform(1, 2))
                step += 1
                
            return False, screenshots, "Exceeded maximum steps"
            
        except Exception as e:
            logger.error(f"Error during Easy Apply: {e}")
            screenshots.append(
                await self.screenshot_manager.capture(self.page, "error")
            )
            return False, screenshots, str(e)
            
    async def _find_easy_apply_button(self):
        """Find the Easy Apply button"""
        selectors = [
            'button.jobs-apply-button',
            'button[aria-label*="Easy Apply"]',
            '.jobs-apply-button--top-card',
        ]
        
        for selector in selectors:
            btn = await self.page.query_selector(selector)
            if btn:
                return btn
        return None
        
    async def _check_application_submitted(self) -> bool:
        """Check if application was submitted"""
        success_indicators = [
            'text="Application sent"',
            'text="Your application was sent"',
            '.artdeco-modal__header:has-text("Application sent")',
        ]
        
        for indicator in success_indicators:
            if await self.page.query_selector(indicator):
                return True
        return False
        
    async def _fill_current_step(
        self,
        cover_letter: Optional[str],
        additional_answers: Optional[Dict]
    ):
        """Fill all fields in the current step"""
        
        # Handle contact info fields
        await self._fill_contact_info()
        
        # Handle resume upload
        await self._handle_resume_upload()
        
        # Handle cover letter
        if cover_letter:
            await self._handle_cover_letter(cover_letter)
            
        # Handle screening questions
        await self._answer_screening_questions(additional_answers)
        
        # Handle work authorization questions
        await self._handle_work_authorization()
        
    async def _fill_contact_info(self):
        """Fill contact information fields"""
        field_mapping = {
            'input[name*="firstName"], input[id*="firstName"]': self.user_profile.get('first_name'),
            'input[name*="lastName"], input[id*="lastName"]': self.user_profile.get('last_name'),
            'input[name*="email"], input[id*="email"], input[type="email"]': self.user_profile.get('email'),
            'input[name*="phone"], input[id*="phone"], input[type="tel"]': self.user_profile.get('phone'),
            'input[name*="city"], input[id*="city"]': self.user_profile.get('city'),
        }
        
        for selector, value in field_mapping.items():
            if value:
                field = await self.page.query_selector(selector)
                if field:
                    await field.fill('')
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    await field.fill(value)
                    await asyncio.sleep(random.uniform(0.2, 0.5))
                    
    async def _handle_resume_upload(self):
        """Handle resume upload if requested"""
        upload_input = await self.page.query_selector('input[type="file"]')
        if upload_input:
            await upload_input.set_input_files(self.resume_path)
            await asyncio.sleep(random.uniform(1, 2))
            
    async def _handle_cover_letter(self, cover_letter: str):
        """Handle cover letter textarea"""
        cover_letter_selectors = [
            'textarea[name*="coverLetter"]',
            'textarea[id*="coverLetter"]',
            'textarea[aria-label*="cover letter"]',
            '.jobs-easy-apply-form-section__grouping textarea',
        ]
        
        for selector in cover_letter_selectors:
            textarea = await self.page.query_selector(selector)
            if textarea:
                await textarea.fill(cover_letter)
                await asyncio.sleep(random.uniform(0.5, 1))
                return
                
    async def _answer_screening_questions(self, additional_answers: Optional[Dict]):
        """Answer screening questions using AI"""
        # Find all question containers
        questions = await self.page.query_selector_all(
            '.jobs-easy-apply-form-section__grouping'
        )
        
        for question_container in questions:
            await self._answer_single_question(question_container, additional_answers)
            
    async def _answer_single_question(self, container, additional_answers: Optional[Dict]):
        """Answer a single screening question"""
        # Get question text
        label = await container.query_selector('label, .fb-dash-form-element__label')
        if not label:
            return
            
        question_text = await label.inner_text()
        
        # Check if we have a pre-defined answer
        if additional_answers and question_text in additional_answers:
            answer = additional_answers[question_text]
        else:
            # Use AI to generate answer
            answer = await self._generate_answer(question_text)
            
        # Find input type and fill
        text_input = await container.query_selector('input[type="text"], input:not([type])')
        number_input = await container.query_selector('input[type="number"]')
        textarea = await container.query_selector('textarea')
        select = await container.query_selector('select')
        radio_buttons = await container.query_selector_all('input[type="radio"]')
        checkboxes = await container.query_selector_all('input[type="checkbox"]')
        
        if text_input:
            await text_input.fill(str(answer))
        elif number_input:
            await number_input.fill(str(answer))
        elif textarea:
            await textarea.fill(str(answer))
        elif select:
            await self._handle_select(select, answer)
        elif radio_buttons:
            await self._handle_radio(radio_buttons, answer)
        elif checkboxes:
            await self._handle_checkboxes(checkboxes, answer)
            
        await asyncio.sleep(random.uniform(0.3, 0.7))
        
    async def _generate_answer(self, question: str) -> str:
        """Use AI to generate answer for screening question"""
        prompt = f"""
        You are helping fill out a job application. Answer this screening question based on the candidate's profile.
        
        Candidate Profile:
        - Name: {self.user_profile.get('full_name')}
        - Experience: {self.user_profile.get('years_experience')} years
        - Skills: {', '.join(self.user_profile.get('skills', []))}
        - Current Title: {self.user_profile.get('current_title')}
        
        Question: {question}
        
        Provide a concise, professional answer. If it's a yes/no question, answer with just "Yes" or "No".
        If it's asking for years of experience with something, provide a number.
        If it's a text question, keep the answer under 200 characters.
        
        Answer:
        """
        
        response = await self.llm.generate(prompt, max_tokens=100)
        return response.strip()
        
    async def _handle_select(self, select, answer):
        """Handle dropdown selection"""
        options = await select.query_selector_all('option')
        for option in options:
            option_text = await option.inner_text()
            if answer.lower() in option_text.lower():
                value = await option.get_attribute('value')
                await select.select_option(value)
                return
        # Select first non-empty option as fallback
        if len(options) > 1:
            value = await options[1].get_attribute('value')
            await select.select_option(value)
            
    async def _handle_radio(self, radio_buttons, answer):
        """Handle radio button selection"""
        for radio in radio_buttons:
            label = await radio.evaluate('el => el.closest("label")?.innerText || el.nextSibling?.textContent')
            if label and answer.lower() in label.lower():
                await radio.click()
                return
        # Click first option as fallback
        if radio_buttons:
            await radio_buttons[0].click()
            
    async def _handle_checkboxes(self, checkboxes, answer):
        """Handle checkbox selection"""
        for checkbox in checkboxes:
            label = await checkbox.evaluate('el => el.closest("label")?.innerText')
            if label and answer.lower() in label.lower():
                await checkbox.click()
                
    async def _handle_work_authorization(self):
        """Handle work authorization questions"""
        auth_questions = {
            'authorized to work': self.user_profile.get('work_authorized', True),
            'sponsorship': not self.user_profile.get('needs_sponsorship', False),
            'legally authorized': self.user_profile.get('work_authorized', True),
        }
        
        # Find relevant questions and answer
        questions = await self.page.query_selector_all('.jobs-easy-apply-form-section__grouping')
        for q in questions:
            text = await q.inner_text()
            text_lower = text.lower()
            
            for keyword, answer in auth_questions.items():
                if keyword in text_lower:
                    # Find Yes/No radio or checkbox
                    yes_option = await q.query_selector('input[value="Yes"], label:has-text("Yes") input')
                    no_option = await q.query_selector('input[value="No"], label:has-text("No") input')
                    
                    if answer and yes_option:
                        await yes_option.click()
                    elif not answer and no_option:
                        await no_option.click()
                        
    async def _click_next_or_submit(self) -> bool:
        """Click Next or Submit button"""
        button_selectors = [
            'button[aria-label="Submit application"]',
            'button[aria-label="Continue to next step"]',
            'button[aria-label="Review your application"]',
            'button:has-text("Submit application")',
            'button:has-text("Next")',
            'button:has-text("Review")',
            'button:has-text("Submit")',
        ]
        
        for selector in button_selectors:
            btn = await self.page.query_selector(selector)
            if btn and await btn.is_visible():
                await btn.click()
                return True
                
        return False
```

### 3. Cover Letter Generator (worker/ai/cover_letter_generator.py)

```python
"""
AI-Powered Cover Letter Generator

Generates highly personalized cover letters using:
- User's resume and experience
- Job description and requirements
- Company research
- Hiring manager information (if available)
"""

from typing import Optional
from app.services.llm_service import LLMService
from app.schemas.job import Job
from app.schemas.profile import UserProfile
import logging

logger = logging.getLogger(__name__)

class CoverLetterGenerator:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
        
    async def generate(
        self,
        user_profile: UserProfile,
        resume_text: str,
        job: Job,
        company_research: Optional[dict] = None,
        hiring_manager: Optional[dict] = None,
        tone: str = "professional",  # professional, casual, enthusiastic
        max_length: int = 300,  # words
    ) -> str:
        """Generate a personalized cover letter"""
        
        # Build context
        context = self._build_context(
            user_profile, resume_text, job, company_research, hiring_manager
        )
        
        prompt = f"""
You are an expert career coach and professional writer. Write a compelling, personalized cover letter for a job application.

IMPORTANT GUIDELINES:
1. Be specific and personal - reference actual details from the job and company
2. Show genuine interest in THIS specific role and company
3. Highlight 2-3 most relevant achievements/skills that match the job
4. Keep it concise - {max_length} words maximum
5. Tone should be {tone}
6. Do NOT use generic phrases like "I am writing to express my interest"
7. Do NOT repeat the job title verbatim - show you understand the role
8. Include a specific example or achievement with metrics if possible
9. End with a clear call to action

{context}

Write the cover letter now. Start directly with a compelling opening line - no "Dear Hiring Manager" needed as that will be added separately.
"""

        cover_letter = await self.llm.generate(
            prompt,
            max_tokens=600,
            temperature=0.7
        )
        
        # Clean up and format
        cover_letter = self._clean_cover_letter(cover_letter)
        
        # Add greeting if hiring manager known
        if hiring_manager and hiring_manager.get('name'):
            greeting = f"Hi {hiring_manager['name'].split()[0]},"
        else:
            greeting = "Hi there,"
            
        # Add signature
        signature = f"\n\nBest regards,\n{user_profile.first_name} {user_profile.last_name}"
        
        return f"{greeting}\n\n{cover_letter}{signature}"
        
    def _build_context(
        self,
        user_profile: UserProfile,
        resume_text: str,
        job: Job,
        company_research: Optional[dict],
        hiring_manager: Optional[dict]
    ) -> str:
        """Build context string for the prompt"""
        
        context_parts = []
        
        # User info
        context_parts.append(f"""
CANDIDATE INFORMATION:
- Name: {user_profile.first_name} {user_profile.last_name}
- Current Role: {user_profile.current_title or 'Not specified'}
- Years of Experience: {user_profile.total_years_experience or 'Not specified'}
- Location: {user_profile.current_city}, {user_profile.current_country}
""")
        
        # Resume highlights
        context_parts.append(f"""
RESUME CONTENT:
{resume_text[:2000]}  # Truncate if too long
""")
        
        # Job details
        context_parts.append(f"""
JOB DETAILS:
- Title: {job.title}
- Company: {job.company_name}
- Location: {job.location}
- Job Type: {job.job_type or 'Full-time'}

Job Description:
{job.description[:2000]}  # Truncate if too long
""")
        
        # Company research
        if company_research:
            research_str = f"""
COMPANY RESEARCH:
- Industry: {company_research.get('industry', 'Unknown')}
- Size: {company_research.get('size', 'Unknown')}
- Recent News: {company_research.get('recent_news', 'None available')}
- Tech Stack: {', '.join(company_research.get('tech_stack', [])) or 'Unknown'}
- Company Values: {company_research.get('values', 'Unknown')}
- Recent Funding: {company_research.get('funding', 'Unknown')}
"""
            context_parts.append(research_str)
            
        # Hiring manager info
        if hiring_manager:
            hm_str = f"""
HIRING MANAGER:
- Name: {hiring_manager.get('name', 'Unknown')}
- Title: {hiring_manager.get('title', 'Unknown')}
- Recent LinkedIn Activity: {hiring_manager.get('recent_posts', 'None available')}
"""
            context_parts.append(hm_str)
            
        return "\n".join(context_parts)
        
    def _clean_cover_letter(self, text: str) -> str:
        """Clean up generated cover letter"""
        # Remove any markdown formatting
        text = text.replace('**', '').replace('*', '')
        
        # Remove any accidental greetings the AI added
        lines = text.strip().split('\n')
        if lines[0].lower().startswith(('dear', 'hi ', 'hello', 'to whom')):
            lines = lines[1:]
            
        # Remove any accidental signatures
        clean_lines = []
        for line in lines:
            if line.lower().startswith(('sincerely', 'best regards', 'regards', 'best,')):
                break
            clean_lines.append(line)
            
        return '\n'.join(clean_lines).strip()


class EmailGenerator:
    """Generate cold outreach emails"""
    
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
        
    async def generate_initial_email(
        self,
        user_profile: dict,
        resume_text: str,
        job: dict,
        company_research: dict,
        hiring_manager: dict,
    ) -> dict:
        """Generate initial cold email"""
        
        prompt = f"""
You are an expert at writing cold outreach emails that get responses. Write a cold email to a hiring manager about a job opportunity.

CRITICAL RULES:
1. Subject line must be intriguing but not clickbait (under 50 chars)
2. Email must be SHORT - under 150 words
3. First line must be personalized (reference their work, company news, or LinkedIn post)
4. Show clear value - what can you do for THEM
5. End with a soft CTA (not "let me know if interested")
6. NO attachments mentioned in body (resume attached separately)
7. Sound human, not like a template

CANDIDATE:
- Name: {user_profile.get('full_name')}
- Current Role: {user_profile.get('current_title')}
- Key Achievement: {user_profile.get('top_achievement', 'Not specified')}
- Relevant Experience: {resume_text[:1000]}

JOB:
- Title: {job.get('title')}
- Company: {job.get('company_name')}

COMPANY RESEARCH:
- Recent News: {company_research.get('recent_news', 'None')}
- Tech Stack: {company_research.get('tech_stack', [])}

HIRING MANAGER:
- Name: {hiring_manager.get('name')}
- Title: {hiring_manager.get('title')}
- Recent LinkedIn Post: {hiring_manager.get('recent_post', 'None')}

Write the email now. Format as:
SUBJECT: [subject line]
BODY:
[email body]
"""

        response = await self.llm.generate(prompt, max_tokens=400, temperature=0.7)
        
        # Parse response
        lines = response.strip().split('\n')
        subject = ""
        body_lines = []
        in_body = False
        
        for line in lines:
            if line.startswith('SUBJECT:'):
                subject = line.replace('SUBJECT:', '').strip()
            elif line.startswith('BODY:'):
                in_body = True
            elif in_body:
                body_lines.append(line)
                
        body = '\n'.join(body_lines).strip()
        
        # Add signature
        body += f"\n\nBest,\n{user_profile.get('full_name')}"
        
        return {
            'subject': subject,
            'body': body
        }
        
    async def generate_followup_email(
        self,
        original_email: dict,
        followup_number: int,
        user_profile: dict,
        job: dict,
    ) -> dict:
        """Generate follow-up email"""
        
        if followup_number == 1:
            prompt = f"""
Write a follow-up email (first follow-up, 3 days after initial).

RULES:
1. Reference the original email briefly
2. Add ONE new piece of value (article, insight, or additional achievement)
3. Keep it under 75 words
4. Friendly but not pushy

Original subject: {original_email.get('subject')}
Job: {job.get('title')} at {job.get('company_name')}
Candidate: {user_profile.get('full_name')}

Format as:
SUBJECT: [subject - can be "Re: original subject" or new]
BODY: [email body]
"""
        elif followup_number == 2:
            prompt = f"""
Write a final follow-up email (second follow-up, 7 days after initial).

RULES:
1. Acknowledge they're busy
2. One final value proposition
3. Make it easy to say no (reduces pressure, increases responses)
4. Under 50 words
5. This is the "breakup" email

Original subject: {original_email.get('subject')}
Job: {job.get('title')} at {job.get('company_name')}
Candidate: {user_profile.get('full_name')}

Format as:
SUBJECT: [subject]
BODY: [email body]
"""
        
        response = await self.llm.generate(prompt, max_tokens=200, temperature=0.7)
        
        # Parse response (same as initial)
        lines = response.strip().split('\n')
        subject = ""
        body_lines = []
        in_body = False
        
        for line in lines:
            if line.startswith('SUBJECT:'):
                subject = line.replace('SUBJECT:', '').strip()
            elif line.startswith('BODY:'):
                in_body = True
            elif in_body:
                body_lines.append(line)
                
        body = '\n'.join(body_lines).strip()
        body += f"\n\n{user_profile.get('full_name')}"
        
        return {
            'subject': subject,
            'body': body
        }
```

### 4. Naukri.com Scraper (worker/scrapers/naukri_scraper.py)

```python
"""
Naukri.com Job Scraper

Scrapes jobs from Naukri.com (India's largest job portal)
Handles login, search, and job extraction.
"""

import asyncio
import random
from datetime import datetime
from typing import List, Optional
from playwright.async_api import async_playwright, Page, Browser
from app.schemas.job import JobCreate
from worker.automation.session_manager import SessionManager
import logging

logger = logging.getLogger(__name__)

class NaukriScraper:
    def __init__(self, user_id: str, credentials: dict):
        self.user_id = user_id
        self.credentials = credentials
        self.session_manager = SessionManager("naukri", user_id)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.base_url = "https://www.naukri.com"
        
    async def initialize(self):
        """Initialize browser"""
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        self.page = await context.new_page()
        
        # Restore session if available
        cookies = await self.session_manager.get_cookies()
        if cookies:
            await context.add_cookies(cookies)
            
    async def login(self) -> bool:
        """Login to Naukri.com"""
        await self.page.goto(f"{self.base_url}/nlogin/login")
        await asyncio.sleep(random.uniform(1, 2))
        
        # Check if already logged in
        if await self._is_logged_in():
            logger.info("Already logged in to Naukri")
            return True
            
        # Fill login form
        await self.page.fill('input[placeholder="Enter your active Email ID / Username"]', 
                            self.credentials['email'])
        await asyncio.sleep(random.uniform(0.3, 0.6))
        
        await self.page.fill('input[placeholder="Enter your password"]',
                            self.credentials['password'])
        await asyncio.sleep(random.uniform(0.3, 0.6))
        
        # Click login button
        await self.page.click('button[type="submit"]')
        await asyncio.sleep(random.uniform(3, 5))
        
        # Verify login
        if await self._is_logged_in():
            cookies = await self.page.context.cookies()
            await self.session_manager.save_cookies(cookies)
            logger.info("Naukri login successful")
            return True
            
        logger.error("Naukri login failed")
        return False
        
    async def _is_logged_in(self) -> bool:
        """Check if user is logged in"""
        # Check for logged-in indicators
        profile_icon = await self.page.query_selector('.nI-gNb-drawer__icon')
        return profile_icon is not None
        
    async def search_jobs(
        self,
        keywords: List[str],
        locations: List[str],
        experience_min: int = 0,
        experience_max: int = 30,
        salary_min: int = 0,
        freshness: int = 7,  # Days
        max_jobs: int = 100
    ) -> List[JobCreate]:
        """Search for jobs on Naukri"""
        jobs = []
        
        for keyword in keywords:
            for location in locations:
                query_jobs = await self._search_single_query(
                    keyword=keyword,
                    location=location,
                    experience_min=experience_min,
                    experience_max=experience_max,
                    salary_min=salary_min,
                    freshness=freshness,
                    max_jobs=max_jobs // (len(keywords) * len(locations))
                )
                jobs.extend(query_jobs)
                await asyncio.sleep(random.uniform(3, 6))
                
        return jobs
        
    async def _search_single_query(
        self,
        keyword: str,
        location: str,
        experience_min: int,
        experience_max: int,
        salary_min: int,
        freshness: int,
        max_jobs: int
    ) -> List[JobCreate]:
        """Execute single search query"""
        jobs = []
        
        # Build search URL
        search_url = (
            f"{self.base_url}/{keyword.replace(' ', '-')}-jobs-in-{location.replace(' ', '-')}?"
            f"k={keyword}&l={location}"
            f"&experience={experience_min}"
            f"&nignbeam_channel=jobsearchDe498702702"
        )
        
        await self.page.goto(search_url)
        await asyncio.sleep(random.uniform(2, 4))
        
        page_num = 0
        while len(jobs) < max_jobs:
            # Extract jobs from current page
            page_jobs = await self._extract_jobs_from_page()
            jobs.extend(page_jobs)
            
            logger.info(f"Naukri: Scraped {len(page_jobs)} jobs from page {page_num + 1}")
            
            # Go to next page
            next_btn = await self.page.query_selector('a.fright.fs14.btn-secondary.br2')
            if not next_btn:
                break
                
            await next_btn.click()
            await asyncio.sleep(random.uniform(2, 4))
            page_num += 1
            
            if page_num >= 5:  # Limit pages
                break
                
        return jobs[:max_jobs]
        
    async def _extract_jobs_from_page(self) -> List[JobCreate]:
        """Extract jobs from current page"""
        jobs = []
        
        job_cards = await self.page.query_selector_all('article.jobTuple')
        
        for card in job_cards:
            try:
                job = await self._extract_job_card(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.error(f"Error extracting Naukri job: {e}")
                continue
                
        return jobs
        
    async def _extract_job_card(self, card) -> Optional[JobCreate]:
        """Extract data from job card"""
        try:
            # Title and URL
            title_el = await card.query_selector('a.title')
            title = await title_el.inner_text() if title_el else None
            job_url = await title_el.get_attribute('href') if title_el else None
            
            # Company
            company_el = await card.query_selector('a.subTitle')
            company = await company_el.inner_text() if company_el else None
            
            # Experience
            exp_el = await card.query_selector('.ellipsis.expwdth')
            experience = await exp_el.inner_text() if exp_el else None
            
            # Salary
            salary_el = await card.query_selector('.ellipsis.salary')
            salary = await salary_el.inner_text() if salary_el else None
            
            # Location
            loc_el = await card.query_selector('.ellipsis.loc')
            location = await loc_el.inner_text() if loc_el else None
            
            # Description snippet
            desc_el = await card.query_selector('.job-description')
            description = await desc_el.inner_text() if desc_el else ""
            
            # Skills
            skills_els = await card.query_selector_all('.tags-gt li')
            skills = [await s.inner_text() for s in skills_els]
            
            # Posted date
            posted_el = await card.query_selector('.type br+ span')
            posted_text = await posted_el.inner_text() if posted_el else None
            
            if not title or not company:
                return None
                
            # Extract job ID from URL
            source_job_id = job_url.split('/')[-1].split('?')[0] if job_url else None
            
            return JobCreate(
                source='naukri',
                source_job_id=source_job_id,
                source_url=job_url,
                title=title.strip(),
                company_name=company.strip(),
                location=location.strip() if location else None,
                description=description,
                salary_text=salary,
                experience_text=experience,
                required_skills=skills,
                posted_at=self._parse_posted_date(posted_text),
            )
            
        except Exception as e:
            logger.error(f"Error parsing Naukri job card: {e}")
            return None
            
    def _parse_posted_date(self, text: str) -> Optional[datetime]:
        """Parse posted date"""
        if not text:
            return None
        # Handle "X days ago", "Today", "Just now", etc.
        return datetime.utcnow()
        
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()


class NaukriApplicator:
    """Apply to jobs on Naukri.com"""
    
    def __init__(self, page: Page, user_profile: dict):
        self.page = page
        self.user_profile = user_profile
        
    async def apply_to_job(self, job_url: str) -> tuple[bool, List[str], Optional[str]]:
        """Apply to a job on Naukri"""
        screenshots = []
        
        try:
            await self.page.goto(job_url)
            await asyncio.sleep(random.uniform(2, 3))
            
            # Take screenshot
            screenshots.append(await self._take_screenshot("job_page"))
            
            # Find apply button
            apply_btn = await self.page.query_selector('button.apply-button, button:has-text("Apply")')
            
            if not apply_btn:
                return False, screenshots, "Apply button not found"
                
            # Check if already applied
            btn_text = await apply_btn.inner_text()
            if 'applied' in btn_text.lower():
                return False, screenshots, "Already applied"
                
            # Click apply
            await apply_btn.click()
            await asyncio.sleep(random.uniform(2, 3))
            
            # Handle any popups or additional forms
            await self._handle_apply_popup()
            
            screenshots.append(await self._take_screenshot("after_apply"))
            
            # Verify application
            success = await self._verify_application()
            
            if success:
                return True, screenshots, None
            else:
                return False, screenshots, "Could not verify application"
                
        except Exception as e:
            logger.error(f"Error applying on Naukri: {e}")
            return False, screenshots, str(e)
            
    async def _handle_apply_popup(self):
        """Handle any popups after clicking apply"""
        # Check for update profile popup
        update_popup = await self.page.query_selector('.chatbot-popup, .update-profile-popup')
        if update_popup:
            close_btn = await update_popup.query_selector('button.close, .close-icon')
            if close_btn:
                await close_btn.click()
                await asyncio.sleep(1)
                
        # Check for questionnaire
        questionnaire = await self.page.query_selector('.screening-questions')
        if questionnaire:
            await self._fill_questionnaire(questionnaire)
            
    async def _fill_questionnaire(self, container):
        """Fill screening questionnaire"""
        questions = await container.query_selector_all('.question-item')
        
        for q in questions:
            input_field = await q.query_selector('input, textarea, select')
            if input_field:
                input_type = await input_field.get_attribute('type')
                
                if input_type == 'text':
                    # Fill with relevant info from profile
                    await input_field.fill(str(self.user_profile.get('years_experience', '5')))
                elif input_type == 'radio':
                    # Click first option
                    await input_field.click()
                    
        # Submit questionnaire
        submit_btn = await container.query_selector('button[type="submit"]')
        if submit_btn:
            await submit_btn.click()
            await asyncio.sleep(2)
            
    async def _verify_application(self) -> bool:
        """Verify if application was successful"""
        success_indicators = [
            'text="Application Sent"',
            'text="Applied Successfully"',
            'text="You have already applied"',
            '.application-success',
        ]
        
        for indicator in success_indicators:
            if await self.page.query_selector(indicator):
                return True
        return False
        
    async def _take_screenshot(self, name: str) -> str:
        """Take screenshot and return URL"""
        # Implementation to capture and upload screenshot
        screenshot_bytes = await self.page.screenshot()
        # Upload to S3 and return URL
        return f"screenshots/{name}.png"
```

### 5. Cold Email Sender (worker/email/email_sender.py)

```python
"""
Cold Email Sender

Handles sending cold emails with:
- SendGrid / AWS SES integration
- Open/click tracking
- Rate limiting
- Deliverability best practices
"""

import asyncio
from datetime import datetime
from typing import Optional
import sendgrid
from sendgrid.helpers.mail import (
    Mail, Email, To, Content, Attachment, 
    FileContent, FileName, FileType, Disposition,
    TrackingSettings, ClickTracking, OpenTracking
)
import base64
from app.config import settings
from app.models.application import Application
from app.db.session import get_db
import logging

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self):
        self.sg_client = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        
    async def send_cold_email(
        self,
        to_email: str,
        from_email: str,
        from_name: str,
        subject: str,
        body: str,
        resume_path: Optional[str] = None,
        application_id: Optional[str] = None,
    ) -> dict:
        """Send a cold email with optional resume attachment"""
        
        try:
            # Create message
            message = Mail(
                from_email=Email(from_email, from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=self._format_html_body(body)
            )
            
            # Add plain text version
            message.add_content(Content("text/plain", body))
            
            # Add tracking
            tracking = TrackingSettings()
            tracking.click_tracking = ClickTracking(True, True)
            tracking.open_tracking = OpenTracking(
                True, 
                f"https://api.yourdomain.com/api/v1/email/track/open/{application_id}"
            )
            message.tracking_settings = tracking
            
            # Add custom headers for tracking
            message.header = {
                'X-Application-ID': application_id,
                'X-Campaign': 'job-outreach'
            }
            
            # Attach resume if provided
            if resume_path:
                attachment = await self._create_attachment(resume_path)
                message.add_attachment(attachment)
                
            # Send email
            response = self.sg_client.send(message)
            
            logger.info(f"Email sent to {to_email}, status: {response.status_code}")
            
            return {
                'success': response.status_code in [200, 201, 202],
                'message_id': response.headers.get('X-Message-Id'),
                'status_code': response.status_code
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    def _format_html_body(self, text: str) -> str:
        """Convert plain text to HTML"""
        # Convert line breaks to <br>
        html = text.replace('\n', '<br>')
        
        # Wrap in basic HTML
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
            {html}
        </body>
        </html>
        """
        
    async def _create_attachment(self, file_path: str) -> Attachment:
        """Create email attachment from file"""
        # Read file (from S3 or local)
        with open(file_path, 'rb') as f:
            file_data = f.read()
            
        encoded = base64.b64encode(file_data).decode()
        
        attachment = Attachment()
        attachment.file_content = FileContent(encoded)
        attachment.file_type = FileType('application/pdf')
        attachment.file_name = FileName('Resume.pdf')
        attachment.disposition = Disposition('attachment')
        
        return attachment
        
    async def send_followup(
        self,
        application_id: str,
        followup_number: int,
    ) -> dict:
        """Send follow-up email for an application"""
        
        async with get_db() as db:
            # Get application details
            application = await db.get(Application, application_id)
            if not application:
                return {'success': False, 'error': 'Application not found'}
                
            # Check if we should send followup
            if application.followup_stopped:
                return {'success': False, 'error': 'Followups stopped'}
                
            if application.email_replied:
                return {'success': False, 'error': 'Already received reply'}
                
            # Get scheduled followup content
            followup = await db.query(ScheduledFollowup).filter(
                ScheduledFollowup.application_id == application_id,
                ScheduledFollowup.followup_number == followup_number,
                ScheduledFollowup.status == 'scheduled'
            ).first()
            
            if not followup:
                return {'success': False, 'error': 'Followup not found'}
                
            # Send the followup
            result = await self.send_cold_email(
                to_email=application.email_sent_to,
                from_email=application.user.email_settings.email_address,
                from_name=application.user.full_name,
                subject=followup.subject,
                body=followup.body,
                application_id=application_id
            )
            
            # Update followup status
            if result['success']:
                followup.status = 'sent'
                followup.sent_at = datetime.utcnow()
                application.followup_count += 1
                application.last_followup_at = datetime.utcnow()
                await db.commit()
                
            return result


class EmailTracker:
    """Track email opens and clicks"""
    
    async def record_open(self, application_id: str, ip: str, user_agent: str):
        """Record email open event"""
        async with get_db() as db:
            application = await db.get(Application, application_id)
            if application and not application.email_opened:
                application.email_opened = True
                application.email_opened_at = datetime.utcnow()
                
                # Create event record
                event = EmailEvent(
                    application_id=application_id,
                    event_type='opened',
                    ip_address=ip,
                    user_agent=user_agent
                )
                db.add(event)
                await db.commit()
                
    async def record_click(self, application_id: str, url: str, ip: str, user_agent: str):
        """Record link click event"""
        async with get_db() as db:
            application = await db.get(Application, application_id)
            if application:
                application.email_clicked = True
                application.email_clicked_at = datetime.utcnow()
                
                event = EmailEvent(
                    application_id=application_id,
                    event_type='clicked',
                    event_data={'url': url},
                    ip_address=ip,
                    user_agent=user_agent
                )
                db.add(event)
                await db.commit()
```

### 6. Email Finder (worker/utils/email_finder.py)

```python
"""
Email Finder

Finds email addresses using:
- Hunter.io API
- Email pattern guessing
- Email verification
"""

import asyncio
import httpx
from typing import Optional, List
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class EmailFinder:
    def __init__(self):
        self.hunter_api_key = settings.HUNTER_API_KEY
        self.zerobounce_api_key = settings.ZEROBOUNCE_API_KEY
        
    async def find_email(
        self,
        first_name: str,
        last_name: str,
        company_domain: str,
    ) -> Optional[dict]:
        """Find email address for a person at a company"""
        
        # Try Hunter.io first
        hunter_result = await self._hunter_find(first_name, last_name, company_domain)
        if hunter_result and hunter_result.get('email'):
            # Verify the email
            is_valid = await self._verify_email(hunter_result['email'])
            if is_valid:
                return {
                    'email': hunter_result['email'],
                    'confidence': hunter_result.get('confidence', 0),
                    'source': 'hunter',
                    'verified': True
                }
                
        # Fallback to pattern guessing
        pattern = await self._get_company_pattern(company_domain)
        guessed_emails = self._generate_email_variations(first_name, last_name, company_domain, pattern)
        
        # Verify each guess
        for email in guessed_emails:
            is_valid = await self._verify_email(email)
            if is_valid:
                return {
                    'email': email,
                    'confidence': 70,
                    'source': 'pattern_guess',
                    'verified': True
                }
                
        return None
        
    async def _hunter_find(self, first_name: str, last_name: str, domain: str) -> Optional[dict]:
        """Use Hunter.io to find email"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.hunter.io/v2/email-finder",
                    params={
                        'domain': domain,
                        'first_name': first_name,
                        'last_name': last_name,
                        'api_key': self.hunter_api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data', {}).get('email'):
                        return {
                            'email': data['data']['email'],
                            'confidence': data['data'].get('score', 0)
                        }
        except Exception as e:
            logger.error(f"Hunter.io error: {e}")
            
        return None
        
    async def _get_company_pattern(self, domain: str) -> Optional[str]:
        """Get email pattern for a company from Hunter.io"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.hunter.io/v2/domain-search",
                    params={
                        'domain': domain,
                        'api_key': self.hunter_api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('data', {}).get('pattern')
        except Exception as e:
            logger.error(f"Hunter.io pattern error: {e}")
            
        return None
        
    def _generate_email_variations(
        self,
        first_name: str,
        last_name: str,
        domain: str,
        pattern: Optional[str] = None
    ) -> List[str]:
        """Generate possible email variations"""
        first = first_name.lower().strip()
        last = last_name.lower().strip()
        
        # If we have a pattern, use it first
        if pattern:
            pattern_email = pattern.format(
                first=first, 
                last=last,
                f=first[0],
                l=last[0]
            )
            variations = [f"{pattern_email}@{domain}"]
        else:
            variations = []
            
        # Common patterns
        common_patterns = [
            f"{first}@{domain}",
            f"{first}.{last}@{domain}",
            f"{first}{last}@{domain}",
            f"{first[0]}{last}@{domain}",
            f"{first}{last[0]}@{domain}",
            f"{first[0]}.{last}@{domain}",
            f"{first}_{last}@{domain}",
            f"{last}.{first}@{domain}",
            f"{first}-{last}@{domain}",
        ]
        
        for p in common_patterns:
            if p not in variations:
                variations.append(p)
                
        return variations[:5]  # Limit to avoid too many API calls
        
    async def _verify_email(self, email: str) -> bool:
        """Verify if email is valid using ZeroBounce"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.zerobounce.net/v2/validate",
                    params={
                        'api_key': self.zerobounce_api_key,
                        'email': email
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', '').lower()
                    return status in ['valid', 'catch-all']
                    
        except Exception as e:
            logger.error(f"ZeroBounce error: {e}")
            
        # If verification fails, assume valid to not miss opportunities
        return True
```

---

## CELERY TASKS

### worker/celery_app.py

```python
"""Celery Configuration"""

from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    'jobpilot',
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL,
    include=[
        'worker.tasks.job_discovery',
        'worker.tasks.job_matching',
        'worker.tasks.application_task',
        'worker.tasks.email_task',
        'worker.tasks.followup_task',
        'worker.tasks.analytics_task',
        'worker.tasks.scheduled_tasks',
    ]
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'worker.tasks.application_task.*': {'queue': 'browser'},
        'worker.tasks.job_discovery.*': {'queue': 'scraping'},
        'worker.tasks.email_task.*': {'queue': 'emails'},
        '*': {'queue': 'default'},
    },
    
    # Task settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    
    # Beat schedule
    beat_schedule={
        # Discover new jobs every hour
        'discover-jobs-hourly': {
            'task': 'worker.tasks.job_discovery.discover_jobs_for_all_users',
            'schedule': crontab(minute=0),  # Every hour
        },
        # Process application queue every 5 minutes
        'process-application-queue': {
            'task': 'worker.tasks.application_task.process_queues',
            'schedule': crontab(minute='*/5'),
        },
        # Send scheduled follow-ups every hour
        'send-followups': {
            'task': 'worker.tasks.followup_task.send_scheduled_followups',
            'schedule': crontab(minute=30),  # Every hour at :30
        },
        # Update daily stats at midnight
        'update-daily-stats': {
            'task': 'worker.tasks.analytics_task.update_daily_stats',
            'schedule': crontab(hour=0, minute=5),
        },
        # Reset daily limits at midnight
        'reset-daily-limits': {
            'task': 'worker.tasks.scheduled_tasks.reset_daily_limits',
            'schedule': crontab(hour=0, minute=0),
        },
        # Send daily summary emails
        'send-daily-summary': {
            'task': 'worker.tasks.scheduled_tasks.send_daily_summaries',
            'schedule': crontab(hour=9, minute=0),  # 9 AM
        },
    },
)
```

### worker/tasks/application_task.py

```python
"""Application Processing Tasks"""

from celery import shared_task
from typing import Optional
import asyncio
from app.db.session import get_db
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.models.agent_settings import AgentSettings
from worker.scrapers.linkedin_applicator import LinkedInApplicator
from worker.scrapers.naukri_applicator import NaukriApplicator
from worker.ai.cover_letter_generator import CoverLetterGenerator, EmailGenerator
from worker.ai.company_researcher import CompanyResearcher
from worker.email.email_sender import EmailSender
from worker.utils.email_finder import EmailFinder
from app.services.llm_service import LLMService
from app.services.notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_queues(self):
    """Process application queues for all active users"""
    asyncio.run(_process_queues_async())
    
async def _process_queues_async():
    """Async implementation of queue processing"""
    async with get_db() as db:
        # Get all users with active agents
        users = await db.query(User).join(AgentSettings).filter(
            AgentSettings.is_active == True,
            AgentSettings.is_paused == False
        ).all()
        
        for user in users:
            await process_user_queue.delay(str(user.id))

@shared_task(bind=True, max_retries=3)
def process_user_queue(self, user_id: str):
    """Process application queue for a single user"""
    asyncio.run(_process_user_queue_async(user_id))
    
async def _process_user_queue_async(user_id: str):
    """Async implementation"""
    async with get_db() as db:
        # Get user and settings
        user = await db.get(User, user_id)
        settings = await db.query(AgentSettings).filter(
            AgentSettings.user_id == user_id
        ).first()
        
        if not user or not settings or not settings.is_active:
            return
            
        # Check daily limits
        if settings.applications_today >= settings.daily_application_limit:
            logger.info(f"User {user_id} reached daily limit")
            return
            
        # Get queued jobs
        queued_matches = await db.query(JobMatch).filter(
            JobMatch.user_id == user_id,
            JobMatch.status == 'queued'
        ).order_by(JobMatch.queue_priority.desc()).limit(10).all()
        
        for match in queued_matches:
            # Check limits again
            if settings.applications_today >= settings.daily_application_limit:
                break
                
            # Process this job
            await apply_to_job.delay(user_id, str(match.job_id), str(match.id))
            
            # Add delay between applications
            await asyncio.sleep(settings.min_delay_seconds)

@shared_task(bind=True, max_retries=2)
def apply_to_job(self, user_id: str, job_id: str, match_id: str):
    """Apply to a specific job"""
    asyncio.run(_apply_to_job_async(user_id, job_id, match_id))
    
async def _apply_to_job_async(user_id: str, job_id: str, match_id: str):
    """Async apply implementation"""
    
    async with get_db() as db:
        # Get all required data
        user = await db.get(User, user_id)
        job = await db.get(Job, job_id)
        match = await db.get(JobMatch, match_id)
        settings = await db.query(AgentSettings).filter(AgentSettings.user_id == user_id).first()
        profile = await db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        resume = await db.query(Resume).filter(Resume.user_id == user_id, Resume.is_default == True).first()
        credentials = await db.query(PlatformCredentials).filter(
            PlatformCredentials.user_id == user_id,
            PlatformCredentials.platform == job.source
        ).first()
        
        if not all([user, job, match, settings, profile, resume]):
            logger.error(f"Missing required data for application")
            return
            
        # Create application record
        application = Application(
            user_id=user_id,
            job_id=job_id,
            job_match_id=match_id,
            job_title=job.title,
            company_name=job.company_name,
            job_location=job.location,
            job_url=job.source_url,
            job_source=job.source,
            status='in_progress',
            resume_id=resume.id,
        )
        db.add(application)
        await db.commit()
        
        try:
            # Initialize services
            llm_service = LLMService()
            cover_letter_gen = CoverLetterGenerator(llm_service)
            company_researcher = CompanyResearcher(llm_service)
            
            # Research company
            company_research = await company_researcher.research(
                company_name=job.company_name,
                company_website=job.company_website,
            )
            job.company_research = company_research
            
            # Generate cover letter
            cover_letter = await cover_letter_gen.generate(
                user_profile=profile,
                resume_text=resume.raw_text,
                job=job,
                company_research=company_research,
                tone=settings.cover_letter_tone,
            )
            application.cover_letter_generated = cover_letter
            application.cover_letter_used = cover_letter
            
            # Determine application method
            if job.source == 'linkedin' and job.easy_apply_available and settings.linkedin_easy_apply_enabled:
                # LinkedIn Easy Apply
                success, screenshots, error = await _apply_linkedin(
                    credentials, profile, resume, job, cover_letter, application
                )
                application.application_method = 'linkedin_easy_apply'
                
            elif job.source == 'naukri' and settings.naukri_apply_enabled:
                # Naukri Apply
                success, screenshots, error = await _apply_naukri(
                    credentials, profile, resume, job, application
                )
                application.application_method = 'naukri_apply'
                
            elif settings.cold_email_enabled:
                # Cold email fallback
                success, error = await _send_cold_email(
                    user, profile, resume, job, company_research, cover_letter, application, settings
                )
                screenshots = []
                application.application_method = 'cold_email'
                
            else:
                success = False
                error = "No applicable method available"
                screenshots = []
                
            # Update application status
            if success:
                application.status = 'applied'
                application.applied_at = datetime.utcnow()
                match.status = 'applied'
                settings.applications_today += 1
                user.applications_this_month += 1
                
                # Send notification
                await NotificationService.send(
                    user_id=user_id,
                    type='application_success',
                    title=f"Applied to {job.title}",
                    message=f"Successfully applied to {job.title} at {job.company_name}",
                    application_id=str(application.id)
                )
            else:
                application.status = 'failed'
                application.error_message = error
                match.status = 'failed'
                
            application.screenshots = screenshots
            await db.commit()
            
        except Exception as e:
            logger.error(f"Application error: {e}")
            application.status = 'failed'
            application.error_message = str(e)
            await db.commit()

async def _apply_linkedin(credentials, profile, resume, job, cover_letter, application):
    """Apply via LinkedIn Easy Apply"""
    from worker.scrapers.linkedin_scraper import LinkedInScraper
    
    scraper = LinkedInScraper(str(profile.user_id), credentials.decrypt())
    await scraper.initialize()
    
    try:
        logged_in = await scraper.login()
        if not logged_in:
            return False, [], "LinkedIn login failed"
            
        applicator = LinkedInApplicator(
            page=scraper.page,
            user_profile=profile.to_dict(),
            resume_path=resume.file_url,
            llm_service=LLMService()
        )
        
        success, screenshots, error = await applicator.apply_to_job(
            job_url=job.source_url,
            cover_letter=cover_letter,
        )
        
        return success, screenshots, error
        
    finally:
        await scraper.close()

async def _apply_naukri(credentials, profile, resume, job, application):
    """Apply via Naukri"""
    from worker.scrapers.naukri_scraper import NaukriScraper, NaukriApplicator
    
    scraper = NaukriScraper(str(profile.user_id), credentials.decrypt())
    await scraper.initialize()
    
    try:
        logged_in = await scraper.login()
        if not logged_in:
            return False, [], "Naukri login failed"
            
        applicator = NaukriApplicator(
            page=scraper.page,
            user_profile=profile.to_dict()
        )
        
        success, screenshots, error = await applicator.apply_to_job(job.source_url)
        return success, screenshots, error
        
    finally:
        await scraper.close()

async def _send_cold_email(user, profile, resume, job, company_research, cover_letter, application, settings):
    """Send cold email to hiring manager"""
    
    # Find hiring manager email
    email_finder = EmailFinder()
    
    # First check if we already have it
    if job.hiring_manager_email and job.hiring_manager_email_verified:
        hm_email = job.hiring_manager_email
    else:
        # Try to find it
        if job.hiring_manager_name:
            names = job.hiring_manager_name.split()
            first_name = names[0]
            last_name = names[-1] if len(names) > 1 else ""
            
            domain = job.company_website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
            
            result = await email_finder.find_email(first_name, last_name, domain)
            if result:
                hm_email = result['email']
                job.hiring_manager_email = hm_email
                job.hiring_manager_email_verified = result['verified']
            else:
                return False, "Could not find hiring manager email"
        else:
            return False, "No hiring manager information"
            
    # Generate email
    email_gen = EmailGenerator(LLMService())
    email_content = await email_gen.generate_initial_email(
        user_profile=profile.to_dict(),
        resume_text=resume.raw_text,
        job=job.to_dict(),
        company_research=company_research,
        hiring_manager={'name': job.hiring_manager_name, 'title': job.hiring_manager_title}
    )
    
    # Send email
    email_sender = EmailSender()
    result = await email_sender.send_cold_email(
        to_email=hm_email,
        from_email=user.email_settings.email_address,
        from_name=f"{profile.first_name} {profile.last_name}",
        subject=email_content['subject'],
        body=email_content['body'],
        resume_path=resume.file_url,
        application_id=str(application.id)
    )
    
    if result['success']:
        application.email_sent_to = hm_email
        application.email_subject = email_content['subject']
        application.email_body = email_content['body']
        application.email_sent_at = datetime.utcnow()
        
        # Schedule follow-ups if enabled
        if settings.followup_enabled:
            await _schedule_followups(application, settings, email_content)
            
        return True, None
    else:
        return False, result.get('error', 'Email send failed')

async def _schedule_followups(application, settings, original_email):
    """Schedule follow-up emails"""
    from worker.ai.cover_letter_generator import EmailGenerator
    
    email_gen = EmailGenerator(LLMService())
    
    # Schedule first follow-up
    followup1 = await email_gen.generate_followup_email(
        original_email=original_email,
        followup_number=1,
        user_profile=application.user.profile.to_dict(),
        job=application.job.to_dict()
    )
    
    scheduled1 = ScheduledFollowup(
        application_id=application.id,
        followup_number=1,
        scheduled_for=datetime.utcnow() + timedelta(days=settings.followup_delay_days_1),
        subject=followup1['subject'],
        body=followup1['body']
    )
    
    # Schedule second follow-up
    followup2 = await email_gen.generate_followup_email(
        original_email=original_email,
        followup_number=2,
        user_profile=application.user.profile.to_dict(),
        job=application.job.to_dict()
    )
    
    scheduled2 = ScheduledFollowup(
        application_id=application.id,
        followup_number=2,
        scheduled_for=datetime.utcnow() + timedelta(days=settings.followup_delay_days_2),
        subject=followup2['subject'],
        body=followup2['body']
    )
    
    async with get_db() as db:
        db.add(scheduled1)
        db.add(scheduled2)
        await db.commit()
```

---

## FRONTEND KEY COMPONENTS

### Dashboard Page (src/app/(dashboard)/dashboard/page.tsx)

```tsx
'use client';

import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Briefcase, 
  Send, 
  MessageSquare, 
  Calendar,
  TrendingUp,
  Play,
  Pause,
  Settings
} from 'lucide-react';
import { StatsCards } from '@/components/dashboard/stats-cards';
import { RecentApplications } from '@/components/dashboard/recent-applications';
import { AgentStatus } from '@/components/dashboard/agent-status';
import { ActivityFeed } from '@/components/dashboard/activity-feed';
import { useAgent } from '@/hooks/use-agent';
import { api } from '@/lib/api';

export default function DashboardPage() {
  const { agentStatus, startAgent, stopAgent, isLoading: agentLoading } = useAgent();
  
  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.get('/analytics/overview').then(r => r.data),
  });
  
  const { data: recentApps } = useQuery({
    queryKey: ['recent-applications'],
    queryFn: () => api.get('/applications', { params: { limit: 5 } }).then(r => r.data),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back! Here's your job search overview.
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <AgentStatus status={agentStatus} />
          
          {agentStatus === 'active' ? (
            <Button 
              variant="outline" 
              onClick={stopAgent}
              disabled={agentLoading}
            >
              <Pause className="mr-2 h-4 w-4" />
              Pause Agent
            </Button>
          ) : (
            <Button 
              onClick={startAgent}
              disabled={agentLoading}
            >
              <Play className="mr-2 h-4 w-4" />
              Start Agent
            </Button>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <StatsCards stats={stats} />

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Applications - 2 cols */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Recent Applications</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <a href="/applications">View all</a>
              </Button>
            </CardHeader>
            <CardContent>
              <RecentApplications applications={recentApps?.items || []} />
            </CardContent>
          </Card>
        </div>

        {/* Activity Feed - 1 col */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <ActivityFeed />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button variant="outline" className="h-24 flex-col" asChild>
              <a href="/jobs">
                <Briefcase className="h-6 w-6 mb-2" />
                Browse Jobs
              </a>
            </Button>
            <Button variant="outline" className="h-24 flex-col" asChild>
              <a href="/settings/preferences">
                <Settings className="h-6 w-6 mb-2" />
                Update Preferences
              </a>
            </Button>
            <Button variant="outline" className="h-24 flex-col" asChild>
              <a href="/analytics">
                <TrendingUp className="h-6 w-6 mb-2" />
                View Analytics
              </a>
            </Button>
            <Button variant="outline" className="h-24 flex-col" asChild>
              <a href="/export">
                <Send className="h-6 w-6 mb-2" />
                Export Data
              </a>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

### Agent Control Panel (src/components/agent/agent-control-panel.tsx)

```tsx
'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import {
  Play,
  Pause,
  Square,
  Settings,
  Zap,
  Clock,
  Mail,
  Linkedin,
  FileText,
} from 'lucide-react';
import { api } from '@/lib/api';
import { useSocket } from '@/hooks/use-socket';
import { LiveBrowserView } from './live-browser-view';
import { ApplicationQueue } from './application-queue';
import { AgentLogs } from './agent-logs';

export function AgentControlPanel() {
  const queryClient = useQueryClient();
  const [showLiveView, setShowLiveView] = useState(false);
  
  // Get agent status
  const { data: agentStatus } = useQuery({
    queryKey: ['agent-status'],
    queryFn: () => api.get('/agent/status').then(r => r.data),
    refetchInterval: 5000,
  });
  
  // Get agent settings
  const { data: settings } = useQuery({
    queryKey: ['agent-settings'],
    queryFn: () => api.get('/agent/settings').then(r => r.data),
  });
  
  // Mutations
  const startAgent = useMutation({
    mutationFn: () => api.post('/agent/start'),
    onSuccess: () => queryClient.invalidateQueries(['agent-status']),
  });
  
  const stopAgent = useMutation({
    mutationFn: () => api.post('/agent/stop'),
    onSuccess: () => queryClient.invalidateQueries(['agent-status']),
  });
  
  const pauseAgent = useMutation({
    mutationFn: () => api.post('/agent/pause'),
    onSuccess: () => queryClient.invalidateQueries(['agent-status']),
  });
  
  const updateSettings = useMutation({
    mutationFn: (data: any) => api.put('/agent/settings', data),
    onSuccess: () => queryClient.invalidateQueries(['agent-settings']),
  });
  
  // Socket for real-time updates
  const { lastMessage } = useSocket('agent');

  const isActive = agentStatus?.is_active && !agentStatus?.is_paused;
  const isPaused = agentStatus?.is_active && agentStatus?.is_paused;

  return (
    <div className="space-y-6">
      {/* Status & Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Agent Control</CardTitle>
            <Badge variant={isActive ? 'default' : isPaused ? 'secondary' : 'outline'}>
              {isActive ? '🟢 Active' : isPaused ? '🟡 Paused' : '⚪ Stopped'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Control Buttons */}
          <div className="flex items-center gap-3">
            {!agentStatus?.is_active ? (
              <Button onClick={() => startAgent.mutate()} disabled={startAgent.isLoading}>
                <Play className="mr-2 h-4 w-4" />
                Start Agent
              </Button>
            ) : (
              <>
                {isPaused ? (
                  <Button onClick={() => startAgent.mutate()} disabled={startAgent.isLoading}>
                    <Play className="mr-2 h-4 w-4" />
                    Resume
                  </Button>
                ) : (
                  <Button variant="outline" onClick={() => pauseAgent.mutate()}>
                    <Pause className="mr-2 h-4 w-4" />
                    Pause
                  </Button>
                )}
                <Button variant="destructive" onClick={() => stopAgent.mutate()}>
                  <Square className="mr-2 h-4 w-4" />
                  Stop
                </Button>
              </>
            )}
            
            <Button 
              variant="outline" 
              onClick={() => setShowLiveView(!showLiveView)}
            >
              {showLiveView ? 'Hide' : 'Show'} Live View
            </Button>
          </div>

          {/* Progress */}
          {isActive && agentStatus?.current_task && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Currently: {agentStatus.current_task}</span>
                <span>{agentStatus.queue_size} jobs in queue</span>
              </div>
              <Progress value={agentStatus.progress || 0} />
            </div>
          )}

          {/* Today's Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-muted rounded-lg">
              <div className="text-2xl font-bold">{agentStatus?.applications_today || 0}</div>
              <div className="text-xs text-muted-foreground">Applications Today</div>
              <div className="text-xs text-muted-foreground">
                Limit: {settings?.daily_application_limit || 25}
              </div>
            </div>
            <div className="text-center p-3 bg-muted rounded-lg">
              <div className="text-2xl font-bold">{agentStatus?.emails_today || 0}</div>
              <div className="text-xs text-muted-foreground">Emails Sent</div>
              <div className="text-xs text-muted-foreground">
                Limit: {settings?.daily_email_limit || 20}
              </div>
            </div>
            <div className="text-center p-3 bg-muted rounded-lg">
              <div className="text-2xl font-bold">{agentStatus?.jobs_discovered_today || 0}</div>
              <div className="text-xs text-muted-foreground">Jobs Found Today</div>
            </div>
            <div className="text-center p-3 bg-muted rounded-lg">
              <div className="text-2xl font-bold">{agentStatus?.responses_today || 0}</div>
              <div className="text-xs text-muted-foreground">Responses</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Live Browser View */}
      {showLiveView && (
        <Card>
          <CardHeader>
            <CardTitle>Live Browser View</CardTitle>
          </CardHeader>
          <CardContent>
            <LiveBrowserView />
          </CardContent>
        </Card>
      )}

      {/* Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Agent Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Application Methods */}
          <div className="space-y-4">
            <Label>Application Methods</Label>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Linkedin className="h-4 w-4" />
                  <span>LinkedIn Easy Apply</span>
                </div>
                <Switch
                  checked={settings?.linkedin_easy_apply_enabled}
                  onCheckedChange={(checked) => 
                    updateSettings.mutate({ linkedin_easy_apply_enabled: checked })
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  <span>Naukri.com Apply</span>
                </div>
                <Switch
                  checked={settings?.naukri_apply_enabled}
                  onCheckedChange={(checked) => 
                    updateSettings.mutate({ naukri_apply_enabled: checked })
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  <span>Cold Email Outreach</span>
                </div>
                <Switch
                  checked={settings?.cold_email_enabled}
                  onCheckedChange={(checked) => 
                    updateSettings.mutate({ cold_email_enabled: checked })
                  }
                />
              </div>
            </div>
          </div>

          {/* Speed Control */}
          <div className="space-y-4">
            <Label>Application Speed</Label>
            <div className="flex items-center gap-4">
              <Slider
                value={[
                  settings?.application_speed === 'slow' ? 0 :
                  settings?.application_speed === 'medium' ? 50 : 100
                ]}
                onValueChange={([value]) => {
                  const speed = value < 33 ? 'slow' : value < 66 ? 'medium' : 'fast';
                  updateSettings.mutate({ application_speed: speed });
                }}
                max={100}
                step={50}
                className="flex-1"
              />
              <Badge variant="outline">
                {settings?.application_speed || 'medium'}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              Slow: 3-5 min between apps | Medium: 1-3 min | Fast: 30s-1min
            </p>
          </div>

          {/* Daily Limits */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Daily Application Limit</Label>
              <div className="flex items-center gap-2">
                <Slider
                  value={[settings?.daily_application_limit || 25]}
                  onValueChange={([value]) => 
                    updateSettings.mutate({ daily_application_limit: value })
                  }
                  max={100}
                  step={5}
                />
                <span className="w-12 text-center">{settings?.daily_application_limit || 25}</span>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Daily Email Limit</Label>
              <div className="flex items-center gap-2">
                <Slider
                  value={[settings?.daily_email_limit || 20]}
                  onValueChange={([value]) => 
                    updateSettings.mutate({ daily_email_limit: value })
                  }
                  max={50}
                  step={5}
                />
                <span className="w-12 text-center">{settings?.daily_email_limit || 20}</span>
              </div>
            </div>
          </div>

          {/* Follow-up Settings */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label>Enable Follow-up Emails</Label>
              <Switch
                checked={settings?.followup_enabled}
                onCheckedChange={(checked) => 
                  updateSettings.mutate({ followup_enabled: checked })
                }
              />
            </div>
            {settings?.followup_enabled && (
              <div className="grid grid-cols-2 gap-4 pl-4">
                <div>
                  <Label className="text-sm">First Follow-up (days)</Label>
                  <Slider
                    value={[settings?.followup_delay_days_1 || 3]}
                    onValueChange={([value]) => 
                      updateSettings.mutate({ followup_delay_days_1: value })
                    }
                    min={1}
                    max={7}
                  />
                </div>
                <div>
                  <Label className="text-sm">Second Follow-up (days)</Label>
                  <Slider
                    value={[settings?.followup_delay_days_2 || 7]}
                    onValueChange={([value]) => 
                      updateSettings.mutate({ followup_delay_days_2: value })
                    }
                    min={3}
                    max={14}
                  />
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Application Queue */}
      <Card>
        <CardHeader>
          <CardTitle>Application Queue</CardTitle>
        </CardHeader>
        <CardContent>
          <ApplicationQueue />
        </CardContent>
      </Card>

      {/* Agent Logs */}
      <Card>
        <CardHeader>
          <CardTitle>Activity Logs</CardTitle>
        </CardHeader>
        <CardContent>
          <AgentLogs />
        </CardContent>
      </Card>
    </div>
  );
}
```

### Live Browser View Component (src/components/agent/live-browser-view.tsx)

```tsx
'use client';

import { useEffect, useState, useRef } from 'react';
import { useSocket } from '@/hooks/use-socket';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';

export function LiveBrowserView() {
  const [screenshot, setScreenshot] = useState<string | null>(null);
  const [currentAction, setCurrentAction] = useState<string>('');
  const [isConnected, setIsConnected] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  
  const { socket, isConnected: socketConnected } = useSocket('agent');
  
  useEffect(() => {
    if (!socket) return;
    
    socket.on('connect', () => setIsConnected(true));
    socket.on('disconnect', () => setIsConnected(false));
    
    socket.on('screenshot', (data: { image: string; action: string }) => {
      setScreenshot(data.image);
      setCurrentAction(data.action);
    });
    
    socket.on('agent_status', (data: { status: string; message: string }) => {
      setCurrentAction(data.message);
    });
    
    return () => {
      socket.off('screenshot');
      socket.off('agent_status');
    };
  }, [socket]);

  return (
    <div className="space-y-3">
      {/* Status Bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm">{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
        {currentAction && (
          <Badge variant="outline">{currentAction}</Badge>
        )}
      </div>
      
      {/* Browser Frame */}
      <div className="relative aspect-video bg-muted rounded-lg overflow-hidden border">
        {screenshot ? (
          <img
            ref={imgRef}
            src={screenshot}
            alt="Live browser view"
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-2">
              <Skeleton className="h-4 w-48 mx-auto" />
              <p className="text-sm text-muted-foreground">
                Waiting for agent to start...
              </p>
            </div>
          </div>
        )}
        
        {/* Loading overlay */}
        {isConnected && !screenshot && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/50">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        )}
      </div>
      
      {/* Current Action Display */}
      {currentAction && (
        <div className="p-3 bg-muted rounded-lg">
          <p className="text-sm font-medium">Currently: {currentAction}</p>
        </div>
      )}
    </div>
  );
}
```

---

## SUBSCRIPTION TIERS

```typescript
// Subscription plan configuration
export const SUBSCRIPTION_PLANS = {
  free: {
    name: 'Free',
    price_monthly: 0,
    price_yearly: 0,
    limits: {
      applications_per_month: 25,
      emails_per_month: 10,
      resumes: 1,
      job_sources: ['linkedin'],
      features: [
        'LinkedIn Easy Apply',
        'Basic job matching',
        'Application tracking',
        'CSV export',
      ],
    },
  },
  basic: {
    name: 'Basic',
    price_monthly: 1900, // $19.00
    price_yearly: 15900, // $159.00 (2 months free)
    limits: {
      applications_per_month: 100,
      emails_per_month: 50,
      resumes: 3,
      job_sources: ['linkedin', 'naukri'],
      features: [
        'Everything in Free',
        'Naukri.com integration',
        'AI cover letters',
        'Basic analytics',
        'Email support',
      ],
    },
  },
  pro: {
    name: 'Pro',
    price_monthly: 4900, // $49.00
    price_yearly: 39900, // $399.00 (2 months free)
    limits: {
      applications_per_month: 500,
      emails_per_month: 200,
      resumes: 10,
      job_sources: ['linkedin', 'naukri', 'email'],
      features: [
        'Everything in Basic',
        'Cold email outreach',
        'Auto follow-ups',
        'Advanced analytics',
        'Priority queue',
        'API access',
        'Priority support',
      ],
    },
  },
  enterprise: {
    name: 'Enterprise',
    price_monthly: 9900, // $99.00
    price_yearly: 79900, // $799.00
    limits: {
      applications_per_month: -1, // Unlimited
      emails_per_month: -1,
      resumes: -1,
      job_sources: ['linkedin', 'naukri', 'email', 'custom'],
      features: [
        'Everything in Pro',
        'Unlimited applications',
        'Custom integrations',
        'Dedicated support',
        'SLA guarantee',
        'Custom AI training',
      ],
    },
  },
};
```

---

## DEPLOYMENT CHECKLIST

### Pre-Deployment
- [ ] Set all environment variables in `.env`
- [ ] Configure domain DNS (A record pointing to server)
- [ ] Set up Stripe products and prices
- [ ] Configure SendGrid/SES for email
- [ ] Set up S3 bucket for file storage
- [ ] Get API keys (Anthropic, Hunter.io, ZeroBounce)

### Deployment Steps
```bash
# 1. Clone repository
git clone https://github.com/your-repo/jobpilot.git
cd jobpilot

# 2. Copy and configure environment
cp .env.example .env
nano .env  # Edit all values

# 3. Build and start services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 4. Run database migrations
docker-compose exec backend alembic upgrade head

# 5. Create admin user (optional)
docker-compose exec backend python scripts/create_admin.py

# 6. Check logs
docker-compose logs -f

# 7. Set up SSL (automatic with Traefik)
# Certificates will be obtained automatically
```

### Post-Deployment
- [ ] Verify SSL certificates are working
- [ ] Test user registration and login
- [ ] Test LinkedIn connection
- [ ] Test job scraping
- [ ] Test application flow
- [ ] Test email sending
- [ ] Set up monitoring (optional: Prometheus/Grafana)
- [ ] Set up log aggregation (optional: ELK stack)
- [ ] Configure backup scripts

---

## SECURITY CONSIDERATIONS

1. **Credential Encryption**: All platform credentials (LinkedIn, Naukri passwords) are encrypted at rest using AES-256
2. **Rate Limiting**: Implemented on all API endpoints to prevent abuse
3. **CORS**: Properly configured to only allow frontend domain
4. **JWT Security**: Short-lived access tokens (30 min) with refresh token rotation
5. **Input Validation**: All inputs validated with Pydantic
6. **SQL Injection**: Prevented via SQLAlchemy ORM
7. **XSS Prevention**: React escapes by default, CSP headers set
8. **HTTPS Only**: Traefik handles SSL termination
9. **Secrets Management**: All secrets in environment variables, never in code

---

## MONITORING & ANALYTICS

### Key Metrics to Track
- User signups and activation rate
- Daily/weekly active users
- Applications per user
- Success rate (applications that get responses)
- Conversion rate (free to paid)
- Churn rate
- Revenue (MRR, ARR)

### Logging
- All API requests logged with user ID, endpoint, response time
- All agent actions logged with screenshots
- All errors logged with full stack trace
- Email events logged (sent, opened, clicked)

---

This completes the full prompt. Generate all files with production-ready code!