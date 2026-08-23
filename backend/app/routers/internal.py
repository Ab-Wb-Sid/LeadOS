from typing import List, Optional
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
from app.services.dedup import normalize_domain
from app.services.encryption import decrypt

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


# --- Routes ---

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
