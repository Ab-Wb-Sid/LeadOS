from sqlalchemy import Column, ForeignKey, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Job(Base):
    """Tracks each async step tied to a campaign — the 'queue log' since
    n8n replaces Celery/Redis as the task runner."""

    __tablename__ = "jobs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=True)
    job_type = Column(String(30), nullable=False)  # SCRAPE, ENRICH, SYNC
    status = Column(String(20), server_default="PENDING")  # PENDING, RUNNING, SUCCESS, FAILED
    error_message = Column(Text, nullable=True)
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    finished_at = Column(TIMESTAMP(timezone=True), nullable=True)
