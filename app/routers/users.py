from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from app.db import SessionLocal
from app.models.users import User
from app.models.tokens import RefreshToken
from app.schemas.users import (
    UserCreate,
    UserResponse,
    TokenResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.utils.hashing import get_password_hash, verify_password
from app.utils.auth import create_access_token, create_refresh_token, verify_token
from app.utils.deps import get_current_user, require_admin, require_provider, require_client
from app.utils.email import send_password_reset_email


router = APIRouter(prefix="/users", tags=["Users"])


# --- Dependency: DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Authentication ---
@router.post(
    "/register",
    response_model=UserResponse,
    tags=["Authentication"],
    summary="Register a new user",
    description="Create a new account by providing email, name, role, and password.",
)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user.email,
        name=user.name,
        role=user.role,
        password_hash=get_password_hash(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    tags=["Authentication"],
    summary="Log in a user",
    description="Authenticate a user with email and password. Returns access and refresh tokens.",
)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=15)
    access_token = create_access_token({"sub": str(db_user.id)}, expires_delta=access_token_expires)
    refresh_token = create_refresh_token({"sub": str(db_user.id)})

    db_refresh = RefreshToken(
        user_id=db_user.id,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(db_refresh)
    db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    tags=["Authentication"],
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new short-lived access token.",
)
def refresh_token(refresh_token: str = Body(..., example="eyJhbGciOi..."), db: Session = Depends(get_db)):
    payload = verify_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if not db_token or db_token.revoked or db_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired")

    access_token_expires = timedelta(minutes=15)
    new_access_token = create_access_token({"sub": user_id}, expires_delta=access_token_expires)

    return TokenResponse(access_token=new_access_token)


@router.post(
    "/logout",
    tags=["Authentication"],
    summary="Log out user",
    description="Revoke the provided refresh token, effectively logging the user out.",
)
def logout(refresh_token: str = Body(..., example="eyJhbGciOi..."), db: Session = Depends(get_db)):
    db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if db_token:
        db_token.revoked = True
        db.commit()
    return {"detail": "Logged out successfully"}


# --- Password Management ---
@router.post(
    "/change-password",
    tags=["Password Management"],
    summary="Change password (logged in)",
    description="Authenticated users can update their password by providing old and new passwords.",
)
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_password(body.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    current_user.password_hash = get_password_hash(body.new_password)

    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.revoked == False
    ).update({"revoked": True})

    db.commit()
    return {"detail": "Password updated and all sessions revoked. Please log in again."}


@router.post(
    "/forgot-password",
    tags=["Password Management"],
    summary="Request password reset",
    description="Request a password reset link by providing a registered email address.",
)
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        return {"detail": "If this email is registered, a reset link has been sent."}

    reset_token = str(uuid.uuid4())
    user.password_reset_token = reset_token
    user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()

    send_password_reset_email(user.email, reset_token)

    return {"detail": "If this email is registered, a reset link has been sent."}


@router.post(
    "/reset-password",
    tags=["Password Management"],
    summary="Reset password",
    description="Reset password using the token sent via email. Revokes all sessions.",
)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.password_reset_token == body.token).first()
    if not user or not user.password_reset_expires or user.password_reset_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.password_hash = get_password_hash(body.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None

    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked == False
    ).update({"revoked": True})

    db.commit()

    return {"detail": "Password has been reset successfully. Please log in again."}


# --- Profile & Dashboards ---
@router.get(
    "/me",
    response_model=UserResponse,
    tags=["Profile"],
    summary="Get current user profile",
    description="Return profile information of the currently authenticated user.",
)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.get(
    "/admin/dashboard",
    tags=["Profile"],
    summary="Admin dashboard",
    description="Restricted to admins. Returns admin-specific dashboard info.",
)
def admin_dashboard(current_user: User = Depends(require_admin)):
    return {"message": f"Welcome Admin {current_user.name} 🚀"}


@router.get(
    "/provider/dashboard",
    tags=["Profile"],
    summary="Provider dashboard",
    description="Restricted to providers. Returns provider-specific dashboard info.",
)
def provider_dashboard(current_user: User = Depends(require_provider)):
    return {"message": f"Welcome Provider {current_user.name}, here are your bookings"}


@router.get(
    "/client/dashboard",
    tags=["Profile"],
    summary="Client dashboard",
    description="Restricted to clients. Returns client-specific dashboard info.",
)
def client_dashboard(current_user: User = Depends(require_client)):
    return {"message": f"Welcome Client {current_user.name}, here are your active services"}


# --- Admin Tools ---
@router.post(
    "/admin/revoke-tokens/{user_id}",
    tags=["Admin"],
    summary="Revoke all tokens for a user",
    description="Admin-only endpoint. Revokes all active refresh tokens for the specified user.",
)
def revoke_all_tokens(user_id: str, db: Session = Depends(get_db), current_admin=Depends(require_admin)):
    tokens = db.query(RefreshToken).filter(RefreshToken.user_id == user_id, RefreshToken.revoked == False).all()
    if not tokens:
        return {"detail": "No active tokens found for this user"}

    for token in tokens:
        token.revoked = True
    db.commit()

    return {"detail": f"All refresh tokens revoked for user {user_id}"}
