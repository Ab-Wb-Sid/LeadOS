from typing import List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.dependencies import verify_internal_api_key
from app.db.session import get_db
from app.models.campaign import Campaign
from app.models.company import Company
from app.models.contact import Contact
from app.models.job import Job
from app.services.dedup import normalize_domain
from app.services.scoring import score_company
from app.services.encryption import decrypt
from sqlalchemy.sql import func

# Protect all routes in this router with the internal API key dependency
router = APIRouter(
    prefix="/internal",
    tags=["Internal"],
    dependencies=[Depends(verify_internal_api_key)],
)


# --- Schemas ---

class ScrapedCompanyCreate(BaseModel):
    name: str
    website: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    source: Optional[str] = None
    google_rating: Optional[float] = None
    review_count: Optional[int] = None


class BulkCompanyInsertRequest(BaseModel):
    campaign_id: UUID
    companies: List[ScrapedCompanyCreate]


class ContactEnrichmentCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    email: str
    linkedin_url: Optional[str] = None
    apollo_source_id: Optional[str] = None
    verification_status: Optional[str] = None


class BulkContactEnrichmentRequest(BaseModel):
    company_id: UUID
    contacts: List[ContactEnrichmentCreate]


class JobStatusUpdateRequest(BaseModel):
    status: str  # RUNNING, SUCCESS, FAILED
    error_message: Optional[str] = None


class CampaignStatusUpdateRequest(BaseModel):
    status: str  # SCRAPING, ENRICHING, SYNCING, COMPLETED, FAILED


# --- Routes ---

@router.get("/campaigns/{campaign_id}/companies/cleaned")
def get_cleaned_companies(
    campaign_id: UUID,
    db: Session = Depends(get_db)
) -> Any:
    """
    Returns a list of companies for a given campaign that are in CLEANED status.
    Used by n8n to fetch companies that need enrichment.
    """
    companies = db.query(Company).filter(
        Company.campaign_id == campaign_id,
        Company.status == 'CLEANED'
    ).all()
    
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "website": c.website,
            "normalized_domain": c.normalized_domain
        }
        for c in companies
    ]

@router.get("/apify-accounts/available")
def claim_apify_account(db: Session = Depends(get_db)):
    """
    Atomically claims one ACTIVE Apify account.
    Avoids race conditions using FOR UPDATE SKIP LOCKED.
    """
    query = text("""
        UPDATE apify_accounts 
        SET last_used_at = now() 
        WHERE id = (
            SELECT id FROM apify_accounts 
            WHERE status = 'ACTIVE' 
            LIMIT 1 
            FOR UPDATE SKIP LOCKED
        ) 
        RETURNING id, api_key
    """)
    result = db.execute(query).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No active Apify accounts available"
        )
    
    db.commit()
    
    account_id, encrypted_key = result
    
    return {
        "id": account_id,
        "api_key": decrypt(encrypted_key)
    }


@router.get("/apollo-accounts/available")
def claim_apollo_account(db: Session = Depends(get_db)):
    """
    Atomically claims one ACTIVE Apollo account.
    Avoids race conditions using FOR UPDATE SKIP LOCKED.
    """
    query = text("""
        UPDATE apollo_accounts 
        SET last_used_at = now() 
        WHERE id = (
            SELECT id FROM apollo_accounts 
            WHERE status = 'ACTIVE' 
            LIMIT 1 
            FOR UPDATE SKIP LOCKED
        ) 
        RETURNING id, api_key
    """)
    result = db.execute(query).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No active Apollo accounts available"
        )
    
    db.commit()
    
    account_id, encrypted_key = result
    
    return {
        "id": account_id,
        "api_key": decrypt(encrypted_key)
    }


@router.post("/companies/bulk")
def bulk_insert_companies(
    payload: BulkCompanyInsertRequest, 
    db: Session = Depends(get_db)
):
    """
    Bulk upserts scraped companies.
    Uses ON CONFLICT DO NOTHING to gracefully handle cross-campaign duplicates.
    Marks newly inserted rows as CLEANED.
    """
    if not payload.companies:
        return {"new": 0, "found": 0}
        
    values = []
    seen_domains = set()
    
    # 1. Pre-process payload and dedup internally
    for comp in payload.companies:
        nd = normalize_domain(comp.website) or None
        
        if nd:
            # Skip if we already have this domain in the current payload
            if nd in seen_domains:
                continue
            seen_domains.add(nd)
            
        val = comp.model_dump()
        val["campaign_id"] = payload.campaign_id
        val["normalized_domain"] = nd
        val["status"] = "CLEANED"
        
        values.append(val)
        
    # 2. Bulk insert with ON CONFLICT DO NOTHING
    if not values:
        return {"new": 0, "found": len(payload.companies)}
        
    stmt = insert(Company).values(values)
    stmt = stmt.on_conflict_do_nothing(index_elements=["normalized_domain"])
    stmt = stmt.returning(Company.id)
    
    result = db.execute(stmt)
    inserted_ids = result.scalars().all()
    
    inserted_count = len(inserted_ids)
    found_count = len(payload.companies) - inserted_count
    
    # 3. Update campaign total_scraped count
    db.execute(
        update(Campaign)
        .where(Campaign.id == payload.campaign_id)
        .values(total_scraped=Campaign.total_scraped + len(payload.companies))
    )
    
    db.commit()
    
    return {
        "new": inserted_count,
        "found": found_count
    }


@router.post("/contacts/bulk")
def bulk_insert_contacts(
    payload: BulkContactEnrichmentRequest,
    db: Session = Depends(get_db)
):
    """
    Accepts enrichment results for a company, upserts contacts on email,
    marks the parent company status=ENRICHED, calls score_company(),
    and updates campaigns.total_enriched.
    """
    # 1. Fetch existing contacts to simulate UPSERT on email
    existing_contacts = db.query(Contact).filter(Contact.company_id == payload.company_id).all()
    existing_by_email = {c.email: c for c in existing_contacts if c.email}
    
    for c_in in payload.contacts:
        if c_in.email in existing_by_email:
            # Update existing
            db_contact = existing_by_email[c_in.email]
            update_data = c_in.model_dump(exclude_unset=True)
            for k, v in update_data.items():
                setattr(db_contact, k, v)
        else:
            # Insert new
            new_contact = Contact(company_id=payload.company_id, **c_in.model_dump())
            db.add(new_contact)
            existing_by_email[c_in.email] = new_contact
            
    db.flush()
    
    # 2. Update company status and score
    company = db.query(Company).filter(Company.id == payload.company_id).first()
    if company:
        company.status = "ENRICHED"
        
        # Attach contacts dynamically for the pure scoring function
        company.contacts = list(existing_by_email.values())
        company.lead_score = score_company(company)
        
        # 3. Update campaign total_enriched count
        if company.campaign_id:
            db.execute(
                update(Campaign)
                .where(Campaign.id == company.campaign_id)
                .values(total_enriched=Campaign.total_enriched + 1)
            )
            
    db.commit()
    return {"status": "ok", "contacts_processed": len(payload.contacts)}


@router.post("/jobs/{job_id}/status")
def update_job_status(
    job_id: UUID,
    payload: JobStatusUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Updates a job's status and timestamps based on transitions.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job.status = payload.status
    if payload.error_message:
        job.error_message = payload.error_message
        
    if payload.status == "RUNNING":
        job.started_at = func.now()
    elif payload.status in ("SUCCESS", "FAILED"):
        job.finished_at = func.now()
        
    db.commit()
    return {"status": "ok"}


@router.post("/campaigns/{campaign_id}/status")
def update_campaign_status(
    campaign_id: UUID,
    payload: CampaignStatusUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Updates a campaign's status and sets completed_at if COMPLETED.
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    campaign.status = payload.status
    
    if payload.status == "COMPLETED":
        campaign.completed_at = func.now()
        
    db.commit()
    return {"status": "ok"}
