from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
from enum import Enum
from datetime import datetime


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
    password: str


# --- Forgot/Reset Password ---
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# --- Change Password ---
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


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
        orm_mode = True


# --- Admin-only Response (extended) ---
class UserAdminResponse(UserResponse):
    phone_number: Optional[str]
    is_phone_verified: Optional[bool]
    province_code: Optional[str]
    address: Optional[str]
    location: Optional[str]  # lat/lon as "POINT" WKT
    verification_token: Optional[str]
    password_reset_token: Optional[str]
    password_reset_expires: Optional[datetime]
    last_login_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]


# --- Token responses ---
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
