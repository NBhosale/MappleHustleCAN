import uuid
import enum
from sqlalchemy import Column, String, Text, Boolean, Enum, DateTime, ForeignKey, Numeric, Date, Time
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
#from app.models.enums import AvailabilityStatus



class ServiceType(enum.Enum):
    dog_sitting = "dog_sitting"
    dog_walking = "dog_walking"
    house_sitting = "house_sitting"
    lawn_maintenance = "lawn_maintenance"
    house_cleaning = "house_cleaning"
    errands = "errands"


class AvailabilityStatus(enum.Enum):
    available = "available"
    booked = "booked"


class Portfolio(Base):
    __tablename__ = "portfolio"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String, nullable=False)
    description = Column(Text)
    images = Column(JSONB, default=list)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    provider = relationship("User")


class Service(Base):
    __tablename__ = "services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    type = Column(Enum(ServiceType), nullable=False)
    title = Column(String)
    description = Column(Text)
    terms = Column(Text)
    hourly_rate = Column(Numeric(10, 2))
    daily_rate = Column(Numeric(10, 2))
    is_featured = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    provider = relationship("User", back_populates="services")


class ServiceTag(Base):
    __tablename__ = "service_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"))
    tag = Column(String, nullable=False)


class Availability(Base):
    __tablename__ = "availability"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # ✅ Split fields instead of TSRANGE
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    status = Column(Enum(AvailabilityStatus), default=AvailabilityStatus.available, nullable=False)
    recurrence_rule = Column(String, nullable=True)  # e.g., "FREQ=WEEKLY;BYDAY=MO"

    def __repr__(self):
        return f"<Availability(provider_id={self.provider_id}, date={self.date}, start={self.start_time}, end={self.end_time}, status={self.status})>"
