from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.apify_account import ApifyAccount
from app.models.user import User
from app.models.audit_log import AuditLog
from app.routers.auth import get_current_user, require_admin
from app.schemas.apify_account import (
    ApifyAccountCreate,
    ApifyAccountRead,
    ApifyAccountUpdate,
)
from app.services.encryption import encrypt

router = APIRouter(
    prefix="/apify-accounts",
    tags=["Apify Accounts"],
    dependencies=[Depends(require_admin)],
)

@router.get("", response_model=list[ApifyAccountRead])
def list_apify_accounts(db: Session = Depends(get_db)):
    """List all Apify accounts. api_key is masked by the response model."""
    return db.query(ApifyAccount).all()

@router.post("", response_model=ApifyAccountRead, status_code=status.HTTP_201_CREATED)
def create_apify_account(account_in: ApifyAccountCreate, db: Session = Depends(get_db)):
    """Create a new Apify account. Encrypts the api_key before storing."""
    db_obj = ApifyAccount(
        name=account_in.name,
        api_key=encrypt(account_in.api_key),
        remaining_credits=account_in.remaining_credits,
        status=account_in.status,
        reset_date=account_in.reset_date,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.patch("/{id}", response_model=ApifyAccountRead)
def update_apify_account(
    id: UUID, 
    account_in: ApifyAccountUpdate, 
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update an Apify account. Re-encrypts the api_key if a new one is provided."""
    db_obj = db.query(ApifyAccount).filter(ApifyAccount.id == id).first()
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Apify account not found"
        )

    update_data = account_in.model_dump(exclude_unset=True)
    if "api_key" in update_data:
        update_data["api_key"] = encrypt(update_data["api_key"])

    for field, value in update_data.items():
        old_value = getattr(db_obj, field)
        if str(old_value) != str(value):
            setattr(db_obj, field, value)
            if field in ("remaining_credits", "status"):
                db.add(AuditLog(
                    entity_type="apify_account",
                    entity_id=str(db_obj.id),
                    field=field,
                    old_value=str(old_value) if old_value is not None else None,
                    new_value=str(value) if value is not None else None,
                    changed_by=current_user.email
                ))

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
