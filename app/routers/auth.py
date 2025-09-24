"""
Authentication endpoints with secure refresh token handling
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.middleware import limiter
from app.core.refresh_token_manager import refresh_token_manager
from app.core.structured_logging import get_api_logger, get_business_logger
from app.db import SessionLocal
from app.models.users import User
from app.schemas.tokens import RefreshTokenResponse
from app.schemas.users import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.utils.auth import create_access_token
from app.utils.hashing import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()
logger = get_api_logger()
business_logger = get_business_logger()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=UserResponse)
@limiter.limit("5/minute")  # 5 registrations per minute per IP
async def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        hashed_password = hash_password(user_data.password)
        user = User(
            email=user_data.email,
            name=user_data.name,
            role=user_data.role,
            hashed_password=hashed_password,
            is_email_verified=False,
            status="active"
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # Log user registration
        business_logger.log_user_action(
            user_id=str(user.id),
            action="user_registered",
            details={"email": user.email, "role": user.role}
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "status": user.status,
                "is_email_verified": user.is_email_verified,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error(f"Registration error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")  # 10 login attempts per minute per IP
async def login(
    request: Request,
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login user and return access + refresh tokens
    """
    try:
        # Find user
        user = db.query(User).filter(User.email == credentials.email).first()
        if not user or not verify_password(
                credentials.password, user.hashed_password):
            logger.log_authentication_failure(
                endpoint="/auth/login",
                reason="invalid_credentials",
                client_ip=None
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Check if user is active
        if user.status != "active":
            logger.log_authentication_failure(
                endpoint="/auth/login",
                reason="inactive_user",
                client_ip=None
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is not active"
            )

        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )

        # Create and store refresh token
        refresh_token, _ = refresh_token_manager.create_refresh_token(
            db=db,
            user_id=str(user.id)
        )

        # Update last login
        user.last_login_at = datetime.utcnow()
        db.commit()

        # Log successful login
        business_logger.log_user_action(
            user_id=str(user.id),
            action="user_logged_in",
            details={"email": user.email, "role": user.role}
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")  # 20 refresh attempts per minute per IP
async def refresh_access_token(
    request: Request,
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    try:
        # Validate refresh token
        token_data = refresh_token_manager.validate_refresh_token(
            db=db,
            token=refresh_token
        )

        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # token_data is already a User object from validate_refresh_token
        user = token_data
        if not user or user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Create new access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )

        # Rotate refresh token (optional - for enhanced security)
        new_refresh_token, _ = refresh_token_manager.rotate_refresh_token(
            db=db,
            old_token=refresh_token
        )

        # Log token refresh
        business_logger.log_user_action(
            user_id=str(user.id),
            action="token_refreshed",
            details={"email": user.email}
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error(f"Token refresh error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Logout user and revoke refresh token
    """
    try:
        # Revoke refresh token
        success = refresh_token_manager.revoke_refresh_token(
            db=db,
            token=refresh_token
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid refresh token"
            )

        # Log logout
        business_logger.log_user_action(
            user_id="unknown",
            action="user_logged_out",
            details={"token_revoked": True}
        )

        return {"message": "Successfully logged out"}

    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error(f"Logout error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/logout-all")
async def logout_all_sessions(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Logout user from all sessions (revoke all refresh tokens)
    """
    try:
        # Revoke all refresh tokens for user
        success = refresh_token_manager.revoke_all_user_tokens(
            db=db,
            user_id=user_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )

        # Log logout all
        business_logger.log_user_action(
            user_id=user_id,
            action="user_logged_out_all_sessions",
            details={"all_tokens_revoked": True}
        )

        return {"message": "Successfully logged out from all sessions"}

    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error(f"Logout all error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout all failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get current user information
    """
    try:
        # Verify access token
        from app.utils.auth import verify_token
        payload = verify_token(credentials.credentials)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token"
            )

        # Get user
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error(f"Get user info error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.get("/refresh-tokens", response_model=list[RefreshTokenResponse])
async def get_user_refresh_tokens(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get user's active refresh tokens (for security monitoring)
    """
    try:
        # Get user's refresh tokens
        tokens = refresh_token_manager.get_user_refresh_tokens(
            db=db,
            user_id=user_id
        )

        return tokens

    except Exception as e:
        logger.logger.error(
            f"Get refresh tokens error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get refresh tokens"
        )
