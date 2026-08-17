from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Input for creating a user. `password` is plaintext here — it gets
    hashed into `password_hash` by the route/service layer, never stored
    or echoed back as-is."""

    name: str = Field(..., max_length=120)
    email: EmailStr = Field(..., max_length=160)
    password: str = Field(..., min_length=8)
    role: str = Field(default="sales", max_length=20)  # 'admin' | 'sales'


class UserRead(BaseModel):
    """Output shape for a user. password_hash is intentionally never
    included here — this is the only representation of a user that
    should ever leave the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    role: str
    created_at: datetime
