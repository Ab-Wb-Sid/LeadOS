"""Stub for triggering the n8n 'Run Campaign' workflow.

Per the architecture doc (section 1.2), POST /campaigns is supposed to
hand off scraping work to n8n and return immediately — FastAPI never
blocks on the actual scrape. The n8n workflows (run_campaign,
scrape_apify, enrich_apollo, sync_hubspot) don't exist yet, so this is
intentionally a no-op that just logs what *would* happen.

Replace the body of `trigger_run_campaign` with a real HTTP call (e.g.
POST to the n8n webhook URL with campaign_id/industry/location/max_leads)
once the run_campaign workflow is built. Keep the function signature
stable so routers/campaigns.py doesn't need to change when that happens.
"""

import logging
from typing import Optional
from uuid import UUID

logger = logging.getLogger("leados.n8n_trigger")


import threading
import httpx
import asyncio
from app.core.config import settings

def _fire_webhook(payload: dict):
    async def do_request():
        url = settings.N8N_RUN_CAMPAIGN_WEBHOOK_URL
        if not url:
            logger.warning("N8N_RUN_CAMPAIGN_WEBHOOK_URL is not set. Skipping n8n trigger.")
            return
            
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Firing n8n webhook: {url}")
                await client.post(url, json=payload, timeout=10.0)
            except Exception as e:
                logger.error("Failed to trigger n8n: %s", e)
    
    try:
        asyncio.run(do_request())
    except Exception as e:
        logger.error("Background task error: %s", e)

def trigger_run_campaign(
    campaign_id: UUID,
    job_id: UUID,
    industry: str,
    country: Optional[str],
    state: Optional[str],
    max_leads: int,
) -> None:
    """Kick off the 'Run Campaign' n8n workflow for a newly created campaign.
    
    Fires the HTTP request in a background thread to prevent blocking the FastAPI 
    response, adhering to the fire-and-forget architecture constraint.
    """
    location_parts = [p for p in (state, country) if p]
    location = ", ".join(location_parts) if location_parts else "Global"
    
    payload = {
        "campaign_id": str(campaign_id),
        "job_id": str(job_id),
        "industry": industry,
        "location": location,
        "max_leads": max_leads
    }
    
    thread = threading.Thread(target=_fire_webhook, args=(payload,), daemon=True)
    thread.start()
