from sqlalchemy import Column, ForeignKey, Index, String, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (Index("idx_contacts_company", "company_id"),)

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    position = Column(String(150), nullable=True)
    email = Column(String(255), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    apollo_source_id = Column(String(100), nullable=True)
    verification_status = Column(String(20), nullable=True)  # verified, guessed, unknown
    hubspot_contact_id = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
