import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class PaymentStatus(enum.Enum):
    pending = "pending"
    held = "held"
    released = "released"
    refunded = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey(
        "bookings.id", ondelete="SET NULL"))
    order_id = Column(UUID(as_uuid=True), ForeignKey(
        "orders.id", ondelete="SET NULL"))
    stripe_transaction_id = Column(String, nullable=False)   # Stripe charge ID
    # Removed refund_id to avoid circular dependency - use refund.payment_id
    # instead
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="CAD")
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    refunds = relationship(
        "Refund", back_populates="payment", cascade="all, delete-orphan")


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey(
        "payments.id", ondelete="CASCADE"))
    # Stripe refund reference
    stripe_refund_id = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    payment = relationship("Payment", back_populates="refunds")
