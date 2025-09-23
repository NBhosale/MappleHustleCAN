from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.notifications import Notification, UserNotificationPreference, NotificationLog
from app.schemas.notifications import (
    NotificationCreate,
    NotificationResponse,
    NotificationStatus,
    NotificationChannel,
    UserNotificationPreferenceUpdate,
    UserNotificationPreferenceResponse,
    NotificationLogResponse,
)
from app.utils.deps import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Create Notification (System/Admin use) ---
@router.post("/", response_model=NotificationResponse)
def create_notification(
    notif: NotificationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),  # could restrict to admin
):
    new_notif = Notification(
        user_id=notif.user_id,
        type=notif.type,
        content=notif.content,
        status=notif.status,
        channel=notif.channel,
    )
    db.add(new_notif)
    db.commit()
    db.refresh(new_notif)
    return new_notif


# --- Get My Notifications ---
@router.get("/me", response_model=list[NotificationResponse])
def get_my_notifications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(Notification).filter(Notification.user_id == current_user.id).all()


# --- Mark as Read ---
@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    if str(notif.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only mark your own notifications")

    notif.status = NotificationStatus.read
    db.commit()
    db.refresh(notif)
    return notif


# --- Update Preferences ---
@router.put("/preferences", response_model=UserNotificationPreferenceResponse)
def update_preferences(
    prefs: UserNotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_prefs = db.query(UserNotificationPreference).filter(
        UserNotificationPreference.user_id == current_user.id
    ).first()

    if not user_prefs:
        user_prefs = UserNotificationPreference(user_id=current_user.id, **prefs.dict())
        db.add(user_prefs)
    else:
        for key, value in prefs.dict().items():
            setattr(user_prefs, key, value)

    db.commit()
    db.refresh(user_prefs)
    return user_prefs


# --- View Notification Logs (Admin only) ---
@router.get("/logs", response_model=list[NotificationLogResponse])
def get_logs(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),  # tighten later with require_admin
):
    return db.query(NotificationLog).all()
