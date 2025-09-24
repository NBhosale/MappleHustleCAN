import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator


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
    quantity: int = Field(..., gt=0, le=1000)
    price: float = Field(..., gt=0, le=100000)

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        if v > 1000:
            raise ValueError('Quantity cannot exceed 1000')
        return v

    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        if v > 100000:
            raise ValueError('Price cannot exceed $100,000')
        return v


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
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]


class OrderShipmentCreate(OrderShipmentBase):
    pass


class OrderShipmentResponse(OrderShipmentBase):
    id: uuid.UUID
    order_id: uuid.UUID

    class Config:
        orm_mode = True


# --- Orders ---
class OrderBase(BaseModel):
    total_amount: Decimal = Field(..., gt=0, le=1000000)
    tax_amount: Decimal = Field(..., ge=0, le=100000)
    platform_fee: Optional[Decimal] = Field(None, ge=0, le=10000)
    status: OrderStatus = OrderStatus.pending
    tracking_number: Optional[str] = Field(None, max_length=100)
    shipped_at: Optional[datetime]

    @validator('total_amount')
    def validate_total_amount(cls, v):
        if v <= 0:
            raise ValueError('Total amount must be greater than 0')
        if v > 1000000:
            raise ValueError('Total amount cannot exceed $1,000,000')
        return v

    @validator('tax_amount')
    def validate_tax_amount(cls, v):
        if v < 0:
            raise ValueError('Tax amount cannot be negative')
        if v > 100000:
            raise ValueError('Tax amount cannot exceed $100,000')
        return v

    @validator('platform_fee')
    def validate_platform_fee(cls, v):
        if v is not None and v < 0:
            raise ValueError('Platform fee cannot be negative')
        if v is not None and v > 10000:
            raise ValueError('Platform fee cannot exceed $10,000')
        return v


class OrderCreate(OrderBase):
    client_id: uuid.UUID
    items: List[OrderItemCreate]


class OrderResponse(OrderBase):
    id: uuid.UUID
    client_id: uuid.UUID
    items: List[OrderItemResponse] = []
    shipments: List[OrderShipmentResponse] = []
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]

    class Config:
        orm_mode = True
