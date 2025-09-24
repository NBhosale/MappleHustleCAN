import enum
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class VerificationStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Provider(Base):
    __tablename__ = "providers"

    user_id = Column(UUID(as_uuid=True), ForeignKey(
        "users.id", ondelete="CASCADE"), primary_key=True)
    verification_status = Column(
        Enum(VerificationStatus), default=VerificationStatus.pending)
    id_uploads = Column(JSON, default=list)
    background_check_result = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="provider")


class ProviderCertification(Base):
    __tablename__ = "provider_certifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(UUID(as_uuid=True), ForeignKey(
        "users.id", ondelete="CASCADE"))
    title = Column(String, nullable=False)
    issuer = Column(String)
    issue_date = Column(DateTime)
    expiry_date = Column(DateTime)
    document_path = Column(String)
    verified = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    provider = relationship("User", back_populates="certifications")
