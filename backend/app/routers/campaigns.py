from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.campaign import Campaign
from app.models.company import Company
from app.models.job import Job
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.campaign import CampaignCreate, CampaignListResponse, CampaignRead
from app.schemas.company import CompanyListResponse
from app.services.n8n_trigger import trigger_run_campaign

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _get_campaign_or_404(campaign_id: UUID, db: Session) -> Campaign:
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


@router.post("", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
def create_campaign(
    payload: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a campaign and kick off the scrape.

    Per the architecture doc's data flow (section 1.2):
      1. create Campaign row (status=PENDING)
      2. create a Job row (job_type=SCRAPE, status=PENDING) tied to it
      3. trigger the n8n 'Run Campaign' webhook (currently stubbed —
         see services/n8n_trigger.py; no real HTTP call happens yet)

    Everything here happens in one commit so a campaign is never left
    without its initial SCRAPE job.
    """
    campaign = Campaign(
        name=payload.name,
        industry=payload.industry,
        country=payload.country,
        state=payload.state,
        max_leads=payload.max_leads,
        status="PENDING",
        created_by=current_user.id,
    )
    db.add(campaign)
    db.flush()  # assigns campaign.id without ending the transaction

    job = Job(
        campaign_id=campaign.id,
        job_type="SCRAPE",
        status="PENDING",
    )
    db.add(job)

    db.commit()
    db.refresh(campaign)

    # Stub for now — logs what would be sent to n8n. Doesn't raise, so a
    # trigger "failure" (there isn't a real call yet) can never roll back
    # or block the response; the Campaign/Job rows above are already
    # committed and are the source of truth.
    trigger_run_campaign(
        campaign_id=campaign.id,
        job_id=job.id,
        industry=campaign.industry,
        country=campaign.country,
        state=campaign.state,
        max_leads=campaign.max_leads,
    )

    return campaign


@router.get("", response_model=CampaignListResponse)
def list_campaigns(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Most-recent-first, paginated list of campaigns."""
    base_query = db.query(Campaign)
    total = base_query.count()
    items = (
        base_query.order_by(Campaign.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return CampaignListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{campaign_id}", response_model=CampaignRead)
def get_campaign(
    campaign_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_campaign_or_404(campaign_id, db)


@router.get("/{campaign_id}/companies", response_model=CompanyListResponse)
def list_campaign_companies(
    campaign_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Paginated list of companies scraped for a given campaign.

    404s if the campaign itself doesn't exist, rather than silently
    returning an empty page — that distinction matters once the frontend
    is showing this.
    """
    _get_campaign_or_404(campaign_id, db)

    base_query = db.query(Company).filter(Company.campaign_id == campaign_id)
    total = base_query.count()
    items = (
        base_query.order_by(Company.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return CompanyListResponse(items=items, total=total, page=page, page_size=page_size)
