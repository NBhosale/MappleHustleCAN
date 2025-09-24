"""
Enhanced validation schemas for MapleHustleCAN
Comprehensive validation rules for all data types
"""

import re
import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class EmailValidation(BaseModel):
    """Enhanced email validation with strong regex"""
    email: EmailStr

    @validator('email')
    def validate_email_strict(cls, v):
        # Strong email regex pattern
        email_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')

        # Check for common disposable email domains
        disposable_domains = [
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email', 'temp-mail.org',
            'guerrillamailblock.com', 'sharklasers.com', 'grr.la'
        ]

        domain = v.split('@')[1].lower()
        if domain in disposable_domains:
            raise ValueError('Disposable email addresses are not allowed')

        # Check for suspicious patterns
        if re.search(r'[.]{2,}', v):  # Multiple consecutive dots
            raise ValueError('Invalid email format')

        if v.startswith('.') or v.endswith('.'):
            raise ValueError('Invalid email format')

        return v.lower()


class PasswordValidation(BaseModel):
    """Enhanced password validation"""
    password: str = Field(..., min_length=8, max_length=128)

    @validator('password')
    def validate_password_strength(cls, v):
        # Check for common passwords
        common_passwords = [
            'password', '123456', 'password123', 'admin', 'qwerty',
            'letmein', 'welcome', 'monkey', '1234567890'
        ]

        if v.lower() in common_passwords:
            raise ValueError(
                'Password is too common, please choose a stronger password')

        # Check for sequential characters
        if re.search(r'(.)\1{2,}', v):
            raise ValueError(
                'Password cannot contain more than 2 consecutive identical characters')

        # Check for keyboard patterns
        keyboard_patterns = [
            'qwerty', 'asdfgh', 'zxcvbn', '123456', 'abcdef'
        ]

        for pattern in keyboard_patterns:
            if pattern in v.lower():
                raise ValueError('Password cannot contain keyboard patterns')

        return v


class PhoneValidation(BaseModel):
    """Canadian phone number validation"""
    phone: str = Field(..., min_length=10, max_length=15)

    @validator('phone')
    def validate_canadian_phone(cls, v):
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', v)

        # Check if it's a valid Canadian phone number
        if len(digits) == 10:
            # Format: NXX-NXX-XXXX
            if not re.match(r'^[2-9]\d{2}[2-9]\d{2}\d{4}$', digits):
                raise ValueError('Invalid Canadian phone number format')
        elif len(digits) == 11 and digits.startswith('1'):
            # Format: 1-NXX-NXX-XXXX
            if not re.match(r'^1[2-9]\d{2}[2-9]\d{2}\d{4}$', digits):
                raise ValueError('Invalid Canadian phone number format')
        else:
            raise ValueError('Phone number must be 10 or 11 digits')

        return v


class PostalCodeValidation(BaseModel):
    """Canadian postal code validation"""
    postal_code: str = Field(..., min_length=6, max_length=7)

    @validator('postal_code')
    def validate_canadian_postal_code(cls, v):
        # Remove spaces and convert to uppercase
        code = v.replace(' ', '').upper()

        # Canadian postal code format: A1A 1A1
        if not re.match(r'^[A-Z]\d[A-Z]\d[A-Z]\d$', code):
            raise ValueError('Invalid Canadian postal code format')

        return code


class MoneyValidation(BaseModel):
    """Money amount validation"""
    amount: Decimal = Field(..., gt=0, le=1000000)

    @validator('amount')
    def validate_money_precision(cls, v):
        # Check decimal places (max 2 for currency)
        if v.as_tuple().exponent < -2:
            raise ValueError('Amount cannot have more than 2 decimal places')

        return v


class PaymentValidation(BaseModel):
    """Enhanced payment validation"""
    amount: Decimal = Field(..., gt=0, le=1000000)
    currency: str = Field(default="CAD", regex="^[A-Z]{3}$")
    payment_method: str = Field(..., min_length=1, max_length=50)

    @validator('amount')
    def validate_payment_amount(cls, v):
        # Check decimal places (max 2 for currency)
        if v.as_tuple().exponent < -2:
            raise ValueError(
                'Payment amount cannot have more than 2 decimal places')

        # Check for reasonable payment amounts
        if v < Decimal('0.01'):
            raise ValueError('Payment amount must be at least $0.01')

        if v > Decimal('1000000'):
            raise ValueError('Payment amount cannot exceed $1,000,000')

        return v

    @validator('currency')
    def validate_currency_code(cls, v):
        # Valid Canadian currency codes
        valid_currencies = ['CAD', 'USD', 'EUR', 'GBP']
        if v not in valid_currencies:
            raise ValueError(
                f'Currency must be one of: {", ".join(valid_currencies)}')

        return v.upper()

    @validator('payment_method')
    def validate_payment_method(cls, v):
        # Valid payment methods
        valid_methods = [
            'credit_card', 'debit_card', 'bank_transfer', 'paypal',
            'stripe', 'interac', 'apple_pay', 'google_pay'
        ]

        if v.lower() not in valid_methods:
            raise ValueError(
                f'Payment method must be one of: {", ".join(valid_methods)}')

        return v.lower()


class CreditCardValidation(BaseModel):
    """Credit card validation"""
    card_number: str = Field(..., min_length=13, max_length=19)
    expiry_month: int = Field(..., ge=1, le=12)
    expiry_year: int = Field(..., ge=2024, le=2030)
    cvv: str = Field(..., min_length=3, max_length=4)
    cardholder_name: str = Field(..., min_length=2, max_length=100)

    @validator('card_number')
    def validate_card_number(cls, v):
        # Remove spaces and dashes
        clean_number = re.sub(r'[\s-]', '', v)

        # Check if all digits
        if not clean_number.isdigit():
            raise ValueError('Card number must contain only digits')

        # Luhn algorithm validation
        if not cls._luhn_check(clean_number):
            raise ValueError('Invalid card number')

        return clean_number

    @validator('expiry_month')
    def validate_expiry_month(cls, v):
        if v < 1 or v > 12:
            raise ValueError('Expiry month must be between 1 and 12')

        return v

    @validator('expiry_year')
    def validate_expiry_year(cls, v, values):
        current_year = datetime.now().year
        if v < current_year:
            raise ValueError('Card has expired')

        # Check if card expires within 10 years
        if v > current_year + 10:
            raise ValueError('Card expiry year is too far in the future')

        return v

    @validator('cvv')
    def validate_cvv(cls, v):
        if not v.isdigit():
            raise ValueError('CVV must contain only digits')

        return v

    @validator('cardholder_name')
    def validate_cardholder_name(cls, v):
        # Check for valid name format
        if not re.match(r'^[a-zA-Z\s\-\'\.]+$', v):
            raise ValueError('Cardholder name contains invalid characters')

        # Check minimum length
        if len(v.strip()) < 2:
            raise ValueError('Cardholder name must be at least 2 characters')

        return v.strip().title()

    @staticmethod
    def _luhn_check(card_number: str) -> bool:
        """Luhn algorithm for credit card validation"""
        def digits_of(n):
            return [int(d) for d in str(n)]

        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))

        return checksum % 10 == 0


class DateRangeValidation(BaseModel):
    """Date range validation"""
    start_date: date
    end_date: date

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')

        # Check if date is not too far in the future (max 1 year)
        max_future_date = date.today().replace(year=date.today().year + 1)
        if v > max_future_date:
            raise ValueError(
                'End date cannot be more than 1 year in the future')

        return v


class TimeSlotValidation(BaseModel):
    """Time slot validation"""
    start_time: time
    end_time: time

    @validator('end_time')
    def validate_time_slot(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')

        # Check if time slot is not too long (max 8 hours)
        start_minutes = values['start_time'].hour * \
            60 + values['start_time'].minute
        end_minutes = v.hour * 60 + v.minute
        duration_minutes = end_minutes - start_minutes

        if duration_minutes > 480:  # 8 hours
            raise ValueError('Time slot cannot be longer than 8 hours')

        return v


class FileUploadValidation(BaseModel):
    """File upload validation"""
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str
    size: int = Field(..., gt=0, le=10485760)  # 10MB max

    @validator('filename')
    def validate_filename(cls, v):
        # Check for dangerous file extensions
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com']
        if any(v.lower().endswith(ext) for ext in dangerous_extensions):
            raise ValueError('File type not allowed')

        # Check for path traversal attempts
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Invalid filename')

        return v

    @validator('content_type')
    def validate_content_type(cls, v):
        allowed_types = [
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/webp',
            'application/pdf',
            'text/plain',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document']

        if v not in allowed_types:
            raise ValueError('File type not allowed')

        return v


class AddressValidation(BaseModel):
    """Address validation"""
    street: str = Field(..., min_length=5, max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    province: str = Field(..., min_length=2, max_length=2)
    postal_code: str = Field(..., min_length=6, max_length=7)

    @validator('street')
    def validate_street(cls, v):
        # Check for valid street address format
        if not re.match(r'^\d+\s+[A-Za-z\s]+', v):
            raise ValueError('Invalid street address format')

        return v

    @validator('city')
    def validate_city(cls, v):
        # Check for valid city name (letters, spaces, hyphens, apostrophes)
        if not re.match(r'^[A-Za-z\s\-\']+$', v):
            raise ValueError('Invalid city name format')

        return v.title()

    @validator('province')
    def validate_province(cls, v):
        # Canadian province codes
        valid_provinces = [
            'AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU',
            'ON', 'PE', 'QC', 'SK', 'YT'
        ]

        if v.upper() not in valid_provinces:
            raise ValueError('Invalid Canadian province code')

        return v.upper()


class ServiceRateValidation(BaseModel):
    """Service rate validation"""
    hourly_rate: Optional[Decimal] = Field(None, ge=0, le=1000)
    daily_rate: Optional[Decimal] = Field(None, ge=0, le=5000)

    @validator('hourly_rate')
    def validate_hourly_rate(cls, v):
        if v is not None and v < 15:
            raise ValueError('Hourly rate must be at least $15/hour')

        return v

    @validator('daily_rate')
    def validate_daily_rate(cls, v):
        if v is not None and v < 100:
            raise ValueError('Daily rate must be at least $100/day')

        return v

    @validator('daily_rate')
    def validate_rate_consistency(cls, v, values):
        if 'hourly_rate' in values and v is not None and values['hourly_rate'] is not None:
            # Daily rate should be reasonable compared to hourly rate
            hourly = values['hourly_rate']
            if v < hourly * 4:  # Less than 4 hours worth
                raise ValueError(
                    'Daily rate seems too low compared to hourly rate')
            if v > hourly * 12:  # More than 12 hours worth
                raise ValueError(
                    'Daily rate seems too high compared to hourly rate')

        return v


class MessageContentValidation(BaseModel):
    """Message content validation"""
    content: str = Field(..., min_length=1, max_length=5000)

    @validator('content')
    def validate_message_content(cls, v):
        # Check for spam patterns
        spam_patterns = [
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            r'(?i)(buy now|click here|free money|urgent|act now)',
            r'(?i)(viagra|cialis|pharmacy|medication)',
        ]

        for pattern in spam_patterns:
            if re.search(pattern, v):
                raise ValueError('Message content appears to be spam')

        # Check for excessive repetition
        words = v.split()
        if len(words) > 10:
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1

            # Check if any word appears more than 30% of the time
            max_repetition = max(word_counts.values())
            if max_repetition > len(words) * 0.3:
                raise ValueError('Message contains excessive repetition')

        return v


class ReviewValidation(BaseModel):
    """Review validation"""
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)

    @validator('comment')
    def validate_review_comment(cls, v):
        if v is not None:
            # Check for profanity (simplified)
            profanity_words = ['bad', 'terrible',
                               'awful', 'hate']  # Add more as needed
            comment_lower = v.lower()

            for word in profanity_words:
                if word in comment_lower:
                    raise ValueError(
                        'Review comment contains inappropriate language')

        return v


class SearchQueryValidation(BaseModel):
    """Search query validation"""
    query: str = Field(..., min_length=1, max_length=100)

    @validator('query')
    def validate_search_query(cls, v):
        # Remove excessive whitespace
        v = ' '.join(v.split())

        # Check for SQL injection patterns
        sql_patterns = [
            r'(?i)(union|select|insert|update|delete|drop|create|alter)',
            r'(?i)(or|and)\s+\d+\s*=\s*\d+',
            r'[\'";]',
        ]

        for pattern in sql_patterns:
            if re.search(pattern, v):
                raise ValueError(
                    'Search query contains potentially dangerous content')

        return v


class PaginationValidation(BaseModel):
    """Pagination validation"""
    page: int = Field(1, ge=1, le=1000)
    limit: int = Field(10, ge=1, le=100)

    @validator('limit')
    def validate_limit(cls, v):
        if v > 100:
            raise ValueError('Limit cannot exceed 100 items per page')

        return v


class UUIDValidation(BaseModel):
    """UUID validation"""
    id: uuid.UUID

    @validator('id')
    def validate_uuid(cls, v):
        if v.version is None:
            raise ValueError('Invalid UUID format')

        return v


class BusinessHoursValidation(BaseModel):
    """Business hours validation"""
    day_of_week: int = Field(..., ge=0, le=6)  # 0 = Monday, 6 = Sunday
    open_time: time
    close_time: time
    is_closed: bool = False

    @validator('close_time')
    def validate_business_hours(cls, v, values):
        if not values.get('is_closed', False):
            if 'open_time' in values and v <= values['open_time']:
                raise ValueError('Close time must be after open time')

            # Check if business hours are reasonable (max 16 hours)
            open_minutes = values['open_time'].hour * \
                60 + values['open_time'].minute
            close_minutes = v.hour * 60 + v.minute
            duration_minutes = close_minutes - open_minutes

            if duration_minutes > 960:  # 16 hours
                raise ValueError(
                    'Business hours cannot exceed 16 hours per day')

        return v


# Export all validation classes
__all__ = [
    'EmailValidation',
    'PasswordValidation',
    'PhoneValidation',
    'PostalCodeValidation',
    'MoneyValidation',
    'DateRangeValidation',
    'TimeSlotValidation',
    'FileUploadValidation',
    'AddressValidation',
    'ServiceRateValidation',
    'MessageContentValidation',
    'ReviewValidation',
    'SearchQueryValidation',
    'PaginationValidation',
    'UUIDValidation',
    'BusinessHoursValidation'
]
