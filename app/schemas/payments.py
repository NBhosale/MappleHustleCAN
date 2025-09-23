from pydantic import BaseModel
from typing import Optional
import uuid
from enum import Enum


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

    class Config:
        orm_mode = True
