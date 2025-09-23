# app/utils/email.py
from fastapi import BackgroundTasks
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@maplehussle.com")


def send_email(to_email: str, subject: str, body: str, background_tasks: Optional[BackgroundTasks] = None):
    """Send an email (sync or async via FastAPI BackgroundTasks)."""
    def _send():
        msg = MIMEMultipart()
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send email: {e}")

    if background_tasks:
        background_tasks.add_task(_send)
    else:
        _send()


def send_password_reset_email(to_email: str, token: str):
    """Helper for password reset flow."""
    reset_link = f"https://maplehussle.com/reset-password?token={token}"
    subject = "Maple Hussle - Reset Your Password"
    body = f"""
    <p>Hello,</p>
    <p>You requested to reset your password. Click the link below:</p>
    <p><a href="{reset_link}">{reset_link}</a></p>
    <p>If you didn’t request this, you can ignore this email.</p>
    """
    send_email(to_email, subject, body)
