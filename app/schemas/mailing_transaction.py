# app/schemas/mailing_transaction.py

from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum

class MailingStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"

class MailingTransactionBase(BaseModel):
    user_letter_request_id: UUID

class MailingTransactionCreate(MailingTransactionBase):
    pass

class MailingTransactionUpdate(BaseModel):
    external_mail_service_id: Optional[str] = None
    status: Optional[MailingStatus] = None
    error_message: Optional[str] = None
    mail_service_response: Optional[Dict[str, Any]] = None

class MailingTransactionOut(MailingTransactionBase):
    id: UUID
    external_mail_service_id: Optional[str]
    status: MailingStatus
    error_message: Optional[str]
    mail_service_response: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
