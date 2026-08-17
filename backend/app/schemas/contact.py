from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ContactRead(BaseModel):
    """Base read shape for a contact. Like companies, contacts are only
    created via the internal bulk-ingest endpoint — no Create schema here
    yet, added when routers/internal.py is built."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: Optional[UUID] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    apollo_source_id: Optional[str] = None
    verification_status: Optional[str] = None  # verified, guessed, unknown
    hubspot_contact_id: Optional[str] = None
    created_at: datetime
