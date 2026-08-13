# LeadOS

Internal Lead Generation Platform for Sanestix.

## What's Built So Far
This repository contains a clean, empty foundation for the LeadOS monolithic application. 
Currently, **only the bootstrap phase is complete. No real features exist yet.**

What is included:
- **Docker Compose Setup:** A complete local development environment containing 4 containers (Postgres, FastAPI Backend, Next.js Frontend, and n8n).
- **Alembic Migrations:** The exact database schema based on the architecture doc has been implemented and run. All 8 core tables exist (users, campaigns, jobs, companies, contacts, apify_accounts, apollo_accounts, hubspot_sync_logs).
- **Backend / Frontend Skeletons:** Minimal, healthy endpoints to ensure full stack boot logic works correctly (ex: `/health` for backend). No auth, no real routes, and no n8n workflows are built out yet.

## Prerequisites
- Docker & Docker Compose
- Make sure ports 8000, 3000, 5678, and 5432 are open on your machine.

## Setup & Running Locally

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd LeadOS
   ```

2. **Setup environment variables:**
   Copy the example environment file and adjust if necessary (defaults are development-safe).
   ```bash
   cp .env.example .env
   ```

3. **Start the environment from scratch:**
   ```bash
   docker compose -f docker/docker-compose.yml up -d --build
   ```

4. **Run database migrations (Alembic):**
   Once the containers are running, apply the database schema by executing the following inside the backend container:
   ```bash
   docker exec docker-backend-1 alembic upgrade head
   ```

## Service Access URLs

- **Next.js Frontend:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Backend (Health):** [http://localhost:8000/health](http://localhost:8000/health)
- **FastAPI Auto-Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **n8n Orchestrator:** [http://localhost:5678](http://localhost:5678)
- **Postgres Local Client:** `postgresql://leados_user:leados_password@localhost:5432/leados_db`
