import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.schemas.notifications import (
    NotificationCreate,
    NotificationLogResponse,
    NotificationResponse,
    UserNotificationPreferenceResponse,
    UserNotificationPreferenceUpdate,
)
from app.services import notifications as notification_service
from app.utils.deps import get_current_user, require_admin

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# --- Dependency: DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Notifications ---
@router.post("/", response_model=NotificationResponse)
def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),  # Only admins or system triggers
):
    try:
        return notification_service.create_notification(db, notification)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[NotificationResponse])
def list_my_notifications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return notification_service.list_user_notifications(db, current_user.id)


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return notification_service.mark_as_read(
            db, notification_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Preferences ---
@router.put("/preferences", response_model=UserNotificationPreferenceResponse)
def update_preferences(
    preferences: UserNotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return notification_service.update_preferences(
        db, current_user.id, preferences)


@router.get("/preferences", response_model=UserNotificationPreferenceResponse)
def get_preferences(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return notification_service.get_preferences(db, current_user.id)


# --- Logs (Admin only) ---
@router.get("/{notification_id}/logs",
            response_model=List[NotificationLogResponse])
def get_notification_logs(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    return notification_service.get_logs(db, notification_id)
