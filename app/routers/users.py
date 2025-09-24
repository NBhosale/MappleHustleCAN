from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from app.db import SessionLocal
from app.schemas.users import (
    UserCreate,
    UserResponse,
    UserAdminResponse,
    TokenResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services import users as user_service
from app.utils.deps import get_current_user, require_admin, require_provider, require_client
from app.utils.auth import verify_token
from app.utils.email import send_password_reset_email
from app.tasks.email_tasks import send_welcome_email_task, send_password_reset_email_task, send_email_verification_task
from app.tasks.notification_tasks import create_notification_task
from app.utils.validation import (
    validate_canadian_province,
    validate_postal_code,
    ValidationError
)
from app.models.tokens import RefreshToken

router = APIRouter(prefix="/users", tags=["Users"])


# --- Dependency: DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Change Password ---
@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        user_service.change_user_password(db, current_user, body.old_password, body.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"detail": "Password updated and all sessions revoked. Please log in again."}


# --- Profile & Dashboards ---
@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user=Depends(get_current_user)):
    # Convert User model to UserResponse schema to ensure no sensitive fields are exposed
    return UserResponse.from_orm(current_user)


@router.get("/admin/dashboard")
def admin_dashboard(current_user=Depends(require_admin)):
    return {"message": f"Welcome Admin {current_user.name} 🚀"}


@router.get("/provider/dashboard")
def provider_dashboard(current_user=Depends(require_provider)):
    return {"message": f"Welcome Provider {current_user.name}, here are your bookings"}


@router.get("/client/dashboard")
def client_dashboard(current_user=Depends(require_client)):
    return {"message": f"Welcome Client {current_user.name}, here are your bookings"}
