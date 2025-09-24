from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.schemas.users import (
    ChangePasswordRequest,
    UserResponse,
)
from app.services import users as user_service
from app.utils.deps import (
    get_current_user,
    require_admin,
    require_client,
    require_provider,
)

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
        user_service.change_user_password(
            db, current_user, body.old_password, body.new_password
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "detail": "Password updated and all sessions revoked. Please log in again."}


# --- Profile & Dashboards ---
@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user=Depends(get_current_user)):
    # Convert User model to UserResponse schema to ensure no sensitive fields
    return UserResponse.from_orm(current_user)


@router.get("/admin/dashboard")
def admin_dashboard(current_user=Depends(require_admin)):
    return {"message": f"Welcome Admin {current_user.name} 🚀"}


@router.get("/provider/dashboard")
def provider_dashboard(current_user=Depends(require_provider)):
    return {
        "message": f"Welcome Provider {
            current_user.name}, here are your bookings"}


@router.get("/client/dashboard")
def client_dashboard(current_user=Depends(require_client)):
    return {
        "message": f"Welcome Client {
            current_user.name}, here are your bookings"}
