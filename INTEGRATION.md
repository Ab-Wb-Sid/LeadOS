# LeadOS n8n Integration Summary

This document summarizes the integration testing and hardening of the LeadOS backend orchestrator with n8n.

## Testing & Fixes Applied

1. **Fire-and-Forget Architecture**: 
   - Replaced the `n8n_trigger.py` stub with a real `httpx.AsyncClient` HTTP call.
   - Wrapped the HTTP call in a background `threading.Thread` executing `asyncio.run()`, ensuring that `POST /campaigns` returns a response instantly without blocking on n8n orchestration.

2. **Atomic Account Claiming & LRU Load Balancing**:
   - Simulated heavy concurrent load on the `GET /internal/apify-accounts/available` endpoint.
   - Verified that `FOR UPDATE SKIP LOCKED` successfully prevented race conditions (no two concurrent workflows locked the same account).
   - **Fix Applied**: Added `ORDER BY last_used_at ASC NULLS FIRST` to the SQL query. Without it, PostgreSQL returned the first physical row repeatedly as locks cleared, destroying load distribution. With the fix, accounts rotate perfectly on a Least-Recently-Used basis.

3. **Cross-Campaign Duplicates**:
   - Sent a simulated scrape payload containing a duplicate `website` already belonging to a previous campaign.
   - Verified that PostgreSQL's `ON CONFLICT DO NOTHING` constraint safely skipped the duplicate insertion without crashing the bulk endpoint.
   - Verified that the system correctly calculates `found_count = len(payload) - inserted_count` and updates the Campaign's `total_scraped` metric by the full payload size, while ensuring the duplicate is NOT enriched a second time (saving Apollo credits).

4. **Failure Path & Polling**:
   - Fixed the `run_campaign` n8n workflow to gracefully catch errors from downstream nodes (`scrape_apify`, `enrich_apollo`) using `continueOnFail` and `IF` logic, ensuring it pings `POST /internal/jobs/{id}/status` and `/campaigns/{id}/status` with `FAILED`.
   - Added a `setInterval` 5-second polling loop to the frontend `(dashboard)/page.tsx` and `campaigns/page.tsx` to automatically reflect job progression and failure states without manual page refreshes.

## Current State (Mocked vs. Live)

* **LIVE**: 
  * Complete FastAPI backend architecture and endpoints.
  * PostgreSQL database schemas, constraints, and relationships.
  * n8n webhook routing, execution coordination, and internal backend communication.
  * Next.js frontend state management and API integration.
* **MOCKED (Apify)**: The `scrape_apify` n8n workflow generates synthetic company payloads instead of making live Apify API calls.
* **MOCKED (Apollo)**: The `enrich_apollo` n8n workflow returns static "Jane Doe" contact structures instead of hitting the live Apollo API.
* **MOCKED (HubSpot)**: The manual sync button is not yet integrated with a live HubSpot n8n workflow.

## Fragilities to Harden Later

1. **Silent Timeout Hangs**: Currently, if the n8n container crashes, is unreachable, or an execution hangs indefinitely without triggering the FAILED endpoint, the campaign will sit in `PENDING` or `SCRAPING` forever. Implementing a Python background sweeper (e.g., using `apscheduler` or Celery Beat) to automatically mark jobs `FAILED` if their `started_at` is older than 60 minutes is highly recommended.
2. **Retry Logic**: There is currently no automatic retry mechanism if the Apify or Apollo API responds with a temporary 502/503. n8n's built-in node retry settings should be configured before swapping the mock nodes for live HTTP requests.
