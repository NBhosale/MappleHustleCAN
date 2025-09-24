from datetime import datetime

from sqlalchemy.orm import Session

from app.models.messages import Message, MessageAttachment
from app.repositories import messages as message_repo


def send_message(
        db: Session,
        booking_id,
        sender_id,
        receiver_id,
        content,
        attachments=None):
    msg = Message(
        booking_id=booking_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content,
        created_at=datetime.utcnow(),
    )
    saved_msg = message_repo.create_message(db, msg)

    if attachments:
        for att in attachments:
            attachment = MessageAttachment(
                message_id=saved_msg.id,
                file_path=att.file_path,
                file_type=att.file_type,
            )
            message_repo.add_attachment(db, attachment)

    return saved_msg
