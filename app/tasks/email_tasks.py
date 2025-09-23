"""
Email background tasks for MapleHustleCAN
"""
import logging
from typing import List, Dict, Any, Optional
from celery import current_task
from app.core.celery_app import celery_app
from app.core.config import settings
from app.utils.email import send_email

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def send_welcome_email(self, user_email: str, user_name: str, user_role: str):
    """Send welcome email to new user"""
    try:
        subject = f"Welcome to MapleHustleCAN, {user_name}!"
        
        if user_role == "provider":
            template = "welcome_provider.html"
            content = f"""
            <h1>Welcome to MapleHustleCAN!</h1>
            <p>Hi {user_name},</p>
            <p>Welcome to MapleHustleCAN! You've successfully registered as a service provider.</p>
            <p>You can now:</p>
            <ul>
                <li>Create and manage your services</li>
                <li>Set your availability</li>
                <li>Receive booking requests</li>
                <li>Manage your marketplace items</li>
            </ul>
            <p>Get started by creating your first service!</p>
            <p>Best regards,<br>The MapleHustleCAN Team</p>
            """
        else:
            template = "welcome_client.html"
            content = f"""
            <h1>Welcome to MapleHustleCAN!</h1>
            <p>Hi {user_name},</p>
            <p>Welcome to MapleHustleCAN! You've successfully registered as a client.</p>
            <p>You can now:</p>
            <ul>
                <li>Browse and book services</li>
                <li>Shop in our marketplace</li>
                <li>Message service providers</li>
                <li>Manage your bookings and orders</li>
            </ul>
            <p>Start exploring our services today!</p>
            <p>Best regards,<br>The MapleHustleCAN Team</p>
            """
        
        send_email(
            to_email=user_email,
            subject=subject,
            content=content,
            template=template
        )
        
        logger.info(f"Welcome email sent to {user_email}")
        return {"status": "success", "email": user_email}
        
    except Exception as exc:
        logger.error(f"Failed to send welcome email to {user_email}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_booking_confirmation(self, booking_data: Dict[str, Any]):
    """Send booking confirmation email"""
    try:
        user_email = booking_data["user_email"]
        user_name = booking_data["user_name"]
        provider_name = booking_data["provider_name"]
        service_title = booking_data["service_title"]
        booking_date = booking_data["booking_date"]
        total_amount = booking_data["total_amount"]
        
        subject = f"Booking Confirmed: {service_title}"
        
        content = f"""
        <h1>Booking Confirmed!</h1>
        <p>Hi {user_name},</p>
        <p>Your booking has been confirmed!</p>
        <div style="background-color: #f5f5f5; padding: 20px; margin: 20px 0;">
            <h3>Booking Details:</h3>
            <p><strong>Service:</strong> {service_title}</p>
            <p><strong>Provider:</strong> {provider_name}</p>
            <p><strong>Date:</strong> {booking_date}</p>
            <p><strong>Total Amount:</strong> ${total_amount}</p>
        </div>
        <p>You can view and manage your booking in your dashboard.</p>
        <p>Best regards,<br>The MapleHustleCAN Team</p>
        """
        
        send_email(
            to_email=user_email,
            subject=subject,
            content=content,
            template="booking_confirmation.html"
        )
        
        logger.info(f"Booking confirmation email sent to {user_email}")
        return {"status": "success", "email": user_email}
        
    except Exception as exc:
        logger.error(f"Failed to send booking confirmation email: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_order_confirmation(self, order_data: Dict[str, Any]):
    """Send order confirmation email"""
    try:
        user_email = order_data["user_email"]
        user_name = order_data["user_name"]
        order_id = order_data["order_id"]
        items = order_data["items"]
        total_amount = order_data["total_amount"]
        shipping_address = order_data["shipping_address"]
        
        subject = f"Order Confirmed - #{order_id}"
        
        items_html = ""
        for item in items:
            items_html += f"""
            <tr>
                <td>{item['name']}</td>
                <td>{item['quantity']}</td>
                <td>${item['price']}</td>
                <td>${item['total']}</td>
            </tr>
            """
        
        content = f"""
        <h1>Order Confirmed!</h1>
        <p>Hi {user_name},</p>
        <p>Your order has been confirmed and is being processed.</p>
        <div style="background-color: #f5f5f5; padding: 20px; margin: 20px 0;">
            <h3>Order Details:</h3>
            <p><strong>Order ID:</strong> #{order_id}</p>
            <p><strong>Total Amount:</strong> ${total_amount}</p>
            <h4>Items:</h4>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #e0e0e0;">
                    <th style="padding: 10px; text-align: left;">Item</th>
                    <th style="padding: 10px; text-align: left;">Quantity</th>
                    <th style="padding: 10px; text-align: left;">Price</th>
                    <th style="padding: 10px; text-align: left;">Total</th>
                </tr>
                {items_html}
            </table>
            <h4>Shipping Address:</h4>
            <p>{shipping_address['street']}<br>
            {shipping_address['city']}, {shipping_address['province']} {shipping_address['postal_code']}</p>
        </div>
        <p>You can track your order in your dashboard.</p>
        <p>Best regards,<br>The MapleHustleCAN Team</p>
        """
        
        send_email(
            to_email=user_email,
            subject=subject,
            content=content,
            template="order_confirmation.html"
        )
        
        logger.info(f"Order confirmation email sent to {user_email}")
        return {"status": "success", "email": user_email}
        
    except Exception as exc:
        logger.error(f"Failed to send order confirmation email: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_password_reset_email(self, user_email: str, reset_token: str, user_name: str):
    """Send password reset email"""
    try:
        subject = "Reset Your MapleHustleCAN Password"
        reset_url = f"{settings.ALLOWED_ORIGINS[0]}/reset-password?token={reset_token}"
        
        content = f"""
        <h1>Password Reset Request</h1>
        <p>Hi {user_name},</p>
        <p>You requested to reset your password for your MapleHustleCAN account.</p>
        <p>Click the link below to reset your password:</p>
        <p><a href="{reset_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
        <p>This link will expire in 1 hour for security reasons.</p>
        <p>If you didn't request this password reset, please ignore this email.</p>
        <p>Best regards,<br>The MapleHustleCAN Team</p>
        """
        
        send_email(
            to_email=user_email,
            subject=subject,
            content=content,
            template="password_reset.html"
        )
        
        logger.info(f"Password reset email sent to {user_email}")
        return {"status": "success", "email": user_email}
        
    except Exception as exc:
        logger.error(f"Failed to send password reset email to {user_email}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_bulk_emails(self, email_list: List[Dict[str, Any]], subject: str, content: str, template: str = None):
    """Send bulk emails"""
    try:
        results = []
        
        for email_data in email_list:
            try:
                send_email(
                    to_email=email_data["email"],
                    subject=subject,
                    content=content.format(**email_data),
                    template=template
                )
                results.append({"email": email_data["email"], "status": "success"})
                
            except Exception as e:
                logger.error(f"Failed to send email to {email_data['email']}: {e}")
                results.append({"email": email_data["email"], "status": "failed", "error": str(e)})
        
        success_count = len([r for r in results if r["status"] == "success"])
        logger.info(f"Bulk email sent: {success_count}/{len(email_list)} successful")
        
        return {
            "status": "completed",
            "total": len(email_list),
            "successful": success_count,
            "failed": len(email_list) - success_count,
            "results": results
        }
        
    except Exception as exc:
        logger.error(f"Failed to send bulk emails: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_notification_email(self, user_email: str, notification_type: str, data: Dict[str, Any]):
    """Send notification email"""
    try:
        subject = f"MapleHustleCAN Notification: {notification_type.replace('_', ' ').title()}"
        
        if notification_type == "booking_reminder":
            content = f"""
            <h1>Booking Reminder</h1>
            <p>Hi {data.get('user_name', 'there')},</p>
            <p>This is a reminder about your upcoming booking:</p>
            <div style="background-color: #f5f5f5; padding: 20px; margin: 20px 0;">
                <p><strong>Service:</strong> {data.get('service_title', 'N/A')}</p>
                <p><strong>Date:</strong> {data.get('booking_date', 'N/A')}</p>
                <p><strong>Time:</strong> {data.get('booking_time', 'N/A')}</p>
            </div>
            <p>We look forward to seeing you!</p>
            """
        elif notification_type == "payment_received":
            content = f"""
            <h1>Payment Received</h1>
            <p>Hi {data.get('user_name', 'there')},</p>
            <p>We've received your payment of ${data.get('amount', 'N/A')}.</p>
            <p>Thank you for your business!</p>
            """
        else:
            content = f"""
            <h1>Notification</h1>
            <p>Hi {data.get('user_name', 'there')},</p>
            <p>{data.get('message', 'You have a new notification.')}</p>
            """
        
        send_email(
            to_email=user_email,
            subject=subject,
            content=content,
            template="notification.html"
        )
        
        logger.info(f"Notification email sent to {user_email}")
        return {"status": "success", "email": user_email, "type": notification_type}
        
    except Exception as exc:
        logger.error(f"Failed to send notification email to {user_email}: {exc}")
        raise self.retry(exc=exc, countdown=60)
