from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pagination import Page


class CampaignCreate(BaseModel):
    """Base creation fields. Router-level fields (e.g. triggering the n8n
    webhook) get added when the campaigns router is built."""

    name: str = Field(..., max_length=200)
    industry: str = Field(..., max_length=120)
    country: Optional[str] = Field(default=None, max_length=80)
    state: Optional[str] = Field(default=None, max_length=80)
    max_leads: int = Field(..., gt=0)


class CampaignRead(BaseModel):
    """Base read shape. Extend with computed/aggregate fields later as
    needed (e.g. company counts)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    industry: str
    country: Optional[str] = None
    state: Optional[str] = None
    max_leads: int
    status: str  # PENDING, SCRAPING, ENRICHING, SYNCING, COMPLETED, FAILED
    total_scraped: int
    total_enriched: int
    total_imported: int
    created_by: Optional[UUID] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class CampaignListResponse(Page[CampaignRead]):
    """Paginated response for GET /campaigns."""

class CampaignDetailRead(CampaignRead):
    """Detailed read shape for a single campaign, including status breakdown."""
    status_breakdown: dict[str, int]
