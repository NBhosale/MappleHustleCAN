import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RefreshTokenBase(BaseModel):
    token: str
    revoked: bool = False
    expires_at: datetime


class RefreshTokenCreate(RefreshTokenBase):
    user_id: uuid.UUID


class RefreshTokenResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    revoked: bool
    expires_at: datetime
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
