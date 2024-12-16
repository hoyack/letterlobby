# app/schemas/queued_letter.py

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

class QueuedLetterCreate(QueuedLetterBase):
    pass

class QueuedLetterUpdate(BaseModel):
    status: Optional[QueuedLetterStatus] = None

class QueuedLetterOut(QueuedLetterBase):
    id: UUID
    status: QueuedLetterStatus
    created_at: datetime

    # Include these two fields to show associated bill and politician data
    bill_id: UUID
    politician_id: UUID

    class Config:
        from_attributes = True
