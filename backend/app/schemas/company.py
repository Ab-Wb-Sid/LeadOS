from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CompanyRead(BaseModel):
    """Base read shape for a company. No Create schema yet — companies
    are only ever created via the internal bulk-ingest endpoint, which
    gets its own schema when routers/internal.py is built."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    campaign_id: Optional[UUID] = None
    name: str
    website: Optional[str] = None
    normalized_domain: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    source: Optional[str] = None
    google_rating: Optional[Decimal] = None
    review_count: Optional[int] = None
    lead_score: int
    status: str  # RAW, CLEANED, ENRICHED, READY, HUBSPOT, CONTACTED, QUALIFIED, CUSTOMER
    hubspot_company_id: Optional[str] = None
    created_at: datetime
