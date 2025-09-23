from pydantic import BaseModel
from typing import Optional
import uuid
from enum import Enum


# --- Enums ---
class SubscriptionPlan(str, Enum):
    free = "free"
    basic = "basic"
    premium = "premium"
    enterprise = "enterprise"


# --- Subscriptions ---
class SubscriptionBase(BaseModel):
    plan: SubscriptionPlan
    billing_cycle: str = "monthly"  # monthly | yearly
    features: dict = {}
    status: str = "active"          # active | canceled | expired


class SubscriptionCreate(SubscriptionBase):
    provider_id: uuid.UUID


class SubscriptionResponse(SubscriptionBase):
    id: uuid.UUID
    provider_id: uuid.UUID
    stripe_subscription_id: Optional[str]
    started_at: Optional[str]
    ends_at: Optional[str]

    class Config:
        orm_mode = True


# --- Referrals ---
class ReferralBase(BaseModel):
    code: str


class ReferralCreate(ReferralBase):
    referrer_id: uuid.UUID
    referred_id: Optional[uuid.UUID]


class ReferralResponse(ReferralBase):
    id: uuid.UUID
    referrer_id: uuid.UUID
    referred_id: Optional[uuid.UUID]
    redeemed: int
    created_at: str

    class Config:
        orm_mode = True


# --- Loyalty Points ---
class LoyaltyPointBase(BaseModel):
    points: int = 0


class LoyaltyPointCreate(LoyaltyPointBase):
    user_id: uuid.UUID


class LoyaltyPointResponse(LoyaltyPointBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: str

    class Config:
        orm_mode = True
