from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.tokens import RefreshToken
from app.repositories import users as user_repo
from app.utils.auth import create_access_token, create_refresh_token
from app.utils.hashing import get_password_hash, verify_password


def register_user(
        db: Session,
        email: str,
        name: str,
        role: str,
        password: str):
    if user_repo.get_user_by_email(db, email):
        raise ValueError("Email already registered")
    password_hash = get_password_hash(password)
    return user_repo.create_user(db, email, name, role, password_hash)


def authenticate_user(db: Session, email: str, password: str):
    user = user_repo.get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def issue_tokens(db: Session, user_id: str):
    access_token_expires = timedelta(minutes=15)
    access_token = create_access_token(
        {"sub": str(user_id)}, expires_delta=access_token_expires)
    refresh_token = create_refresh_token({"sub": str(user_id)})

    db_refresh = RefreshToken(
        user_id=user_id,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(db_refresh)
    db.commit()

    return access_token, refresh_token


def change_user_password(
        db: Session,
        user,
        old_password: str,
        new_password: str):
    if not verify_password(old_password, user.password_hash):
        raise ValueError("Old password is incorrect")
    new_hash = get_password_hash(new_password)
    return user_repo.update_user_password(db, user, new_hash)
