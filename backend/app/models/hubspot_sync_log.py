from sqlalchemy import Column, ForeignKey, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class HubspotSyncLog(Base):
    __tablename__ = "hubspot_sync_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True)
    sync_status = Column(String(20), nullable=True)  # SUCCESS, FAILED, SKIPPED_DUPLICATE
    error_message = Column(Text, nullable=True)
    synced_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
