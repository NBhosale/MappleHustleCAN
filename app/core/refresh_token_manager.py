"""
Refresh Token Manager for secure token lifecycle and rotation
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.models.tokens import RefreshToken
from app.models.users import User
from app.schemas.tokens import TokenResponse

# Password hashing context for token hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RefreshTokenManager:
    """Manages refresh token lifecycle, rotation, and security"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
        self.max_refresh_tokens_per_user = settings.MAX_REFRESH_TOKENS_PER_USER
    
    def generate_refresh_token(self, user_id: str) -> str:
        """Generate a secure refresh token"""
        # Generate a cryptographically secure random token
        token_data = secrets.token_urlsafe(32)
        
        # Add timestamp and user info for additional security
        payload = {
            "user_id": user_id,
            "token_type": "refresh",
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16)  # JWT ID for token tracking
        }
        
        # Sign the token
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        return token
    
    def hash_refresh_token(self, token: str) -> str:
        """Hash refresh token for secure storage"""
        return pwd_context.hash(token)
    
    def verify_refresh_token(self, token: str, hashed_token: str) -> bool:
        """Verify refresh token against stored hash"""
        return pwd_context.verify(token, hashed_token)
    
    def create_refresh_token(self, db: Session, user_id: str) -> Tuple[str, RefreshToken]:
        """Create a new refresh token for user"""
        # Generate new token
        token = self.generate_refresh_token(user_id)
        hashed_token = self.hash_refresh_token(token)
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        # Clean up old tokens for this user (token rotation)
        self._cleanup_old_tokens(db, user_id)
        
        # Create new refresh token record
        refresh_token = RefreshToken(
            user_id=user_id,
            token=hashed_token,
            expires_at=expires_at,
            revoked=False
        )
        
        db.add(refresh_token)
        db.commit()
        db.refresh(refresh_token)
        
        return token, refresh_token
    
    def validate_refresh_token(self, db: Session, token: str) -> Optional[User]:
        """Validate refresh token and return user if valid"""
        try:
            # Decode token to get user_id
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            token_type = payload.get("token_type")
            
            if not user_id or token_type != "refresh":
                return None
            
            # Find the token in database
            refresh_token = db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.utcnow()
            ).first()
            
            if not refresh_token:
                return None
            
            # Verify token against stored hash
            if not self.verify_refresh_token(token, refresh_token.token):
                return None
            
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            return user
            
        except JWTError:
            return None
    
    def revoke_refresh_token(self, db: Session, token: str) -> bool:
        """Revoke a specific refresh token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            
            if not user_id:
                return False
            
            # Find and revoke the token
            refresh_token = db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False
            ).first()
            
            if refresh_token:
                refresh_token.revoked = True
                refresh_token.revoked_at = datetime.utcnow()
                db.commit()
                return True
            
            return False
            
        except JWTError:
            return False
    
    def revoke_all_user_tokens(self, db: Session, user_id: str) -> int:
        """Revoke all refresh tokens for a user"""
        count = db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False
        ).update({
            "revoked": True,
            "revoked_at": datetime.utcnow()
        })
        
        db.commit()
        return count
    
    def rotate_refresh_token(self, db: Session, old_token: str) -> Tuple[str, RefreshToken]:
        """Rotate refresh token (revoke old, create new)"""
        try:
            payload = jwt.decode(old_token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            
            if not user_id:
                raise ValueError("Invalid token")
            
            # Revoke old token
            self.revoke_refresh_token(db, old_token)
            
            # Create new token
            return self.create_refresh_token(db, user_id)
            
        except JWTError:
            raise ValueError("Invalid token")
    
    def _cleanup_old_tokens(self, db: Session, user_id: str):
        """Clean up old tokens for user (keep only recent ones)"""
        # Get all active tokens for user
        active_tokens = db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False
        ).order_by(RefreshToken.created_at.desc()).all()
        
        # If we have more than the limit, revoke the oldest ones
        if len(active_tokens) >= self.max_refresh_tokens_per_user:
            tokens_to_revoke = active_tokens[self.max_refresh_tokens_per_user - 1:]
            for token in tokens_to_revoke:
                token.revoked = True
                token.revoked_at = datetime.utcnow()
        
        db.commit()
    
    def cleanup_expired_tokens(self, db: Session) -> int:
        """Clean up expired tokens from database"""
        count = db.query(RefreshToken).filter(
            RefreshToken.expires_at < datetime.utcnow()
        ).delete()
        
        db.commit()
        return count
    
    def get_user_active_tokens(self, db: Session, user_id: str) -> list:
        """Get all active refresh tokens for a user"""
        return db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        ).all()
    
    def is_token_compromised(self, db: Session, token: str) -> bool:
        """Check if token has been marked as compromised"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            jti = payload.get("jti")
            
            if not user_id or not jti:
                return True
            
            # Check if token is revoked
            refresh_token = db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == True
            ).first()
            
            return refresh_token is not None
            
        except JWTError:
            return True


# Global instance
refresh_token_manager = RefreshTokenManager()
