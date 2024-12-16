# app/schemas/letter_request.py

from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

class LetterStatus(str, Enum):
    drafting = "drafting"
    finalized = "finalized"
    paid = "paid"
    mailed = "mailed"

class UserLetterRequestCreate(BaseModel):
    bill_id: UUID
    politician_id: UUID
    # By default, let's assume the user wants to use their profile return address
    use_profile_return_address: bool = True

class UserLetterRequestUpdate(BaseModel):
    final_letter_text: Optional[str] = None
    status: Optional[LetterStatus] = None
    stripe_charge_id: Optional[str] = None
    use_profile_return_address: Optional[bool] = None

class UserLetterRequestOut(BaseModel):
    bill_id: UUID
    politician_id: UUID
    id: UUID
    final_letter_text: Optional[str]
    status: LetterStatus
    stripe_charge_id: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    use_profile_return_address: bool

    class Config:
        from_attributes = True

class LetterDraftRequest(BaseModel):
    personal_feedback: str
