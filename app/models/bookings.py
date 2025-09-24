import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class BookingStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    completed = "completed"
    canceled = "canceled"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey(
        "users.id", ondelete="SET NULL"))
    provider_id = Column(UUID(as_uuid=True), ForeignKey(
        "users.id", ondelete="SET NULL"))
    service_id = Column(UUID(as_uuid=True), ForeignKey(
        "services.id", ondelete="SET NULL"))
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    platform_fee = Column(Numeric(10, 2), default=0)
    status = Column(Enum(BookingStatus), default=BookingStatus.pending)
    tip = Column(Numeric(10, 2))
    cancellation_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    client = relationship("User", foreign_keys=[
                          client_id], back_populates="bookings_as_client")
    provider = relationship(
        "User",
        foreign_keys=[provider_id],
        back_populates="bookings_as_provider")
    service = relationship("Service")
