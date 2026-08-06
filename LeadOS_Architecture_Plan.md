# LeadOS — System Architecture & Implementation Plan
### Internal Lead Generation Platform for Sanestix

---

## 1. System Architecture

### 1.1 High-Level Principle

LeadOS is a **single monolithic application** with three moving parts:

1. **Next.js frontend** — dashboard, campaign management, account management.
2. **FastAPI backend** — the only source of truth. Owns the database, exposes REST APIs, and is the only service allowed to write to Postgres.
3. **n8n** — acts as your *job runner / orchestrator*, replacing Celery + Redis. It calls Apify, polls for scrape completion, calls Apollo for enrichment, and calls HubSpot for sync — then reports results back to FastAPI via internal webhook endpoints.

This is the key architectural decision that lets you skip Celery/Redis/Kafka entirely: **n8n is your task queue.** FastAPI never blocks on long-running scraping — it kicks off an n8n workflow and returns immediately. n8n does the slow work asynchronously and calls back into FastAPI when done.

### 1.2 Data Flow

```
User creates campaign (Next.js)
        │
        ▼
FastAPI: POST /campaigns
   - creates Campaign row (status=PENDING)
   - creates Job row
   - triggers n8n webhook (campaign_id, industry, location, max_leads)
        │
        ▼
n8n Workflow: "Run Campaign"
   1. Pick available Apify account (calls FastAPI: GET /internal/apify-accounts/available)
   2. Run Apify actor for scraping
   3. Poll Apify run until finished
   4. POST raw companies → FastAPI: POST /internal/companies/bulk
   5. FastAPI dedupes + cleans, marks companies as CLEANED
   6. n8n triggers enrichment sub-workflow
   7. Pick available Apollo account
   8. For each cleaned company → call Apollo → get contacts
   9. POST contacts → FastAPI: POST /internal/contacts/bulk
   10. FastAPI marks companies ENRICHED, scores leads
   11. n8n (or a manual "Sync" button) triggers HubSpot sync workflow
   12. FastAPI marks campaign COMPLETED, updates counts
```

Every step that touches Apify/Apollo/HubSpot happens **inside n8n**, not inside FastAPI. FastAPI's job is: store state, expose data, do business logic (dedup, scoring, status transitions). This keeps your Python backend simple and keeps all "flaky third-party API" pain isolated inside n8n where you already have retry/error-branch tooling.

### 1.3 Architecture Diagram

```
                         ┌─────────────────────┐
                         │   Next.js Dashboard   │
                         │  (React + Tailwind)   │
                         └──────────┬───────────┘
                                    │ REST (JWT/session)
                                    ▼
                         ┌─────────────────────┐
                         │   FastAPI Backend     │
                         │  - Auth (simple)      │
                         │  - CRUD APIs          │
                         │  - Dedup/Scoring logic│
                         │  - Internal webhooks  │
                         └──────┬───────┬────────┘
                                │       │
                    ┌───────────┘       └───────────┐
                    ▼                                ▼
            ┌───────────────┐               ┌──────────────────┐
            │  PostgreSQL    │               │   n8n Workflows   │
            │  (single DB)   │◄──────────────┤  - Scrape workflow │
            └───────────────┘   webhooks     │  - Enrich workflow │
                                              │  - Sync workflow   │
                                              └─────────┬──────────┘
                                                         │
                                     ┌───────────────────┼───────────────────┐
                                     ▼                   ▼                   ▼
                                  Apify               Apollo              HubSpot
```

### 1.4 Why not Celery/Redis?

You explicitly want minimum tech. n8n already gives you:
- Retry logic per node
- Visual debugging of failed runs
- Polling/wait nodes for long-running scrapes
- Easy credential rotation across multiple Apify/Apollo accounts

Adding Celery+Redis on top would duplicate what n8n already does for this workload. Revisit this only if you outgrow n8n's execution concurrency limits (unlikely at your current campaign volume).

### 1.5 Authentication

Since you excluded "separate authentication providers," use FastAPI's built-in simple approach:
- One `users` table (your internal sales team, not customers)
- Email + hashed password (bcrypt) login
- JWT issued by FastAPI itself, stored in an httpOnly cookie
- No Auth0/Clerk/Firebase — this avoids external dependency and is genuinely sufficient for an internal tool with under ~10 users.

---

## 2. Database Schema (PostgreSQL)

```sql
-- USERS (internal team, not customers)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL,
    email VARCHAR(160) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'sales',  -- 'admin' | 'sales'
    created_at TIMESTAMPTZ DEFAULT now()
);

-- CAMPAIGNS
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    industry VARCHAR(120) NOT NULL,
    country VARCHAR(80),
    state VARCHAR(80),
    max_leads INT NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, SCRAPING, ENRICHING, SYNCING, COMPLETED, FAILED
    total_scraped INT DEFAULT 0,
    total_enriched INT DEFAULT 0,
    total_imported INT DEFAULT 0,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- JOBS (tracks each async step tied to a campaign — this is your "queue log")
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id),
    job_type VARCHAR(30) NOT NULL,  -- SCRAPE, ENRICH, SYNC
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, RUNNING, SUCCESS, FAILED
    error_message TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);

-- COMPANIES
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id),
    name VARCHAR(255) NOT NULL,
    website VARCHAR(255),
    normalized_domain VARCHAR(255),  -- used for deduplication
    phone VARCHAR(50),
    address VARCHAR(255),
    city VARCHAR(120),
    state VARCHAR(120),
    country VARCHAR(120),
    industry VARCHAR(120),
    source VARCHAR(50),              -- 'apify'
    google_rating NUMERIC(2,1),
    review_count INT,
    lead_score INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'RAW', -- RAW, CLEANED, ENRICHED, READY, HUBSPOT, CONTACTED, QUALIFIED, CUSTOMER
    hubspot_company_id VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (normalized_domain)  -- global dedup across all campaigns
);
CREATE INDEX idx_companies_status ON companies(status);
CREATE INDEX idx_companies_campaign ON companies(campaign_id);

-- CONTACTS
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    position VARCHAR(150),
    email VARCHAR(255),
    linkedin_url VARCHAR(255),
    apollo_source_id VARCHAR(100),
    verification_status VARCHAR(20),  -- verified, guessed, unknown
    hubspot_contact_id VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_contacts_company ON contacts(company_id);

-- APIFY ACCOUNTS
CREATE TABLE apify_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL,
    api_key VARCHAR(255) NOT NULL,   -- encrypt at rest (see Best Practices)
    remaining_credits NUMERIC(10,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ACTIVE',  -- ACTIVE, COOLDOWN, DISABLED
    reset_date DATE,
    last_used_at TIMESTAMPTZ
);

-- APOLLO ACCOUNTS
CREATE TABLE apollo_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL,
    api_key VARCHAR(255) NOT NULL,
    remaining_credits NUMERIC(10,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    reset_date DATE,
    last_used_at TIMESTAMPTZ
);

-- HUBSPOT SYNC LOGS
CREATE TABLE hubspot_sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    contact_id UUID REFERENCES contacts(id),
    sync_status VARCHAR(20),   -- SUCCESS, FAILED, SKIPPED_DUPLICATE
    error_message TEXT,
    synced_at TIMESTAMPTZ DEFAULT now()
);
```

**Deduplication strategy:** normalize `website` → strip protocol, `www.`, trailing slash → store in `normalized_domain` with a UNIQUE constraint. This is your single source of dedup truth across campaigns, not just within one campaign.

---

## 3. API Design (FastAPI)

### Public (used by Next.js dashboard)

```
Auth
POST   /auth/login
POST   /auth/logout
GET    /auth/me

Dashboard
GET    /dashboard/stats

Campaigns
POST   /campaigns                 -- create + trigger n8n
GET    /campaigns
GET    /campaigns/{id}
GET    /campaigns/{id}/companies

Companies
GET    /companies?status=&industry=&search=
GET    /companies/{id}
PATCH  /companies/{id}            -- manual status update (e.g. mark Contacted)

Contacts
GET    /contacts?company_id=

Apify Accounts
GET    /apify-accounts
POST   /apify-accounts
PATCH  /apify-accounts/{id}

Apollo Accounts
GET    /apollo-accounts
POST   /apollo-accounts
PATCH  /apollo-accounts/{id}

HubSpot
POST   /hubspot/sync/{company_id}
POST   /hubspot/sync-bulk         -- body: list of company_ids
GET    /hubspot/logs
```

### Internal (called only by n8n, protected by a shared internal secret header, not exposed publicly)

```
GET    /internal/apify-accounts/available
GET    /internal/apollo-accounts/available
POST   /internal/companies/bulk       -- raw scrape results in
POST   /internal/contacts/bulk        -- enrichment results in
POST   /internal/jobs/{id}/status     -- n8n reports job progress/failure
POST   /internal/campaigns/{id}/status
```

Splitting `/internal/*` from the public API is important: it means your webhook surface can be locked down with a simple shared-secret header (`X-Internal-Key`) instead of full user auth, since n8n isn't a logged-in user.

---

## 4. Folder Structure

```
leados/
├── frontend/                     # Next.js
│   ├── app/
│   │   ├── dashboard/
│   │   ├── campaigns/
│   │   ├── companies/
│   │   ├── contacts/
│   │   ├── accounts/
│   │   │   ├── apify/
│   │   │   └── apollo/
│   │   ├── hubspot/
│   │   └── login/
│   ├── components/
│   ├── lib/                      # api client, auth helpers
│   └── package.json
│
├── backend/                      # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── models/                # SQLAlchemy models
│   │   ├── schemas/               # Pydantic schemas
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── campaigns.py
│   │   │   ├── companies.py
│   │   │   ├── contacts.py
│   │   │   ├── apify_accounts.py
│   │   │   ├── apollo_accounts.py
│   │   │   ├── hubspot.py
│   │   │   └── internal.py        # n8n-only endpoints
│   │   ├── services/
│   │   │   ├── dedup.py
│   │   │   ├── scoring.py
│   │   │   ├── hubspot_client.py
│   │   │   └── n8n_trigger.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   └── db/
│   │       ├── session.py
│   │       └── migrations/        # Alembic
│   ├── requirements.txt
│   └── Dockerfile
│
├── n8n/
│   └── workflows/
│       ├── run_campaign.json
│       ├── scrape_apify.json
│       ├── enrich_apollo.json
│       └── sync_hubspot.json
│
├── docker/
│   └── docker-compose.yml
│
└── README.md
```

---

## 5. Development Roadmap

| Phase | Scope | Est. Time |
|---|---|---|
| 1 | Project scaffold: Next.js + FastAPI + Postgres + Docker Compose, auth login | 3–4 days |
| 2 | Campaign creation, dashboard stats, campaign history, company list view | 4–5 days |
| 3 | Apify account manager + n8n scrape workflow + dedup on ingest | 4–5 days |
| 4 | Apollo account manager + n8n enrich workflow + contact storage | 4–5 days |
| 5 | HubSpot integration (company + contact create, dedup check) | 3–4 days |
| 6 | Lead pipeline status tracking, filtering/search, campaign analytics | 3–4 days |

Total realistic MVP: **~4 weeks** part-time, assuming you're the primary builder alongside coursework.

---

## 6. UI Wireframes (text-based)

### Dashboard
```
┌────────────────────────────────────────────────────────────┐
│  LeadOS                                     [Sid ▾] [Logout]│
├────────────────────────────────────────────────────────────┤
│  Total Scraped: 4,210   Enriched: 2,980   Imported: 2,100   │
│  Active Jobs: 2          Failed Jobs: 1                     │
├────────────────────────────────────────────────────────────┤
│  Apify Accounts          │  Apollo Accounts                │
│  ● Account A  $4.20      │  ● Account A  120 credits        │
│  ● Account B  cooldown   │  ● Account B  0 (reset Sep 6)     │
├────────────────────────────────────────────────────────────┤
│  Recent Campaigns                                           │
│  Garage Door USA        COMPLETED   500 → 350 → 290         │
│  Roofing TX              RUNNING     120 → –   → –           │
└────────────────────────────────────────────────────────────┘
```

### Campaign Creation
```
┌───────────────────────────────┐
│ New Campaign                  │
├───────────────────────────────┤
│ Industry:  [Garage Door Repair▾]│
│ Country:   [United States ▾]  │
│ State:     [Texas ▾]          │
│ Max Leads: [500]              │
│                                │
│         [ Start Campaign ]     │
└───────────────────────────────┘
```

### Companies List
```
┌──────────────────────────────────────────────────────────┐
│ Filter: [Status ▾] [Industry ▾] [Search...........]      │
├──────────────────────────────────────────────────────────┤
│ Name           City      Status      Score   HubSpot     │
│ Acme Doors     Austin    ENRICHED    82      —           │
│ Best Garage    Dallas    HUBSPOT     91      ✔ synced    │
└──────────────────────────────────────────────────────────┘
```

### Account Manager (Apify/Apollo — same layout)
```
┌────────────────────────────────────────────┐
│ Apify Accounts                [+ Add]      │
├────────────────────────────────────────────┤
│ Account A   $4.20   ACTIVE                 │
│ Account B   $0.00   COOLDOWN (Sep 6)       │
└────────────────────────────────────────────┘
```

---

## 7. Best Practices

- **Idempotent bulk-ingest endpoints.** `/internal/companies/bulk` and `/internal/contacts/bulk` should upsert on `normalized_domain` / `email`, not blind-insert — n8n retries will otherwise create duplicates.
- **Encrypt API keys at rest.** Even internally, don't store Apify/Apollo keys as plaintext — use `pgcrypto` or app-level encryption (Fernet) before writing to `apify_accounts.api_key`.
- **Alembic migrations from day one.** Don't hand-edit schema; every change goes through a migration file so Phase 6 doesn't break Phase 2's data.
- **Shared-secret header for internal routes**, separate from user JWTs — n8n is a service, not a logged-in user.
- **Async I/O in FastAPI** for anything calling n8n or HubSpot directly (use `httpx.AsyncClient`), so the API stays responsive even if a downstream call is slow.
- **Single Docker Compose file** for local dev: postgres, backend, frontend, n8n — one `docker compose up` should get a new contributor running.
- **Lead scoring as a pure function**, isolated in `services/scoring.py`, so you can tune the formula without touching ingestion logic.

---

## 8. Potential Pitfalls

- **Apify/Apollo credit drift:** the credits stored in your DB (`remaining_credits`) will drift from actual account balances unless you periodically reconcile via each provider's API. Build a small n8n "reconcile credits" workflow that runs daily rather than trusting your own decrements.
- **Cross-campaign duplicates:** the same garage-door company could get scraped in two overlapping campaigns (e.g. Texas run + national run). The `normalized_domain` UNIQUE constraint prevents duplicate rows but means your second campaign's "total_scraped" count needs to distinguish "found" vs "newly added."
- **HubSpot duplicate creation:** always search HubSpot by domain/email before creating — don't rely solely on your own `hubspot_company_id` field, in case someone creates records manually in HubSpot outside LeadOS.
- **Long n8n executions timing out:** Apify scrapes can take minutes; make sure n8n's workflow uses polling/wait nodes rather than a single blocking HTTP call with a short timeout.
- **Multi-account race conditions:** if two campaigns start simultaneously and both try to claim "Account A," you need an atomic claim (e.g. `UPDATE ... SET status='IN_USE' WHERE id=... AND status='ACTIVE' RETURNING id`) rather than a read-then-write pattern.
- **Score inflation without ground truth:** lead score is only useful if you feed back real outcomes (which leads became customers) into recalibrating it — otherwise it's a static heuristic that quietly becomes wrong over time.

---

## 9. Suggested Improvements (post-MVP)

- Add a **"reconcile credits" nightly n8n job** as noted above.
- Add **role-based access** (admin can manage accounts/campaigns; sales reps can only update status/contact leads) — cheap to add now via the `role` column, expensive to retrofit later.
- Add **webhook signature verification** if you ever expose `/internal/*` beyond your own network.
- Add **campaign scheduling** (recurring campaigns, e.g. re-scrape Texas garage doors monthly) once the manual flow is proven.
- Add a **simple audit log table** for account credit changes and status transitions — useful when debugging "why did this lead skip HubSpot sync."

---

## 10. Step-by-Step Implementation Plan

1. **Repo & Docker setup** — create the folder structure above, write `docker-compose.yml` with `postgres`, `backend`, `frontend`, `n8n` services.
2. **Postgres schema** — write the SQL above as an initial Alembic migration; run it, confirm tables exist.
3. **FastAPI skeleton** — `main.py`, DB session, `/auth/login` + `/auth/me`, one seeded admin user.
4. **Next.js skeleton** — Tailwind configured, login page wired to `/auth/login`, protected layout for `/dashboard`.
5. **Campaigns CRUD** — `POST /campaigns` (status=PENDING, no n8n trigger yet), `GET /campaigns`, campaign list + creation form in Next.js.
6. **Dashboard stats endpoint** — aggregate counts from `companies`/`campaigns`, render dashboard cards.
7. **Apify account manager** — CRUD endpoints + UI table, manual credit entry for now (no live API check yet).
8. **n8n scrape workflow** — build "Run Campaign" workflow: webhook trigger → call `/internal/apify-accounts/available` → run Apify actor → poll → POST results to `/internal/companies/bulk`.
9. **Wire campaign creation to n8n** — `POST /campaigns` now also calls n8n's webhook URL; campaign status flips to SCRAPING → CLEANED.
10. **Apollo account manager + enrich workflow** — same pattern as steps 7–8, ending in `POST /internal/contacts/bulk`.
11. **Lead scoring** — implement `services/scoring.py`, run automatically after enrichment, expose score in company list/filter.
12. **HubSpot integration** — build the sync workflow (dedup check by domain/email, create company + associated contact), wire the "Sync to HubSpot" button.
13. **Pipeline status + filtering/search** — company list filters by status/industry/search, manual status transitions (Contacted, Qualified, Customer) via `PATCH /companies/{id}`.
14. **Campaign history + analytics** — campaign detail page showing scraped/enriched/imported counts, rerun option.
15. **Polish pass** — error states for failed jobs, account cooldown display, basic role separation if needed.

Each step above is independently testable — you can demo working software after every single one, which matches your preference for phased, concrete deliverables over big upfront builds.
