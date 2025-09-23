from twilio.rest import Client
import os

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)


def send_sms(to: str, body: str):
    """
    Send SMS via Twilio.
    :param to: Recipient phone number (+1...)
    :param body: Message body
    """
    if not TWILIO_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        raise RuntimeError("❌ Twilio credentials not configured")

    message = client.messages.create(
        body=body,
        from_=TWILIO_PHONE_NUMBER,
        to=to
    )
    return message.sid

# // Use inside routers (e.g., booking confirmation):
# //from app.utils.sms import send_sms
# // send_sms("+15555555555", "Your booking is confirmed ✅")
