from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.models.audit_log import AuditLog
from app.routers.auth import get_current_user
from app.schemas.company import CompanyListResponse, CompanyRead, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=CompanyListResponse)
def list_companies(
    status: Optional[str] = None,
    industry: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base_query = db.query(Company)

    if status:
        base_query = base_query.filter(Company.status == status)
    
    if industry:
        base_query = base_query.filter(Company.industry == industry)
        
    if search:
        search_term = f"%{search}%"
        base_query = base_query.filter(
            or_(
                Company.name.ilike(search_term),
                Company.website.ilike(search_term),
                Company.city.ilike(search_term)
            )
        )

    total = base_query.count()
    items = (
        base_query.order_by(Company.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    return CompanyListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: UUID,
    payload: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Company not found")

    allowed_statuses = {"CONTACTED", "QUALIFIED", "CUSTOMER"}
    pipeline_statuses = {"RAW", "CLEANED", "ENRICHED", "READY", "HUBSPOT"}

    new_status = payload.status.upper()

    if new_status in pipeline_statuses:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 
            detail=f"Cannot manually set status to {new_status}. This is a pipeline-owned status."
        )
        
    if new_status not in allowed_statuses:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status {new_status}. Allowed manual statuses are: {', '.join(allowed_statuses)}"
        )

    old_status = company.status
    company.status = new_status
    if old_status != new_status:
        db.add(AuditLog(
            entity_type="company",
            entity_id=str(company.id),
            field="status",
            old_value=old_status,
            new_value=new_status,
            changed_by=current_user.email
        ))
        
    db.commit()
    db.refresh(company)

    return company
