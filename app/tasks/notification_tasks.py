"""
Notification background tasks for MapleHustleCAN
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.notifications import Notification
from app.models.users import User
from app.tasks.email_tasks import send_email_notification

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def create_notification_task(
    self,
    user_id: str,
    title: str,
    message: str,
    notification_type: str = "info",
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a notification for a user

    Args:
        user_id: User ID
        title: Notification title
        message: Notification message
        notification_type: Type of notification (info, warning, error, success)
        data: Optional additional data

    Returns:
        Dict with task result
    """
    try:
        db = SessionLocal()
        try:
            # Create notification
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                data=data or {},
                created_at=datetime.utcnow()
            )

            db.add(notification)
            db.commit()
            db.refresh(notification)

            logger.info(f"Notification created for user {user_id}: {title}")

            return {
                "success": True,
                "notification_id": str(notification.id),
                "user_id": user_id,
                "title": title
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error creating notification for user {user_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_email(
    self,
    user_id: str,
    title: str,
    message: str,
    notification_type: str = "info"
) -> Dict[str, Any]:
    """
    Send notification via email

    Args:
        user_id: User ID
        title: Notification title
        message: Notification message
        notification_type: Type of notification

    Returns:
        Dict with task result
    """
    try:
        db = SessionLocal()
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            # Send email notification
            email_result = send_email_notification.delay(
                to_email=user.email,
                subject=f"MapleHustleCAN: {title}",
                message=message,
                user_id=user_id
            ).get()

            # Create notification record
            notification_result = create_notification_task.delay(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type
            ).get()

            return {
                "success": True, "email_sent": email_result.get(
                    "success", False), "notification_created": notification_result.get(
                    "success", False), "user_id": user_id}

        finally:
            db.close()

    except Exception as e:
        logger.error(
            f"Error sending notification email to user {user_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_notification(
    self,
    user_id: str,
    booking_details: Dict[str, Any],
    notification_type: str = "booking_confirmation"
) -> Dict[str, Any]:
    """
    Send booking-related notification

    Args:
        user_id: User ID
        booking_details: Booking information
        notification_type: Type of booking notification

    Returns:
        Dict with task result
    """
    try:
        service_name = booking_details.get("service_name", "Service")
        date = booking_details.get("date", "Unknown date")
        time = booking_details.get("time", "Unknown time")

        if notification_type == "booking_confirmation":
            title = "Booking Confirmed"
            message = f"Your booking for {service_name} on {date} at {time} has been confirmed."
        elif notification_type == "booking_reminder":
            title = "Booking Reminder"
            message = f"Reminder: You have a booking for {service_name} tomorrow ({date}) at {time}."
        elif notification_type == "booking_cancelled":
            title = "Booking Cancelled"
            message = f"Your booking for {service_name} on {date} at {time} has been cancelled."
        else:
            title = "Booking Update"
            message = f"Your booking for {service_name} has been updated."

        return send_notification_email.delay(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="info"
        ).get()

    except Exception as e:
        logger.error(
            f"Error sending booking notification to user {user_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_payment_notification(
    self,
    user_id: str,
    payment_details: Dict[str, Any],
    notification_type: str = "payment_confirmation"
) -> Dict[str, Any]:
    """
    Send payment-related notification

    Args:
        user_id: User ID
        payment_details: Payment information
        notification_type: Type of payment notification

    Returns:
        Dict with task result
    """
    try:
        amount = payment_details.get("amount", "Unknown amount")
        service_name = payment_details.get("service_name", "Service")

        if notification_type == "payment_confirmation":
            title = "Payment Confirmed"
            message = f"Payment of ${amount} for {service_name} has been processed successfully."
        elif notification_type == "payment_failed":
            title = "Payment Failed"
            message = f"Payment of ${amount} for {service_name} failed. Please try again."
        elif notification_type == "refund_processed":
            title = "Refund Processed"
            message = f"Refund of ${amount} for {service_name} has been processed."
        else:
            title = "Payment Update"
            message = f"Your payment for {service_name} has been updated."

        return send_notification_email.delay(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="info"
        ).get()

    except Exception as e:
        logger.error(
            f"Error sending payment notification to user {user_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_daily_reports(self) -> Dict[str, Any]:
    """
    Send daily reports to admin users

    Returns:
        Dict with task result
    """
    try:
        db = SessionLocal()
        try:
            # Get admin users
            admin_users = db.query(User).filter(User.role == "admin").all()

            # Get daily statistics
            from datetime import date
            today = date.today()

            # This would be replaced with actual statistics queries
            stats = {
                "date": today.isoformat(),
                "total_users": db.query(User).count(),
                "new_users_today": 0,  # Would query for today's new users
                "total_bookings": 0,  # Would query bookings
                "revenue_today": 0.0,  # Would query revenue
            }

            # Send reports to admin users
            results = []
            for admin in admin_users:
                title = "Daily Report"
                message = f"""
Daily Report for {today}:

- Total Users: {stats['total_users']}
- New Users Today: {stats['new_users_today']}
- Total Bookings: {stats['total_bookings']}
- Revenue Today: ${stats['revenue_today']}

Best regards,
MapleHustleCAN Team
                """

                result = send_notification_email.delay(
                    user_id=str(admin.id),
                    title=title,
                    message=message,
                    notification_type="info"
                ).get()

                results.append(result)

            return {
                "success": True,
                "reports_sent": len(results),
                "admin_users": len(admin_users),
                "stats": stats
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error sending daily reports: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def cleanup_old_notifications(self) -> Dict[str, Any]:
    """
    Clean up old notifications (older than 30 days)

    Returns:
        Dict with task result
    """
    try:
        db = SessionLocal()
        try:
            # Delete notifications older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)

            old_notifications = db.query(Notification).filter(
                Notification.created_at < cutoff_date
            ).all()

            count = len(old_notifications)

            for notification in old_notifications:
                db.delete(notification)

            db.commit()

            logger.info(f"Cleaned up {count} old notifications")

            return {
                "success": True,
                "notifications_deleted": count,
                "cutoff_date": cutoff_date.isoformat()
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error cleaning up old notifications: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_bulk_notifications(
    self,
    user_ids: List[str],
    title: str,
    message: str,
    notification_type: str = "info"
) -> Dict[str, Any]:
    """
    Send bulk notifications to multiple users

    Args:
        user_ids: List of user IDs
        title: Notification title
        message: Notification message
        notification_type: Type of notification

    Returns:
        Dict with task results
    """
    try:
        results = []
        failed_users = []

        for user_id in user_ids:
            try:
                result = create_notification_task.delay(
                    user_id=user_id,
                    title=title,
                    message=message,
                    notification_type=notification_type
                ).get()

                results.append(result)

            except Exception as e:
                logger.error(
                    f"Failed to send notification to user {user_id}: {e}")
                failed_users.append(user_id)

        return {
            "success": len(failed_users) == 0,
            "total_sent": len(results),
            "total_failed": len(failed_users),
            "failed_users": failed_users,
            "results": results
        }

    except Exception as e:
        logger.error(f"Error sending bulk notifications: {e}")
        raise self.retry(exc=e, countdown=60)
