from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
from enum import Enum


# --- Enums ---
class UserRole(str, Enum):
    client = "client"
    provider = "provider"
    admin = "admin"


class UserStatus(str, Enum):
    active = "active"
    suspended = "suspended"
    deleted = "deleted"


# --- Shared base fields ---
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole


# --- Create User ---
class UserCreate(UserBase):
    password: str

    class Config:
        schema_extra = {
            "example": {
                "email": "jane@example.com",
                "name": "Jane Doe",
                "role": "client",
                "password": "strongpassword123"
            }
        }


# --- Forgot/Reset Password ---
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    class Config:
        schema_extra = {
            "example": {"email": "jane@example.com"}
        }


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    class Config:
        schema_extra = {
            "example": {
                "token": "123e4567-e89b-12d3-a456-426614174000",
                "new_password": "newsecurepassword"
            }
        }


# --- Change Password ---
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    class Config:
        schema_extra = {
            "example": {
                "old_password": "oldpassword123",
                "new_password": "newsecurepassword"
            }
        }


# --- Login ---
class UserLogin(BaseModel):
    email: EmailStr
    password: str

    class Config:
        schema_extra = {
            "example": {
                "email": "jane@example.com",
                "password": "strongpassword123"
            }
        }


# --- User Response ---
class UserResponse(UserBase):
    id: uuid.UUID
    is_email_verified: bool
    status: UserStatus

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "jane@example.com",
                "name": "Jane Doe",
                "role": "client",
                "is_email_verified": True,
                "status": "active"
            }
        }


# --- Admin-only Response ---
class UserAdminResponse(UserResponse):
    phone_number: Optional[str]
    is_phone_verified: Optional[bool]
    province_code: Optional[str]
    last_login_at: Optional[str]
    created_at: Optional[str]


# --- Token responses ---
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
