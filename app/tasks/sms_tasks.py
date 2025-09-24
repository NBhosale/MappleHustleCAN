"""
SMS background tasks for MapleHustleCAN
"""
import logging
from typing import Any, Dict, Optional

from twilio.base.exceptions import TwilioException
from twilio.rest import Client

from app.core.celery_app import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_sms_notification(
    self,
    phone_number: str,
    message: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send SMS notification via Twilio

    Args:
        phone_number: Recipient phone number
        message: SMS message content
        user_id: Optional user ID for tracking

    Returns:
        Dict with task result
    """
    try:
        # Initialize Twilio client
        client = Client(settings.TWILIO_ACCOUNT_SID,
                        settings.TWILIO_AUTH_TOKEN)

        # Send SMS
        message_obj = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )

        logger.info(
            f"SMS sent successfully to {phone_number}, SID: {message_obj.sid}")

        return {
            "success": True,
            "message_sid": message_obj.sid,
            "phone_number": phone_number,
            "user_id": user_id
        }

    except TwilioException as e:
        logger.error(f"Twilio error sending SMS to {phone_number}: {e}")
        # Retry on Twilio errors
        raise self.retry(exc=e, countdown=60)

    except Exception as e:
        logger.error(f"Unexpected error sending SMS to {phone_number}: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_sms(
    self,
    phone_number: str,
    verification_code: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Send phone verification SMS

    Args:
        phone_number: Recipient phone number
        verification_code: Verification code
        user_id: User ID

    Returns:
        Dict with task result
    """
    message = f"Your MapleHustleCAN verification code is: {verification_code}. This code expires in 10 minutes."

    return send_sms_notification.delay(
        phone_number=phone_number,
        message=message,
        user_id=user_id
    ).get()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_confirmation_sms(
    self,
    phone_number: str,
    booking_details: Dict[str, Any],
    user_id: str
) -> Dict[str, Any]:
    """
    Send booking confirmation SMS

    Args:
        phone_number: Recipient phone number
        booking_details: Booking information
        user_id: User ID

    Returns:
        Dict with task result
    """
    service_name = booking_details.get("service_name", "Service")
    date = booking_details.get("date", "Unknown date")
    time = booking_details.get("time", "Unknown time")

    message = f"Booking confirmed! {service_name} on {date} at {time}. Thank you for using MapleHustleCAN!"

    return send_sms_notification.delay(
        phone_number=phone_number,
        message=message,
        user_id=user_id
    ).get()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_reminder_sms(
    self,
    phone_number: str,
    booking_details: Dict[str, Any],
    user_id: str
) -> Dict[str, Any]:
    """
    Send booking reminder SMS

    Args:
        phone_number: Recipient phone number
        booking_details: Booking information
        user_id: User ID

    Returns:
        Dict with task result
    """
    service_name = booking_details.get("service_name", "Service")
    date = booking_details.get("date", "Unknown date")
    time = booking_details.get("time", "Unknown time")

    message = f"Reminder: You have a booking for {service_name} tomorrow ({date}) at {time}. Don't forget!"

    return send_sms_notification.delay(
        phone_number=phone_number,
        message=message,
        user_id=user_id
    ).get()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_payment_confirmation_sms(
    self,
    phone_number: str,
    payment_details: Dict[str, Any],
    user_id: str
) -> Dict[str, Any]:
    """
    Send payment confirmation SMS

    Args:
        phone_number: Recipient phone number
        payment_details: Payment information
        user_id: User ID

    Returns:
        Dict with task result
    """
    amount = payment_details.get("amount", "Unknown amount")
    service_name = payment_details.get("service_name", "Service")

    message = f"Payment of ${amount} for {service_name} has been processed successfully. Thank you!"

    return send_sms_notification.delay(
        phone_number=phone_number,
        message=message,
        user_id=user_id
    ).get()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_emergency_notification_sms(
    self,
    phone_number: str,
    emergency_message: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Send emergency notification SMS

    Args:
        phone_number: Recipient phone number
        emergency_message: Emergency message content
        user_id: User ID

    Returns:
        Dict with task result
    """
    message = f"URGENT: {emergency_message}"

    return send_sms_notification.delay(
        phone_number=phone_number,
        message=message,
        user_id=user_id
    ).get()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_bulk_sms_notifications(
    self,
    phone_numbers: list,
    message: str,
    user_ids: Optional[list] = None
) -> Dict[str, Any]:
    """
    Send bulk SMS notifications

    Args:
        phone_numbers: List of phone numbers
        message: SMS message content
        user_ids: Optional list of user IDs

    Returns:
        Dict with task results
    """
    results = []
    failed_numbers = []

    for i, phone_number in enumerate(phone_numbers):
        try:
            user_id = user_ids[i] if user_ids and i < len(user_ids) else None

            result = send_sms_notification.delay(
                phone_number=phone_number,
                message=message,
                user_id=user_id
            ).get()

            results.append(result)

        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {e}")
            failed_numbers.append(phone_number)

    return {
        "success": len(failed_numbers) == 0,
        "total_sent": len(results),
        "total_failed": len(failed_numbers),
        "failed_numbers": failed_numbers,
        "results": results
    }
