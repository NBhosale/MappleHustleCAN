from uuid import UUID

from sqlalchemy.orm import Session

from app.models.users import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(
        db: Session,
        email: str,
        name: str,
        role: str,
        password_hash: str) -> User:
    user = User(email=email, name=name, role=role, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_password(
        db: Session,
        user: User,
        new_password_hash: str) -> User:
    user.password_hash = new_password_hash
    db.commit()
    db.refresh(user)
    return user
