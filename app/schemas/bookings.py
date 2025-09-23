from pydantic import BaseModel
from typing import Optional
import uuid
from enum import Enum
from datetime import datetime

# --- Enums ---
class BookingStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    completed = "completed"
    canceled = "canceled"


# --- Base ---
class BookingBase(BaseModel):
    start_date: datetime
    end_date: datetime
    total_amount: float
    platform_fee: Optional[float] = 0.0
    tip: Optional[float] = None
    cancellation_reason: Optional[str] = None
    status: BookingStatus = BookingStatus.pending


# --- Create ---
class BookingCreate(BookingBase):
    client_id: uuid.UUID
    provider_id: uuid.UUID
    service_id: uuid.UUID


# --- Response ---
class BookingResponse(BookingBase):
    id: uuid.UUID
    client_id: uuid.UUID
    provider_id: uuid.UUID
    service_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
