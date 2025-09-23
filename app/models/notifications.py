import uuid
import enum
from sqlalchemy import Column, String, Text, Enum, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


# Enums (match DB enum types)
class NotificationType(enum.Enum):
    booking_request = "booking_request"
    booking_accepted = "booking_accepted"
    booking_completed = "booking_completed"
    message_received = "message_received"
    payment_released = "payment_released"


class NotificationStatus(enum.Enum):
    unread = "unread"
    read = "read"


class NotificationChannel(enum.Enum):
    in_app = "in_app"
    email = "email"
    sms = "sms"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.unread)
    channel = Column(Enum(NotificationChannel), default=NotificationChannel.in_app)
    sent_at = Column(DateTime(timezone=True))
    delivered = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    logs = relationship("NotificationLog", back_populates="notification")


class UserNotificationPreference(Base):
    __tablename__ = "user_notification_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    notify_on_new_message = Column(Boolean, default=True)
    notify_on_booking_update = Column(Boolean, default=True)
    notify_on_payment = Column(Boolean, default=False)
    notify_on_review_reminder = Column(Boolean, default=False)
    notify_by_sms = Column(Boolean, default=False)
    notify_by_email = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_id = Column(UUID(as_uuid=True), ForeignKey("notifications.id", ondelete="CASCADE"))
    channel = Column(Enum(NotificationChannel), nullable=False)
    status = Column(String, nullable=False)   # pending, sent, failed, delivered
    provider_response = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    notification = relationship("Notification", back_populates="logs")
