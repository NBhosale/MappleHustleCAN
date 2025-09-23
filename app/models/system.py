import uuid
import enum
from sqlalchemy import Column, String, Enum, DateTime, ForeignKey, Integer, Numeric, JSON, Interval
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base_class import Base


# Enum for system event severity
class SeverityLevel(enum.Enum):
    info = "info"
    warning = "warning"
    error = "error"


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String, nullable=False)   # Store hashed JWT token
    expires = Column(DateTime(timezone=True), nullable=False)
    context = Column(JSON, default={})            # e.g., {"ip": "1.2.3.4", "user_agent": "Chrome"}
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SystemEvent(Base):
    __tablename__ = "system_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    event_type = Column(String, nullable=False)   # e.g., login_failed, booking_created
    severity = Column(Enum(SeverityLevel), default=SeverityLevel.info)
    event_data = Column(JSON, default={})         # Flexible event payload
    context = Column(JSON, default={})            # e.g., {"ip": "1.2.3.4"}
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TaxRule(Base):
    __tablename__ = "tax_rules"

    province_code = Column(String(2), ForeignKey("canadian_provinces.code", ondelete="CASCADE"), primary_key=True)
    effective_date = Column(DateTime(timezone=True), primary_key=True, nullable=False, server_default=func.now())
    gst = Column(Numeric(5, 2), default=0)
    pst = Column(Numeric(5, 2), default=0)
    hst = Column(Numeric(5, 2), default=0)


class ProviderMetric(Base):
    __tablename__ = "provider_metrics"

    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    response_rate = Column(Numeric(5, 2), default=100)
    avg_response_time = Column(Interval)
    repeat_clients = Column(Integer, default=0)
    completed_bookings = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
