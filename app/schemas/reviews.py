import datetime
import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel


# --- Enums ---
class ReviewDirection(str, Enum):
    client_to_provider = "client_to_provider"
    provider_to_client = "provider_to_client"


# --- Base ---
class ReviewBase(BaseModel):
    rating: int
    comment: Optional[str]
    direction: ReviewDirection


# --- Create ---
class ReviewCreate(ReviewBase):
    booking_id: uuid.UUID
    reviewer_id: uuid.UUID
    reviewed_id: uuid.UUID


# --- Response ---
class ReviewResponse(ReviewBase):
    id: uuid.UUID
    booking_id: uuid.UUID
    reviewer_id: uuid.UUID
    reviewed_id: uuid.UUID
    approval_status: str
    created_at: datetime

    class Config:
        orm_mode = True
