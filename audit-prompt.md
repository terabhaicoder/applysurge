# MASTER AUDIT & POLISH PROMPT
## Paste this into Claude Code in the jobpilot root directory

---

```
You are auditing and fixing a full-stack application called JobPilot to make it production-ready and top-notch quality. The project already exists with backend (FastAPI/Python), frontend (Next.js/React), and Docker infrastructure.

YOUR MISSION: Systematically audit every part of this application, fix all issues, and ensure everything works end-to-end with production-grade quality.

WORK IN THIS EXACT ORDER:

═══════════════════════════════════════════
PHASE 1: GET EVERYTHING RUNNING
═══════════════════════════════════════════

Step 1.1: Check .env file exists and has real values (not placeholder "change-me" values for local dev). For local development, generate actual random SECRET_KEY and ENCRYPTION_KEY values. Ensure DATABASE_URL, REDIS_URL, RABBITMQ_URL point to correct Docker service names.

Step 1.2: Check all Dockerfiles (backend/Dockerfile, backend/Dockerfile.prod, backend/Dockerfile.worker, frontend/Dockerfile, frontend/Dockerfile.prod):
- Ensure they build without errors
- Ensure backend Dockerfile.worker installs Playwright and its browser dependencies
- Ensure frontend Dockerfile installs all npm dependencies

Step 1.3: Check docker-compose.yml:
- All services have correct health checks
- Correct dependency ordering (postgres must be healthy before backend starts)
- Volumes are properly defined
- Network configuration is correct
- Environment variables are properly passed

Step 1.4: Try to build and start everything:
- Run: docker-compose build
- Fix ANY build errors (missing dependencies, syntax errors, wrong paths)
- Run: docker-compose up -d
- Check logs for each service: docker-compose logs backend, docker-compose logs frontend, docker-compose logs worker, etc.
- Fix ALL startup errors

Step 1.5: Database initialization:
- Ensure alembic is configured correctly (alembic.ini points to correct DB URL)
- Ensure migrations exist and are valid
- Run: docker-compose exec backend alembic upgrade head
- If migrations fail, fix them. If they don't exist, generate them from models.
- Verify all tables from the schema are created

═══════════════════════════════════════════
PHASE 2: BACKEND AUDIT
═══════════════════════════════════════════

For EVERY file in backend/app/ and backend/worker/, do the following:

Step 2.1: Check app/main.py
- FastAPI app is created with proper title, version, description
- CORS middleware is configured (allow frontend URL + localhost:3000)
- All API routers from api/v1/ are included with correct prefixes
- Startup/shutdown events exist for DB connections
- Socket.IO is mounted if websocket is used
- Health check endpoint exists at GET /health that returns {"status": "ok"}

Step 2.2: Check app/core/config.py
- Pydantic BaseSettings class loads ALL env variables from the spec
- Has sensible defaults for development
- Properly typed (str, int, bool, Optional)
- model_config has env_file=".env"

Step 2.3: Check app/core/security.py
- create_access_token(data, expires_delta) → JWT string
- create_refresh_token(data) → JWT string
- verify_token(token) → payload dict or raise
- hash_password(password) → hashed string (bcrypt)
- verify_password(plain, hashed) → bool
- All use proper algorithms and libraries (python-jose or PyJWT, passlib)

Step 2.4: Check app/core/encryption.py
- encrypt(plaintext) → encrypted bytes
- decrypt(encrypted_bytes) → plaintext string
- Uses Fernet symmetric encryption
- Key derived from ENCRYPTION_KEY env var

Step 2.5: Check app/db/session.py
- async engine created with create_async_engine
- async_sessionmaker configured
- get_db async generator dependency that yields session and closes properly

Step 2.6: Check ALL models in app/models/
For each model file, verify:
- Inherits from Base (declarative_base)
- Table name matches the SQL schema
- ALL columns from the SQL schema exist with correct types
- Relationships are defined (e.g., User has relationship to UserProfile)
- Column types use SQLAlchemy types (UUID, String, Integer, Boolean, JSONB, DateTime with timezone, etc.)
- Default values match the schema
- Unique constraints and indexes are defined

CHECK THESE SPECIFIC MODELS EXIST AND ARE COMPLETE:
- User, VerificationToken, RefreshToken, Session
- UserProfile, UserEducation, UserExperience, UserSkill, UserCertification
- Resume
- JobPreferences
- PlatformCredentials
- Job
- JobMatch
- Application, ApplicationLog
- EmailSettings, EmailTemplate, EmailEvent, ScheduledFollowup
- AgentSettings
- Notification
- DailyStats
- SubscriptionPlan, PaymentHistory, Export

Step 2.7: Check ALL schemas in app/schemas/
- Every API endpoint has proper request and response schemas
- Pydantic v2 syntax (model_config = ConfigDict(...))
- Proper validation (email validation, min/max lengths, enums for status fields)
- Separate Create, Update, and Response schemas where needed

Step 2.8: Check ALL API routes in app/api/v1/
For EVERY route file, verify:
- All endpoints from the API spec exist
- Proper HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Authentication dependency (get_current_user) on protected routes
- Proper request body types (Pydantic schemas)
- Proper response models defined
- Error handling (try/except, proper HTTP status codes)
- Pagination on list endpoints (skip, limit parameters)
- No placeholder/stub implementations — every endpoint must have real logic

SPECIFICALLY CHECK:
- auth.py: register, login, logout, refresh, forgot-password, reset-password, verify-email, google oauth, /me
- users.py: get/update/delete current user, change password, usage stats
- profile.py: full CRUD for profile, education, experience, skills, certifications
- resumes.py: upload (multipart), list, get, delete, parse, download
- preferences.py: get/update preferences
- credentials.py: connect/disconnect/validate LinkedIn & Naukri
- jobs.py: list matched jobs with filters & pagination, save, hide, queue management
- applications.py: list with filters & pagination, get details, logs, screenshots, status update, withdraw, notes, stats
- agent.py: start, stop, pause, resume, settings CRUD, queue, logs
- analytics.py: overview, applications over time, response rates, source breakdown, daily/weekly/monthly
- email_settings.py: CRUD, connect Gmail/Outlook/SMTP, verify, test send
- email_templates.py: CRUD, preview with sample data, AI generate
- notifications.py: list, unread count, mark read, mark all read, delete
- exports.py: create, list, download, delete
- billing.py: plans, current subscription, Stripe checkout, portal, invoices, webhook

Step 2.9: Check ALL services in app/services/
- Each service has proper async methods
- Database operations use async session correctly
- Error handling is comprehensive
- No raw SQL — use SQLAlchemy ORM
- Services are stateless (take db session as parameter)

Step 2.10: Check worker/celery_app.py
- Celery app configured with RabbitMQ broker and Redis backend
- Beat schedule includes: hourly job discovery, 5-min queue processing, hourly followups, midnight stats reset, daily summary at 9am
- Task routing: browser tasks → browser queue, scraping → scraping queue, emails → emails queue
- Proper serialization settings

Step 2.11: Check ALL worker tasks
- Each task is a proper Celery @shared_task
- Tasks handle their own DB sessions (not relying on request context)
- Proper error handling with retries
- Logging on all important actions

Step 2.12: Check ALL scrapers
- linkedin_scraper.py: Login, search with all filters, extract all job fields, pagination, anti-detection
- linkedin_applicator.py: Full Easy Apply flow with multi-step forms, resume upload, screening Q&A, screenshots
- naukri_scraper.py: Login, search, extract jobs
- naukri_applicator.py: Apply flow
- All use Playwright with stealth settings
- Random delays between actions
- Error handling and screenshot on failure

Step 2.13: Check AI services
- cover_letter_generator.py: Takes all context, generates personalized letter
- job_matcher.py: Scores 0-100 with weighted criteria
- question_answerer.py: Handles all question types
- email_generator.py: Initial + follow-up emails
- company_researcher.py: Web scraping + AI summary
- response_classifier.py: Email response classification

Step 2.14: Check email system
- email_sender.py: SendGrid integration, tracking, attachments
- email_finder.py: Hunter.io + pattern guessing + verification
- email_tracker.py: Open/click tracking endpoints

Step 2.15: Check requirements.txt has ALL needed packages:
fastapi, uvicorn[standard], sqlalchemy[asyncio], asyncpg, alembic, pydantic[email], pydantic-settings, python-jose[cryptography], passlib[bcrypt], python-multipart, httpx, celery[rabbitmq], redis, python-socketio, anthropic, sendgrid, boto3, aioboto3, stripe, playwright, Pillow, python-docx, PyMuPDF, openpyxl, reportlab, cryptography, slowapi, gunicorn, pytest, pytest-asyncio, httpx (for tests)

Fix ANY missing packages.

═══════════════════════════════════════════
PHASE 3: FRONTEND AUDIT
═══════════════════════════════════════════

Step 3.1: Check package.json has ALL required dependencies:
next (14.x), react, react-dom, typescript, tailwindcss, postcss, autoprefixer, @tanstack/react-query, zustand, socket.io-client, react-hook-form, @hookform/resolvers, zod, recharts, lucide-react, axios, clsx, tailwind-merge, class-variance-authority, date-fns
PLUS all shadcn/ui dependencies (radix-ui packages)

Step 3.2: Check next.config.js
- Proper configuration for API proxying or external image domains
- No errors

Step 3.3: Check tailwind.config.js
- Includes shadcn/ui theme configuration
- Content paths cover all component directories
- Dark mode support (class-based)

Step 3.4: Check src/app/globals.css
- Tailwind directives (@tailwind base, components, utilities)
- CSS variables for shadcn theme (--background, --foreground, --primary, etc.)
- Both light and dark theme variables

Step 3.5: Check src/lib/api.ts
- Axios instance configured with base URL from env
- Request interceptor that adds JWT token from auth store
- Response interceptor that handles 401 (auto refresh token)
- Proper error handling

Step 3.6: Check src/lib/utils.ts
- cn() function for tailwind class merging (clsx + tailwind-merge)

Step 3.7: Check src/stores/
- auth-store.ts: user, token, isAuthenticated, login(), logout(), setToken()
- agent-store.ts: agentStatus, isActive, queue, logs
- notification-store.ts: notifications, unreadCount
- ui-store.ts: sidebarOpen, theme

Step 3.8: Check src/hooks/
- use-auth.ts: wraps auth store + TanStack Query for user data
- use-socket.ts: Socket.IO connection management
- use-agent.ts: agent status + controls
- use-applications.ts: TanStack Query hooks for applications
- use-jobs.ts: TanStack Query hooks for jobs

Step 3.9: Check src/providers/
- auth-provider.tsx: wraps auth context, handles token refresh on mount
- query-provider.tsx: TanStack QueryClientProvider setup
- socket-provider.tsx: Socket.IO connection provider
- theme-provider.tsx: next-themes provider
- toast-provider.tsx: toast/sonner provider

Step 3.10: Check ALL shadcn/ui components exist in src/components/ui/
Every component listed in the spec must exist. If any are missing, create them using proper shadcn/ui patterns.

Step 3.11: Check src/app/layout.tsx (root)
- Wraps children with ALL providers (query, auth, socket, theme, toast)
- Proper metadata (title, description)
- Font setup (Inter or similar)

Step 3.12: Check Landing Page (src/app/page.tsx)
THIS MUST BE VISUALLY IMPRESSIVE. Check:
- Hero section with compelling headline, subheadline, CTA button
- Feature highlights (at least 6 features with icons)
- How it works section (3-4 steps)
- Pricing section (showing all 4 tiers)
- Social proof / testimonials section
- Footer with links
- Responsive design (mobile, tablet, desktop)
- Smooth animations (framer-motion or CSS transitions)
- Modern design (gradients, glassmorphism, or clean minimal)
- Dark mode support

Step 3.13: Check Auth Pages
- login/page.tsx: Clean form with email, password, Google OAuth button, "forgot password" link, "register" link
- register/page.tsx: Name, email, password, confirm password, Google OAuth, "already have account" link
- verify-email/page.tsx: Takes token from URL, calls API, shows success/error
- forgot-password/page.tsx: Email input, sends reset link
- reset-password/page.tsx: New password + confirm, takes token from URL

ALL auth forms must use react-hook-form + zod validation with proper error messages.

Step 3.14: Check Dashboard (src/app/(dashboard)/dashboard/page.tsx)
- Stats cards: Total applications, responses, interviews, active jobs (with trend indicators)
- Recent applications list (last 5-10)
- Agent status indicator with start/stop controls
- Activity feed / timeline
- Quick action buttons
- Responsive grid layout

Step 3.15: Check Dashboard Layout (src/app/(dashboard)/layout.tsx)
- Left sidebar with navigation links to ALL dashboard pages
- Top navbar with: search, notifications dropdown, user avatar/menu
- Sidebar should be collapsible
- Mobile: sidebar becomes sheet/drawer
- Sidebar nav items:
  * Dashboard
  * Jobs (with count badge)
  * Applications (with count badge)
  * Agent Control
  * Analytics
  * Email Outreach
  * Settings (with sub-items)
  * Export

Step 3.16: Check ALL dashboard pages exist and are functional (not just empty shells):

src/app/(dashboard)/jobs/page.tsx
- Job list with cards showing: title, company, location, match score, salary, posted date, source badge
- Filters: source, location, remote, salary range, match score, date posted
- Search input
- Pagination
- Actions per job: save, hide, add to queue, view details

src/app/(dashboard)/jobs/[id]/page.tsx
- Full job details: description, requirements, benefits, salary, company info
- Match analysis (score breakdown, matching skills, missing skills)
- Company research summary
- Apply button / add to queue
- Similar jobs suggestions

src/app/(dashboard)/applications/page.tsx
- Application list with: job title, company, status badge, method, date applied, response status
- Filters: status, method, source, date range
- Search
- Pagination
- Bulk actions

src/app/(dashboard)/applications/[id]/page.tsx
- Full application details
- Status timeline (visual timeline showing each status change)
- Cover letter used
- Screening Q&A
- Screenshots gallery (clickable thumbnails that open full view)
- Email thread (if cold email)
- Notes section
- Manual status update dropdown

src/app/(dashboard)/agent/page.tsx
- Agent control panel (start/stop/pause buttons)
- Current status with live indicator
- Today's stats (applications, emails, jobs found)
- Application speed slider
- Method toggles (LinkedIn, Naukri, Email)
- Daily limits configuration
- Application queue (draggable/sortable list)
- Activity logs (scrolling feed)

src/app/(dashboard)/agent/live/page.tsx
- Live browser view (shows screenshot stream via WebSocket)
- Current action indicator
- Connection status

src/app/(dashboard)/analytics/page.tsx
- Applications over time chart (line/area chart, last 30 days)
- Response rate pie chart
- Applications by source (bar chart)
- Applications by status (donut chart)
- Weekly/monthly comparison
- Key metrics: avg response time, best performing job titles, top companies
- Date range selector

src/app/(dashboard)/emails/page.tsx
- Email outreach dashboard
- Stats: sent, opened, clicked, replied (with rates)
- Email list with status indicators
- Follow-up schedule view

src/app/(dashboard)/emails/templates/page.tsx
- Template list with performance metrics
- Create/edit template with rich text
- Template preview with sample data
- Placeholder helper

src/app/(dashboard)/settings/page.tsx - Settings overview with links to sub-pages

src/app/(dashboard)/settings/profile/page.tsx
- Full profile form: personal info, location, links, work authorization
- Education CRUD (add/edit/delete cards)
- Experience CRUD (add/edit/delete cards)
- Skills CRUD (add/edit/delete tags)
- Certifications CRUD
- Profile completeness indicator

src/app/(dashboard)/settings/resume/page.tsx
- Resume upload (drag & drop zone)
- Resume list with: name, file type, size, upload date, default indicator
- Set default resume
- Delete resume
- View parsed content

src/app/(dashboard)/settings/preferences/page.tsx
- Target job titles (multi-select/tags input)
- Preferred locations (multi-select)
- Remote preference (radio: remote only, hybrid, onsite, any)
- Salary range (min/max inputs)
- Company preferences (size, industry)
- Blacklist/whitelist companies
- Experience level (multi-select)
- Job type (multi-select)
- Min match score (slider)
- Keywords (required, excluded)

src/app/(dashboard)/settings/connections/page.tsx
- LinkedIn connection card: status, connect/disconnect button, last validated
- Naukri connection card: same
- Connection form: email + password inputs
- Validation status indicator

src/app/(dashboard)/settings/email/page.tsx
- Email provider selection (Gmail OAuth, Outlook OAuth, Custom SMTP)
- SMTP configuration form
- Email signature editor
- Send test email button
- Daily limit setting

src/app/(dashboard)/settings/agent/page.tsx
- All agent settings from the agent_settings schema
- Schedule configuration (start/end time, days of week)
- Speed settings
- Method enables
- Review mode toggle
- Cover letter settings
- Follow-up settings
- Notification settings

src/app/(dashboard)/settings/billing/page.tsx
- Current plan display with usage
- Plan comparison cards (Free, Basic, Pro, Enterprise)
- Upgrade/downgrade buttons
- Payment history table
- Manage subscription button (opens Stripe portal)

src/app/(dashboard)/export/page.tsx
- Export type selection (CSV, XLSX, PDF)
- Scope selection (all data, applications only, jobs only, analytics)
- Date range filter
- Export button
- Export history with download links

Step 3.17: Check ALL component files in src/components/ exist and are properly implemented:
- Every component listed in the project structure spec must exist
- No empty components — each must render meaningful UI
- All components must be properly typed with TypeScript
- Use shadcn/ui primitives consistently
- Responsive design on all components

Step 3.18: Check marketing pages
- pricing/page.tsx: 4 tier pricing cards with feature comparison
- features/page.tsx: Detailed feature showcase
- about/page.tsx: Company/product info

═══════════════════════════════════════════
PHASE 4: VISUAL QUALITY CHECK
═══════════════════════════════════════════

Step 4.1: Ensure consistent design system:
- Consistent spacing (use Tailwind spacing scale)
- Consistent typography (headings, body, captions)
- Consistent color usage (primary for CTAs, muted for backgrounds, destructive for errors)
- Consistent border radius
- Consistent shadow usage
- Loading states on ALL data-fetching components (skeletons, not spinners)
- Empty states on ALL list components (illustration + message + action button)
- Error states with retry buttons
- Proper transitions/animations on interactive elements

Step 4.2: Ensure responsive design:
- Landing page: perfect on mobile, tablet, desktop
- Dashboard: sidebar collapses on mobile, grid adjusts
- All forms: full width on mobile, constrained on desktop
- Tables: horizontal scroll on mobile or card view
- Charts: responsive sizing

Step 4.3: Ensure dark mode works:
- All pages must look good in both light and dark mode
- No hardcoded colors — use CSS variables / Tailwind theme colors
- Charts should adapt colors for dark mode

═══════════════════════════════════════════
PHASE 5: END-TO-END VERIFICATION
═══════════════════════════════════════════

Step 5.1: Build and run everything:
docker-compose down -v
docker-compose build
docker-compose up -d
docker-compose exec backend alembic upgrade head

Step 5.2: Verify all services are healthy:
- GET http://localhost:8000/health returns 200
- GET http://localhost:3000 loads the landing page
- postgres is accepting connections
- redis is responding to PING
- rabbitmq management UI is accessible at :15672

Step 5.3: Test the core user flow:
1. POST /api/v1/auth/register — creates user
2. POST /api/v1/auth/login — returns tokens
3. GET /api/v1/auth/me — returns user with token
4. PUT /api/v1/profile — update profile
5. POST /api/v1/resumes — upload resume
6. PUT /api/v1/preferences — set job preferences
7. POST /api/v1/credentials/linkedin — connect LinkedIn
8. GET /api/v1/agent/status — check agent status
9. POST /api/v1/agent/start — start agent

Step 5.4: Write a comprehensive test script at scripts/test_e2e.py that:
- Creates a test user
- Completes the full onboarding
- Triggers job discovery
- Verifies a job was matched
- Triggers an application
- Checks application was recorded
- Tests analytics endpoints
- Tests export functionality

═══════════════════════════════════════════
PHASE 6: FINAL FIXES
═══════════════════════════════════════════

After all checks, create a summary of:
1. What was broken and what you fixed
2. What's working perfectly
3. Any remaining issues that need external setup (API keys, etc.)

CRITICAL RULES:
- NEVER leave a file with TODO, FIXME, or placeholder code
- NEVER leave a route that returns "Not implemented"
- EVERY form must have validation
- EVERY API call must have error handling
- EVERY list must have empty and loading states
- Fix issues IN PLACE — don't create new files alongside old ones
- If a file is fundamentally broken, rewrite it completely
- Test as you go — don't wait until the end to find issues
```

---

# RUNNING MULTIPLE AGENTS FOR THE AUDIT

If you want to parallelize the audit, split it into 3 agents:

## Agent A: Backend Audit (Phases 1-2)
Paste the shared context + everything from Phase 1 and Phase 2 above.

## Agent B: Frontend Audit (Phase 3-4)  
Paste the shared context + everything from Phase 3 and Phase 4 above.
Add: "Assume the backend is running at http://localhost:8000 with all endpoints functional."

## Agent C: Integration & Testing (Phase 5-6)
Run this AFTER Agents A and B finish.
Paste Phase 5 and Phase 6.

---

# QUICK VERIFICATION COMMANDS

After all agents finish, run these to verify:

```bash
# 1. Clean start
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# 2. Wait for services
sleep 30

# 3. Check all containers are running
docker-compose ps
# ALL should show "Up" status

# 4. Check backend health
curl http://localhost:8000/health
# Should return: {"status":"ok"}

# 5. Check frontend loads
curl -s http://localhost:3000 | head -20
# Should return HTML

# 6. Run migrations
docker-compose exec backend alembic upgrade head

# 7. Test registration
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test1234!","full_name":"Test User"}'

# 8. Test login  
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test1234!"}'

# 9. Check backend logs for errors
docker-compose logs backend --tail=50

# 10. Check frontend build
docker-compose exec frontend npm run build

# 11. Run backend tests
docker-compose exec backend pytest -v --tb=short

# 12. Check RabbitMQ has queues
curl -u jobpilot:rabbitmq_password http://localhost:15672/api/queues
```

# WHAT "PRODUCTION-READY" MEANS — CHECKLIST

## Backend
- [ ] All 50+ API endpoints return proper responses
- [ ] Auth flow works (register → verify → login → refresh → logout)
- [ ] File upload works (resume PDF/DOCX)
- [ ] Credential encryption/decryption works
- [ ] Celery tasks are discoverable and runnable
- [ ] Database migrations run cleanly
- [ ] Rate limiting is active
- [ ] CORS is properly configured
- [ ] WebSocket connections work
- [ ] Error responses are consistent JSON format

## Frontend  
- [ ] Landing page is visually impressive and responsive
- [ ] All auth forms work with validation
- [ ] Dashboard loads with real data
- [ ] All 15+ dashboard pages are functional
- [ ] Sidebar navigation works
- [ ] Dark mode works everywhere
- [ ] Mobile responsive everywhere
- [ ] Loading states on all async operations
- [ ] Empty states on all lists
- [ ] Error handling on all API calls
- [ ] Toast notifications work
- [ ] Charts render correctly

## Infrastructure
- [ ] All Docker containers start and stay running
- [ ] Database initializes with schema
- [ ] Redis connects properly
- [ ] RabbitMQ accepts connections
- [ ] Celery workers register tasks
- [ ] Celery beat schedules tasks
- [ ] Frontend can reach backend API
