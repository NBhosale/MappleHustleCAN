from pydantic import BaseModel
from typing import Optional, List
import uuid
from enum import Enum


# --- Existing Provider/Certification Enums & Schemas (already in your file) ---
class VerificationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ProviderBase(BaseModel):
    verification_status: VerificationStatus = VerificationStatus.pending


class ProviderResponse(ProviderBase):
    user_id: uuid.UUID
    id_uploads: List[str] = []
    background_check_result: Optional[dict]

    class Config:
        orm_mode = True


class ProviderCertificationBase(BaseModel):
    title: str
    issuer: Optional[str]
    issue_date: Optional[str]
    expiry_date: Optional[str]
    document_path: Optional[str]


class ProviderCertificationCreate(ProviderCertificationBase):
    pass


class ProviderCertificationResponse(ProviderCertificationBase):
    id: uuid.UUID
    provider_id: uuid.UUID
    verified: bool

    class Config:
        orm_mode = True


# --- Service-related Enums ---
class ServiceType(str, Enum):
    dog_sitting = "dog_sitting"
    dog_walking = "dog_walking"
    house_sitting = "house_sitting"
    lawn_maintenance = "lawn_maintenance"
    house_cleaning = "house_cleaning"
    errands = "errands"


class AvailabilityStatus(str, Enum):
    available = "available"
    booked = "booked"


# --- Portfolio Schemas ---
class PortfolioBase(BaseModel):
    title: str
    description: Optional[str]
    images: List[str] = []


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioResponse(PortfolioBase):
    id: uuid.UUID
    provider_id: uuid.UUID

    class Config:
        orm_mode = True


# --- Service Schemas ---
class ServiceBase(BaseModel):
    type: ServiceType
    title: Optional[str]
    description: Optional[str]
    terms: Optional[str]
    hourly_rate: Optional[float]
    daily_rate: Optional[float]
    is_featured: bool = False


class ServiceCreate(ServiceBase):
    pass


class ServiceResponse(ServiceBase):
    id: uuid.UUID
    provider_id: uuid.UUID

    class Config:
        orm_mode = True


# --- Availability Schemas ---
class AvailabilityBase(BaseModel):
    date: str  # ISO date string
    start_time: str  # "HH:MM:SS"
    end_time: str
    status: AvailabilityStatus = AvailabilityStatus.available
    recurrence_rule: Optional[str]


class AvailabilityCreate(AvailabilityBase):
    pass


class AvailabilityResponse(AvailabilityBase):
    id: uuid.UUID
    provider_id: uuid.UUID

    class Config:
        orm_mode = True