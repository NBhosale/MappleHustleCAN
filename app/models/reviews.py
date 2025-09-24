import enum
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base_class import Base


class ReviewDirection(enum.Enum):
    client_to_provider = "client_to_provider"
    provider_to_client = "provider_to_client"


class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey(
        "bookings.id", ondelete="CASCADE"))
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey(
        "users.id", ondelete="SET NULL"))
    reviewed_id = Column(UUID(as_uuid=True), ForeignKey(
        "users.id", ondelete="SET NULL"))
    direction = Column(Enum(ReviewDirection), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    # pending | approved | rejected
    approval_status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
