from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name = Column(String(200), nullable=False)
    industry = Column(String(120), nullable=False)
    country = Column(String(80), nullable=True)
    state = Column(String(80), nullable=True)
    max_leads = Column(Integer, nullable=False)
    # PENDING, SCRAPING, ENRICHING, SYNCING, COMPLETED, FAILED
    status = Column(String(20), server_default="PENDING")
    total_scraped = Column(Integer, server_default="0")
    total_enriched = Column(Integer, server_default="0")
    total_imported = Column(Integer, server_default="0")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
