from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db import SessionLocal
from app.models.messages import Message, MessageAttachment
from app.schemas.messages import (
    MessageCreate,
    MessageResponse,
    MessageAttachmentCreate,
    MessageAttachmentResponse,
)
from app.utils.deps import get_current_user

router = APIRouter(prefix="/messages", tags=["Messages"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Send Message ---
@router.post("/", response_model=MessageResponse)
def send_message(
    msg: MessageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if str(current_user.id) != str(msg.sender_id):
        raise HTTPException(status_code=403, detail="You can only send messages from yourself")

    new_message = Message(
        booking_id=msg.booking_id,
        sender_id=msg.sender_id,
        receiver_id=msg.receiver_id,
        content=msg.content,
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    # Add attachments if any
    if msg.attachments:
        for att in msg.attachments:
            new_attachment = MessageAttachment(
                message_id=new_message.id,
                file_path=att.file_path,
                file_type=att.file_type,
            )
            db.add(new_attachment)
        db.commit()
        db.refresh(new_message)

    return new_message


# --- Get Conversation ---
@router.get("/conversation/{user_id}", response_model=list[MessageResponse])
def get_conversation(
    user_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    messages = db.query(Message).filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()

    return messages


# --- Mark as Read ---
@router.put("/{message_id}/read", response_model=MessageResponse)
def mark_as_read(
    message_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    if str(msg.receiver_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only mark your own messages as read")

    msg.is_read = True
    db.commit()
    db.refresh(msg)
    return msg
