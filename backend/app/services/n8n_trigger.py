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


def trigger_run_campaign(
    campaign_id: UUID,
    industry: str,
    country: Optional[str],
    state: Optional[str],
    max_leads: int,
) -> None:
    """Kick off the 'Run Campaign' n8n workflow for a newly created campaign.

    STUB: does not make any real HTTP call. Just logs the payload that
    would be sent to the n8n webhook, so POST /campaigns can be developed
    and tested end-to-end before any n8n workflows exist.

    TODO (later Antigravity prompt, once n8n workflows exist):
        - POST to settings.N8N_RUN_CAMPAIGN_WEBHOOK_URL (add to
          core/config.py) with a JSON body of
          {campaign_id, industry, country, state, max_leads}.
        - Handle/log request failures without raising — a failed trigger
          shouldn't crash the POST /campaigns response since the Campaign
          and Job rows are already committed at that point. Consider
          marking the Job as FAILED with an error_message instead.
    """
    logger.info(
        "would trigger n8n here: run_campaign webhook | campaign_id=%s "
        "industry=%r country=%r state=%r max_leads=%s",
        campaign_id,
        industry,
        country,
        state,
        max_leads,
    )
