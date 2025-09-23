from sqlalchemy.orm import Session
from app.models.notifications import Notification, UserNotificationPreference, NotificationLog
from uuid import UUID


def create_notification(db: Session, notification: Notification) -> Notification:
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def update_preferences(db: Session, user_id: UUID, prefs: dict):
    pref = db.query(UserNotificationPreference).filter(UserNotificationPreference.user_id == user_id).first()
    if not pref:
        pref = UserNotificationPreference(user_id=user_id, **prefs)
        db.add(pref)
    else:
        for k, v in prefs.items():
            setattr(pref, k, v)
    db.commit()
    db.refresh(pref)
    return pref


def log_notification(db: Session, log: NotificationLog) -> NotificationLog:
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
