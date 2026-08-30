from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, UUID4


class BulkSyncRequest(BaseModel):
    company_ids: List[UUID4]


class SyncResultSummary(BaseModel):
    company_id: UUID4
    status: str
    error: Optional[str] = None


class BulkSyncResponse(BaseModel):
    results: List[SyncResultSummary]


class HubspotSyncLogOut(BaseModel):
    id: UUID4
    company_id: Optional[UUID4] = None
    contact_id: Optional[UUID4] = None
    company_name: Optional[str] = None
    sync_status: Optional[str] = None
    error_message: Optional[str] = None
    synced_at: datetime

    class Config:
        from_attributes = True
