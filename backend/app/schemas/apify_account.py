from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApifyAccountCreate(BaseModel):
    """Input for registering an Apify account. `api_key` is plaintext
    here — encrypting it at rest (Fernet, per the architecture doc) is
    the service layer's job when this gets wired into a route."""

    name: str = Field(..., max_length=120)
    api_key: str = Field(..., max_length=255)
    remaining_credits: Decimal = Field(default=Decimal("0"))
    status: str = Field(default="ACTIVE", max_length=20)  # ACTIVE, COOLDOWN, DISABLED
    reset_date: Optional[date] = None


class ApifyAccountUpdate(BaseModel):
    """Input for updating an Apify account. Any provided fields will overwrite existing ones."""
    name: Optional[str] = Field(None, max_length=120)
    api_key: Optional[str] = Field(None, max_length=255)
    remaining_credits: Optional[Decimal] = None
    status: Optional[str] = Field(None, max_length=20)
    reset_date: Optional[date] = None


class ApifyAccountRead(BaseModel):
    """Output shape. api_key is always masked to its last 4 characters —
    the full key should never leave the API once stored."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    api_key: str
    remaining_credits: Decimal
    status: str
    reset_date: Optional[date] = None
    last_used_at: Optional[datetime] = None

    @field_validator("api_key", mode="before")
    @classmethod
    def mask_api_key(cls, v: Optional[str]) -> str:
        if not v:
            return "****"
        if len(v) <= 4:
            return "****"
        return f"****{v[-4:]}"
