import uuid

from sqlalchemy import Column, String, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class User(Base):
    """Internal Sanestix team member (sales/admin) — not a customer."""

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), server_default="sales")  # 'admin' | 'sales'
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
