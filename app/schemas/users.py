import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


# --- Enums ---
class UserRole(str, Enum):
    client = "client"
    provider = "provider"
    admin = "admin"


class UserStatus(str, Enum):
    active = "active"
    suspended = "suspended"
    deleted = "deleted"


class ContactMethod(str, Enum):
    in_app = "in_app"
    email = "email"
    sms = "sms"


# --- Shared base fields ---
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole


# --- Create User ---
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

    @validator('password')
    def validate_password(cls, v):
        if not re.match(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]',
                v):
            raise ValueError(
                'Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character')
        return v

    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip()


# --- Forgot/Reset Password ---
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=32)
    new_password: str = Field(..., min_length=8, max_length=128)

    @validator('new_password')
    def validate_password(cls, v):
        if not re.match(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]',
                v):
            raise ValueError(
                'Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character')
        return v


# --- Change Password ---
class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @validator('new_password')
    def validate_password(cls, v):
        if not re.match(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]',
                v):
            raise ValueError(
                'Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character')
        return v


# --- Login ---
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# --- User Response (safe for client) ---
class UserResponse(UserBase):
    id: uuid.UUID
    is_email_verified: bool
    status: UserStatus
    city: Optional[str]
    postal_code: Optional[str]
    profile_image_path: Optional[str]
    preferred_contact_method: Optional[ContactMethod]

    class Config:
        from_attributes = True


# --- Admin-only Response (extended) ---
# SECURITY NOTE: This schema is intentionally minimal to prevent sensitive data exposure
# Even admin users should not have access to sensitive fields like tokens
# or password hashes
class UserAdminResponse(UserResponse):
    phone_number: Optional[str]
    is_phone_verified: Optional[bool]
    province_code: Optional[str]
    address: Optional[str]
    location: Optional[str]  # lat/lon as "POINT" WKT
    last_login_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    # SECURITY: Sensitive fields (verification_token, password_reset_token, hashed_password)
    # are intentionally excluded even from admin responses for security reasons

    class Config:
        from_attributes = True


# --- Admin Detail Response (for internal admin operations only) ---
# WARNING: This schema should ONLY be used for internal admin operations
# and NEVER exposed via public API endpoints
class UserAdminDetailResponse(UserAdminResponse):
    """Extended admin response with additional fields for internal admin operations"""
    # Additional admin fields can be added here if needed
    # But NEVER include sensitive fields like tokens or password hashes


# --- Token responses ---
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
