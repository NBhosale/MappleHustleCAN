from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.db import SessionLocal
from app.schemas.messages import (
    MessageCreate, MessageResponse,
    MessageAttachmentResponse,
)
from app.services import messages as message_service
from app.utils.deps import get_current_user

router = APIRouter(prefix="/messages", tags=["Messages"])


# --- Dependency: DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Send a new message ---
@router.post("/", response_model=MessageResponse)
def send_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return message_service.send_message(db, message, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Get messages for a booking (conversation) ---
@router.get("/booking/{booking_id}", response_model=List[MessageResponse])
def get_messages_for_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return message_service.get_messages_for_booking(db, booking_id, current_user.id)


# --- Get direct messages between two users ---
@router.get("/direct/{other_user_id}", response_model=List[MessageResponse])
def get_direct_messages(
    other_user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return message_service.get_direct_messages(db, current_user.id, other_user_id)


# --- Mark a message as read ---
@router.post("/{message_id}/read", response_model=MessageResponse)
def mark_as_read(
    message_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return message_service.mark_as_read(db, message_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- List attachments for a message ---
@router.get("/{message_id}/attachments", response_model=List[MessageAttachmentResponse])
def list_attachments(message_id: uuid.UUID, db: Session = Depends(get_db)):
    return message_service.list_attachments(db, message_id)
