from pydantic import BaseModel
from typing import Optional, List
import uuid
from enum import Enum


# Enum for provider verification
class VerificationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


# Provider base
class ProviderBase(BaseModel):
    verification_status: VerificationStatus = VerificationStatus.pending


# Provider details
class ProviderResponse(ProviderBase):
    user_id: uuid.UUID
    id_uploads: List[str] = []
    background_check_result: Optional[dict]

    class Config:
        orm_mode = True


# Certification schema
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
