import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# --- Attachments ---
class MessageAttachmentBase(BaseModel):
    file_path: str   # e.g., /uploads/messages/{uuid}.jpg
    file_type: str   # e.g., image/jpeg, application/pdf


class MessageAttachmentCreate(MessageAttachmentBase):
    pass


class MessageAttachmentResponse(MessageAttachmentBase):
    id: uuid.UUID
    message_id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True


# --- Messages ---
class MessageBase(BaseModel):
    content: str
    is_read: bool = False


class MessageCreate(MessageBase):
    booking_id: Optional[uuid.UUID]
    sender_id: uuid.UUID
    receiver_id: uuid.UUID
    attachments: Optional[List[MessageAttachmentCreate]] = None


class MessageResponse(MessageBase):
    id: uuid.UUID
    booking_id: Optional[uuid.UUID]
    sender_id: uuid.UUID
    receiver_id: uuid.UUID
    encrypted_content: Optional[bytes] = None
    created_at: datetime
    attachments: List[MessageAttachmentResponse] = []

    class Config:
        orm_mode = True
