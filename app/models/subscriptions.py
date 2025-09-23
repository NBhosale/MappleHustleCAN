import uuid
import enum
from sqlalchemy import Column, String, Enum, DateTime, ForeignKey, Integer, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base_class import Base


# Enum for subscription plans
class SubscriptionPlan(enum.Enum):
    free = "free"
    basic = "basic"
    premium = "premium"
    enterprise = "enterprise"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan = Column(Enum(SubscriptionPlan), nullable=False)
    billing_cycle = Column(String, default="monthly")  # monthly | yearly
    features = Column(JSON, default={})  # Feature flags: {"featured_listings": true}
    stripe_subscription_id = Column(String, unique=True)
    status = Column(String, default="active")  # active | canceled | expired
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ends_at = Column(DateTime(timezone=True))


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referrer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    referred_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    code = Column(String(50), unique=True, nullable=False)
    redeemed = Column(Integer, default=0)  # 0 = not redeemed, 1 = redeemed
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LoyaltyPoint(Base):
    __tablename__ = "loyalty_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    points = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
