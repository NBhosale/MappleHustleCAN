from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional, List
import uuid
from enum import Enum


# --- Enums ---
class OrderStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    shipped = "shipped"
    delivered = "delivered"
    canceled = "canceled"
    refunded = "refunded"


# --- Order Items ---
class OrderItemBase(BaseModel):
    item_id: uuid.UUID
    quantity: int
    price: float


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: uuid.UUID
    order_id: uuid.UUID

    class Config:
        orm_mode = True


# --- Shipments ---
class OrderShipmentBase(BaseModel):
    carrier: Optional[str]
    tracking_number: Optional[str]
    shipped_at: Optional[str]
    delivered_at: Optional[str]


class OrderShipmentCreate(OrderShipmentBase):
    pass


class OrderShipmentResponse(OrderShipmentBase):
    id: uuid.UUID
    order_id: uuid.UUID

    class Config:
        orm_mode = True


# --- Orders ---
class OrderBase(BaseModel):
    total_amount: Decimal
    tax_amount: Decimal
    platform_fee: Optional[Decimal]
    status: OrderStatus = OrderStatus.pending
    tracking_number: Optional[str]
    shipped_at: Optional[datetime]


class OrderCreate(OrderBase):
    client_id: uuid.UUID
    items: List[OrderItemCreate]


class OrderResponse(OrderBase):
    id: uuid.UUID
    client_id: uuid.UUID
    items: List[OrderItemResponse] = []
    shipments: List[OrderShipmentResponse] = []

    class Config:
        orm_mode = True
