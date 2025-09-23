import uuid
import enum
from sqlalchemy import Column, String, Boolean, Enum, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, CITEXT
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


# Enums (mirror Postgres enums)
class UserRole(enum.Enum):
    client = "client"
    provider = "provider"
    admin = "admin"

class UserStatus(enum.Enum):
    active = "active"
    suspended = "suspended"
    deleted = "deleted"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(CITEXT, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    name = Column(String, nullable=False)
    phone_number = Column(String)
    is_phone_verified = Column(Boolean, default=False)
    address = Column(String)
    city = Column(String)
    postal_code = Column(String)
    province_code = Column(String(2), ForeignKey("canadian_provinces.code"))
    status = Column(Enum(UserStatus), default=UserStatus.active)
    is_email_verified = Column(Boolean, default=False)

    last_login_at = Column(DateTime(timezone=True))
    password_reset_token = Column(UUID(as_uuid=True))
    password_reset_expires = Column(DateTime(timezone=True))
    verification_token = Column(UUID(as_uuid=True))
    verification_expires = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    provider = relationship("Provider", back_populates="user", uselist=False)
    certifications = relationship("ProviderCertification", back_populates="provider")
    services = relationship("Service", back_populates="provider")
    bookings_as_client = relationship("Booking", foreign_keys="Booking.client_id")
    bookings_as_provider = relationship("Booking", foreign_keys="Booking.provider_id")
