from sqlalchemy.orm import Session
from app.models.notifications import Notification, NotificationLog
from app.repositories import notifications as notif_repo
from datetime import datetime


def send_notification(db: Session, user_id, type, content, channel="in_app"):
    notif = Notification(
        user_id=user_id,
        type=type,
        content=content,
        status="unread",
        channel=channel,
        sent_at=datetime.utcnow(),
        delivered=True,
    )
    return notif_repo.create_notification(db, notif)


def update_user_preferences(db: Session, user_id, prefs: dict):
    return notif_repo.update_preferences(db, user_id, prefs)


def log_notification_delivery(db: Session, notification_id, channel, status, response=None):
    log = NotificationLog(
        notification_id=notification_id,
        channel=channel,
        status=status,
        response=response,
        created_at=datetime.utcnow(),
    )
    return notif_repo.log_notification(db, log)
