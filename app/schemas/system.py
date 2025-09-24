import uuid
from datetime import date, datetime
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel


# --- Enums ---
class SeverityLevel(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"


# --- Sessions ---
class SessionBase(BaseModel):
    token_hash: str
    expires: datetime
    context: Dict = {}


class SessionCreate(SessionBase):
    user_id: uuid.UUID


class SessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    expires: datetime
    context: Dict = {}
    created_at: datetime

    class Config:
        orm_mode = True


# --- System Events ---
class SystemEventBase(BaseModel):
    event_type: str
    severity: SeverityLevel = SeverityLevel.info
    event_data: Dict = {}
    context: Dict = {}


class SystemEventCreate(SystemEventBase):
    user_id: Optional[uuid.UUID]


class SystemEventResponse(SystemEventBase):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    created_at: datetime

    class Config:
        orm_mode = True


# --- Tax Rules ---
class TaxRuleBase(BaseModel):
    gst: float = 0.0
    pst: float = 0.0
    hst: float = 0.0


class TaxRuleCreate(TaxRuleBase):
    province_code: str
    effective_date: Optional[date]


class TaxRuleResponse(TaxRuleBase):
    province_code: str
    effective_date: date

    class Config:
        orm_mode = True


# --- Provider Metrics ---
class ProviderMetricBase(BaseModel):
    response_rate: float = 100.0
    repeat_clients: int = 0
    completed_bookings: int = 0


class ProviderMetricCreate(ProviderMetricBase):
    provider_id: uuid.UUID


class ProviderMetricResponse(ProviderMetricBase):
    provider_id: uuid.UUID
    avg_response_time: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
