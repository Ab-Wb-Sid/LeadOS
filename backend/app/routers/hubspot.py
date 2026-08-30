from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import UUID4
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.company import Company
from app.models.contact import Contact
from app.models.hubspot_sync_log import HubspotSyncLog
from app.models.user import User
from app.routers.auth import get_current_user, require_admin
from app.schemas.hubspot import BulkSyncRequest, BulkSyncResponse, HubspotSyncLogOut, SyncResultSummary
from app.schemas.pagination import Page
from app.services.hubspot_client import (
    create_company,
    create_contact,
    find_company_by_domain,
    find_contact_by_email,
)

router = APIRouter(prefix="/hubspot", tags=["HubSpot"], dependencies=[Depends(require_admin)])


async def _sync_single_company(db: Session, company_id: UUID4) -> SyncResultSummary:
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return SyncResultSummary(company_id=company_id, status="FAILED", error="Company not found")

        # 1. Sync Company
        hs_comp_id = None
        if company.normalized_domain:
            found_company = await find_company_by_domain(company.normalized_domain)
            if found_company:
                hs_comp_id = found_company.get("id")

        if not hs_comp_id:
            comp_data = {
                "name": company.name,
                "domain": company.website or company.normalized_domain,
                "phone": company.phone,
                "address": company.address,
                "city": company.city,
                "state": company.state,
                "country": company.country,
                "industry": company.industry,
                "website": company.website,
            }
            new_comp = await create_company(comp_data)
            hs_comp_id = new_comp.get("id")

        if not hs_comp_id:
            raise Exception("Failed to get or create HubSpot Company ID")

        company.hubspot_company_id = hs_comp_id
        company.status = "HUBSPOT"

        # 2. Sync Contact (Primary contact only, assuming the first one associated)
        contact = db.query(Contact).filter(Contact.company_id == company.id).first()
        if contact and contact.email:
            hs_cont_id = None
            found_contact = await find_contact_by_email(contact.email)
            if found_contact:
                hs_cont_id = found_contact.get("id")

            if not hs_cont_id:
                cont_data = {
                    "email": contact.email,
                    "first_name": contact.first_name,
                    "last_name": contact.last_name,
                    "position": contact.position,
                    "linkedin_url": contact.linkedin_url,
                }
                new_cont = await create_contact(cont_data, hs_comp_id)
                hs_cont_id = new_cont.get("id")

            if hs_cont_id:
                contact.hubspot_contact_id = hs_cont_id

        # 3. Log Success
        log = HubspotSyncLog(
            company_id=company.id,
            contact_id=contact.id if contact else None,
            sync_status="SUCCESS",
        )
        db.add(log)
        db.commit()
        return SyncResultSummary(company_id=company_id, status="SUCCESS")

    except Exception as e:
        db.rollback()
        log = HubspotSyncLog(
            company_id=company_id,
            sync_status="FAILED",
            error_message=str(e),
        )
        db.add(log)
        db.commit()
        return SyncResultSummary(company_id=company_id, status="FAILED", error=str(e))


@router.post("/sync/{company_id}", response_model=SyncResultSummary)
async def sync_company(
    company_id: UUID4, 
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Syncs a single company (and its primary contact) to HubSpot.
    Validates duplicates by domain/email first to prevent redundant creation.
    """
    result = await _sync_single_company(db, company_id)
    if result.status == "FAILED":
        raise HTTPException(status_code=400, detail=result.error)
    return result


@router.post("/sync-bulk", response_model=BulkSyncResponse)
async def sync_bulk(
    request: BulkSyncRequest, 
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Syncs a batch of companies to HubSpot sequentially.
    """
    results = []
    for cid in request.company_ids:
        res = await _sync_single_company(db, cid)
        results.append(res)
    return BulkSyncResponse(results=results)


@router.get("/logs", response_model=Page[HubspotSyncLogOut])
def get_logs(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Retrieve paginated HubSpot sync logs joined with company names.
    """
    total = db.query(HubspotSyncLog).count()
    
    logs = (
        db.query(HubspotSyncLog, Company.name.label("company_name"))
        .outerjoin(Company, HubspotSyncLog.company_id == Company.id)
        .order_by(HubspotSyncLog.synced_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for log, c_name in logs:
        items.append(
            HubspotSyncLogOut(
                id=log.id,
                company_id=log.company_id,
                contact_id=log.contact_id,
                company_name=c_name,
                sync_status=log.sync_status,
                error_message=log.error_message,
                synced_at=log.synced_at,
            )
        )

    return Page(items=items, total=total, page=page, page_size=page_size)
