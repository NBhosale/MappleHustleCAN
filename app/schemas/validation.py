"""
Pydantic validation schemas for business rules
"""
from pydantic import BaseModel, validator, Field
from typing import Optional
from datetime import date, time
import re


class AvailabilityValidation(BaseModel):
    """Validation schema for availability creation"""
    date: date
    start_time: time
    end_time: time
    recurrence_rule: Optional[str] = None

    @validator('end_time')
    def validate_time_slot(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

    @validator('recurrence_rule')
    def validate_recurrence_rule(cls, v):
        if v and not v.startswith('FREQ='):
            raise ValueError('Recurrence rule must start with FREQ=')
        return v


class BookingValidation(BaseModel):
    """Validation schema for booking creation"""
    start_date: date
    start_time: time
    end_time: time
    service_id: str

    @validator('end_time')
    def validate_time_slot(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

    @validator('start_date')
    def validate_advance_notice(cls, v):
        from datetime import datetime, timedelta
        booking_datetime = datetime.combine(v, time.min)
        now = datetime.now()
        
        if booking_datetime - now < timedelta(hours=2):
            raise ValueError('Bookings must be made at least 2 hours in advance')
        
        if booking_datetime - now > timedelta(days=180):
            raise ValueError('Bookings cannot be made more than 6 months in advance')
        
        return v


class UserLocationValidation(BaseModel):
    """Validation schema for user location data"""
    province_code: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None

    @validator('province_code')
    def validate_province_code(cls, v):
        if v:
            v = v.upper()
            valid_provinces = {
                'AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 
                'ON', 'PE', 'QC', 'SK', 'YT'
            }
            if v not in valid_provinces:
                raise ValueError(f'Invalid Canadian province code: {v}')
        return v

    @validator('postal_code')
    def validate_postal_code(cls, v):
        if v:
            # Remove spaces and convert to uppercase
            v = v.replace(" ", "").upper()
            # Canadian postal code pattern: A1A 1A1
            pattern = r"^[A-Z]\d[A-Z]\d[A-Z]\d$"
            if not re.match(pattern, v):
                raise ValueError('Invalid Canadian postal code format. Expected: A1A 1A1')
        return v


class ItemInventoryValidation(BaseModel):
    """Validation schema for item inventory management"""
    item_id: str
    quantity: int = Field(gt=0, description="Quantity must be positive")

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        if v > 1000:
            raise ValueError('Quantity cannot exceed 1000')
        return v


class ServiceRateValidation(BaseModel):
    """Validation schema for service rate validation"""
    hourly_rate: Optional[float] = None
    daily_rate: Optional[float] = None

    @validator('hourly_rate')
    def validate_hourly_rate(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError('Hourly rate cannot be negative')
            if v > 1000:
                raise ValueError('Hourly rate cannot exceed $1000/hour')
        return v

    @validator('daily_rate')
    def validate_daily_rate(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError('Daily rate cannot be negative')
            if v > 5000:
                raise ValueError('Daily rate cannot exceed $5000/day')
        return v

    @validator('daily_rate')
    def validate_rate_consistency(cls, v, values):
        if v is not None and 'hourly_rate' in values and values['hourly_rate'] is not None:
            hourly = values['hourly_rate']
            # Daily rate should be reasonable compared to hourly (4-12 hours)
            if v < hourly * 4:
                raise ValueError('Daily rate seems too low compared to hourly rate')
            if v > hourly * 12:
                raise ValueError('Daily rate seems too high compared to hourly rate')
        return v


class PaymentAmountValidation(BaseModel):
    """Validation schema for payment amounts"""
    amount: float = Field(gt=0, description="Amount must be positive")

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Payment amount must be positive')
        if v > 100000:
            raise ValueError('Payment amount cannot exceed $100,000')
        return v


class MessageContentValidation(BaseModel):
    """Validation schema for message content"""
    content: str = Field(min_length=1, max_length=5000, description="Message content length")

    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Message content cannot be empty')
        
        # Check for spam-like content (basic check)
        spam_indicators = ['spam', 'scam', 'free money', 'click here']
        if any(indicator in v.lower() for indicator in spam_indicators):
            raise ValueError('Message content appears to be spam')
        
        return v.strip()


class ReviewValidation(BaseModel):
    """Validation schema for review submission"""
    rating: int = Field(ge=1, le=5, description="Rating must be between 1 and 5")
    comment: Optional[str] = Field(None, max_length=1000, description="Review comment")

    @validator('comment')
    def validate_comment(cls, v):
        if v and len(v.strip()) < 10:
            raise ValueError('Review comment must be at least 10 characters')
        return v.strip() if v else v
