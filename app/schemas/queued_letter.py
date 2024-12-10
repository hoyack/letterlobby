from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

class QueuedLetterStatus(str, Enum):
    queued = "queued"
    processed = "processed"

class QueuedLetterBase(BaseModel):
    user_letter_request_id: UUID
    final_letter_text: Optional[str] = None

class QueuedLetterCreate(QueuedLetterBase):
    pass

class QueuedLetterUpdate(BaseModel):
    final_letter_text: Optional[str] = None
    status: Optional[QueuedLetterStatus] = None

class QueuedLetterOut(QueuedLetterBase):
    id: UUID
    status: QueuedLetterStatus
    created_at: datetime

    class Config:
        from_attributes = True
