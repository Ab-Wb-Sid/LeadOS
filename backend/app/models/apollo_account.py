from sqlalchemy import Column, Date, Numeric, String, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class ApolloAccount(Base):
    __tablename__ = "apollo_accounts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name = Column(String(120), nullable=False)
    api_key = Column(String(255), nullable=False)
    remaining_credits = Column(Numeric(10, 2), server_default="0")
    status = Column(String(20), server_default="ACTIVE")
    reset_date = Column(Date, nullable=True)
    last_used_at = Column(TIMESTAMP(timezone=True), nullable=True)
