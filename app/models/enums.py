"""
Enums for the MapleHustle application
"""
from enum import Enum


class UserRole(str, Enum):
    """User roles in the system"""
    client = "client"
    provider = "provider"
    admin = "admin"


class UserStatus(str, Enum):
    """User account status"""
    active = "active"
    inactive = "inactive"
    suspended = "suspended"
    pending_verification = "pending_verification"


class ContactMethod(str, Enum):
    """Preferred contact methods"""
    email = "email"
    phone = "phone"
    sms = "sms"
    in_app = "in_app"


class ServiceStatus(str, Enum):
    """Service status"""
    active = "active"
    inactive = "inactive"
    pending_approval = "pending_approval"
    rejected = "rejected"


class BookingStatus(str, Enum):
    """Booking status"""
    pending = "pending"
    confirmed = "confirmed"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"


class OrderStatus(str, Enum):
    """Order status"""
    pending = "pending"
    confirmed = "confirmed"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"
    returned = "returned"


class PaymentStatus(str, Enum):
    """Payment status"""
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"
    cancelled = "cancelled"


class PaymentMethod(str, Enum):
    """Payment methods"""
    credit_card = "credit_card"
    debit_card = "debit_card"
    paypal = "paypal"
    apple_pay = "apple_pay"
    google_pay = "google_pay"
    bank_transfer = "bank_transfer"
    cash = "cash"


class NotificationType(str, Enum):
    """Notification types"""
    booking_confirmation = "booking_confirmation"
    booking_reminder = "booking_reminder"
    booking_cancellation = "booking_cancellation"
    payment_confirmation = "payment_confirmation"
    service_approval = "service_approval"
    service_rejection = "service_rejection"
    general = "general"


class MessageType(str, Enum):
    """Message types"""
    text = "text"
    image = "image"
    file = "file"
    system = "system"


class ReviewRating(int, Enum):
    """Review rating scale"""
    one = 1
    two = 2
    three = 3
    four = 4
    five = 5


class SubscriptionStatus(str, Enum):
    """Subscription status"""
    active = "active"
    inactive = "inactive"
    cancelled = "cancelled"
    expired = "expired"
    pending = "pending"


class SubscriptionPlan(str, Enum):
    """Subscription plans"""
    basic = "basic"
    premium = "premium"
    enterprise = "enterprise"


class ItemStatus(str, Enum):
    """Item status"""
    available = "available"
    sold = "sold"
    reserved = "reserved"
    unavailable = "unavailable"


class ItemCondition(str, Enum):
    """Item condition"""
    new = "new"
    like_new = "like_new"
    good = "good"
    fair = "fair"
    poor = "poor"
