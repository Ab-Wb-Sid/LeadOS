from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.apollo_account import ApolloAccount
from app.routers.auth import get_current_user
from app.schemas.apollo_account import (
    ApolloAccountCreate,
    ApolloAccountRead,
    ApolloAccountUpdate,
)
from app.services.encryption import encrypt

router = APIRouter(
    prefix="/apollo-accounts",
    tags=["Apollo Accounts"],
    dependencies=[Depends(get_current_user)],
)

@router.get("", response_model=list[ApolloAccountRead])
def list_apollo_accounts(db: Session = Depends(get_db)):
    """List all Apollo accounts. api_key is masked by the response model."""
    return db.query(ApolloAccount).all()

@router.post("", response_model=ApolloAccountRead, status_code=status.HTTP_201_CREATED)
def create_apollo_account(account_in: ApolloAccountCreate, db: Session = Depends(get_db)):
    """Create a new Apollo account. Encrypts the api_key before storing."""
    db_obj = ApolloAccount(
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

@router.patch("/{id}", response_model=ApolloAccountRead)
def update_apollo_account(
    id: UUID, account_in: ApolloAccountUpdate, db: Session = Depends(get_db)
):
    """Update an Apollo account. Re-encrypts the api_key if a new one is provided."""
    db_obj = db.query(ApolloAccount).filter(ApolloAccount.id == id).first()
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Apollo account not found"
        )

    update_data = account_in.model_dump(exclude_unset=True)
    if "api_key" in update_data:
        update_data["api_key"] = encrypt(update_data["api_key"])

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
