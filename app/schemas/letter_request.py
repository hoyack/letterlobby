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

class UserLetterRequestBase(BaseModel):
    bill_id: UUID
    politician_id: UUID
    user_provided_name: Optional[str] = None
    user_provided_address_line1: Optional[str] = None
    user_provided_address_line2: Optional[str] = None
    user_provided_city: Optional[str] = None
    user_provided_state: Optional[str] = None
    user_provided_zip: Optional[str] = None
    user_comments: Optional[str] = None

class UserLetterRequestCreate(UserLetterRequestBase):
    pass

class UserLetterRequestUpdate(BaseModel):
    final_letter_text: Optional[str] = None
    status: Optional[LetterStatus] = None
    stripe_charge_id: Optional[str] = None

class UserLetterRequestOut(UserLetterRequestBase):
    id: UUID
    final_letter_text: Optional[str]
    status: LetterStatus
    stripe_charge_id: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
