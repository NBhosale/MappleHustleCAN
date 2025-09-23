import uuid
import enum
from sqlalchemy import Column, String, Enum, DateTime, ForeignKey, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class OrderStatus(enum.Enum):
    pending = "pending"
    paid = "paid"
    shipped = "shipped"
    delivered = "delivered"
    canceled = "canceled"
    refunded = "refunded"


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    total_amount = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0)
    platform_fee = Column(Numeric(10, 2), default=0)
    status = Column(Enum(OrderStatus), default=OrderStatus.pending)
    tracking_number = Column(String)
    shipped_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    items = relationship("OrderItem", back_populates="order")
    shipments = relationship("OrderShipment", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"))
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="SET NULL"))
    quantity = Column(Integer, default=1)
    price = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")


class OrderShipment(Base):
    __tablename__ = "order_shipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"))
    carrier = Column(String)  # e.g., Canada Post, UPS
    tracking_number = Column(String)
    shipped_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))

    order = relationship("Order", back_populates="shipments")
