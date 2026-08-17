from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    TIMESTAMP,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("normalized_domain", name="companies_normalized_domain_key"),
        Index("idx_companies_status", "status"),
        Index("idx_companies_campaign", "campaign_id"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=True)
    name = Column(String(255), nullable=False)
    website = Column(String(255), nullable=True)
    # used for deduplication — global UNIQUE constraint across all campaigns
    normalized_domain = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(255), nullable=True)
    city = Column(String(120), nullable=True)
    state = Column(String(120), nullable=True)
    country = Column(String(120), nullable=True)
    industry = Column(String(120), nullable=True)
    source = Column(String(50), nullable=True)  # 'apify'
    google_rating = Column(Numeric(2, 1), nullable=True)
    review_count = Column(Integer, nullable=True)
    lead_score = Column(Integer, server_default="0")
    # RAW, CLEANED, ENRICHED, READY, HUBSPOT, CONTACTED, QUALIFIED, CUSTOMER
    status = Column(String(20), server_default="RAW")
    hubspot_company_id = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
