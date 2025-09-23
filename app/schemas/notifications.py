import datetime
from pydantic import BaseModel
from typing import Optional, Dict
import uuid
from enum import Enum
from datetime import datetime


# --- Enums ---
class NotificationType(str, Enum):
    booking_request = "booking_request"
    booking_accepted = "booking_accepted"
    booking_completed = "booking_completed"
    message_received = "message_received"
    payment_released = "payment_released"


class NotificationStatus(str, Enum):
    unread = "unread"
    read = "read"


class NotificationChannel(str, Enum):
    in_app = "in_app"
    email = "email"
    sms = "sms"


# --- Notifications ---
class NotificationBase(BaseModel):
    type: NotificationType
    content: str
    status: NotificationStatus = NotificationStatus.unread
    channel: NotificationChannel = NotificationChannel.in_app


class NotificationCreate(NotificationBase):
    user_id: uuid.UUID


class NotificationResponse(NotificationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    sent_at: Optional[datetime]
    delivered: bool

    class Config:
        orm_mode = True


# --- Preferences ---
class UserNotificationPreferenceBase(BaseModel):
    notify_on_new_message: bool = True
    notify_on_booking_update: bool = True
    notify_on_payment: bool = False
    notify_on_review_reminder: bool = False
    notify_by_sms: bool = False
    notify_by_email: bool = True


class UserNotificationPreferenceUpdate(UserNotificationPreferenceBase):
    pass


class UserNotificationPreferenceResponse(UserNotificationPreferenceBase):
    user_id: uuid.UUID
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


# --- Notification Logs ---
class NotificationLogResponse(BaseModel):
    id: uuid.UUID
    notification_id: uuid.UUID
    channel: NotificationChannel
    status: str
    response: Optional[Dict]
    created_at: Optional[datetime]

    class Config:
        orm_mode = True
