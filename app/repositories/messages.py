from sqlalchemy.orm import Session
from app.models.messages import Message, MessageAttachment
from uuid import UUID


def create_message(db: Session, message: Message) -> Message:
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def add_attachment(db: Session, attachment: MessageAttachment) -> MessageAttachment:
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def get_message_by_id(db: Session, message_id: UUID) -> Message | None:
    return db.query(Message).filter(Message.id == message_id).first()
