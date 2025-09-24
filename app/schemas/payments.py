import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class PaymentStatus(str, Enum):
    pending = "pending"
    held = "held"
    released = "released"
    refunded = "refunded"


class RefundBase(BaseModel):
    amount: float
    reason: Optional[str]


class RefundCreate(RefundBase):
    payment_id: uuid.UUID
    stripe_refund_id: Optional[str]


class RefundResponse(RefundBase):
    id: uuid.UUID
    payment_id: uuid.UUID
    stripe_refund_id: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class PaymentBase(BaseModel):
    amount: float
    currency: str = "CAD"
    status: PaymentStatus = PaymentStatus.pending


class PaymentCreate(PaymentBase):
    booking_id: Optional[uuid.UUID]
    order_id: Optional[uuid.UUID]
    stripe_transaction_id: str


class PaymentResponse(PaymentBase):
    id: uuid.UUID
    booking_id: Optional[uuid.UUID]
    order_id: Optional[uuid.UUID]
    stripe_transaction_id: str
    refund_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
